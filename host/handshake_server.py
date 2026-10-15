"""Loopback-only HD handshake server. Sends exactly three read-only RPC requests."""
import argparse
import asyncio
import json
from websockets.asyncio.server import serve

COMMANDS = ('get_version', 'get_model', 'get_status')


async def handshake(ws, timeout=5):
    results = {}
    for index, command in enumerate(COMMANDS):
        request_id = f'hd-{index}'
        await ws.send(json.dumps({'Request': {'id': request_id, 'command': command, 'payload': None}}))
        raw = await asyncio.wait_for(ws.recv(), timeout)
        if not isinstance(raw, str):
            raise ValueError('unexpected binary frame')
        response = json.loads(raw)
        if not isinstance(response, dict) or set(response) != {'Response'}:
            raise ValueError('unexpected response envelope')
        body = response['Response']
        if not isinstance(body, dict) or body.get('id') != request_id or body.get('code') != 0:
            raise ValueError('handshake query rejected or mismatched')
        data = body.get('data')
        if not isinstance(data, dict):
            raise ValueError('invalid data schema')
        if command == 'get_version':
            if set(data) - {'client', 'version', 'protocol', 'firmware', 'simulated'}:
                raise ValueError('unexpected version fields')
            if data.get('client') != 'hd-handshake' or type(data.get('protocol')) is not int or data['protocol'] != 1:
                raise ValueError('unsupported client protocol')
        if command == 'get_model' and data != {'model': 'XMYX01JY', 'hardware': 'M01'}:
            raise ValueError('unsupported model')
        if command == 'get_status' and (data.get('read_only') is not True or data.get('commands') != list(COMMANDS)):
            raise ValueError('unexpected capabilities')
        if command == 'get_status':
            if set(data) - {'read_only', 'simulated', 'memory', 'uptime_seconds', 'commands', 'player', 'player_error'}:
                raise ValueError('unexpected status fields')
            if not isinstance(data.get('memory'), dict) or set(data['memory']) - {'total_kib', 'available_kib'}:
                raise ValueError('unexpected memory fields')
            if 'player' in data and (not isinstance(data['player'], dict) or set(data['player']) - {'status', 'volume', 'loop_type'}):
                raise ValueError('unexpected player fields')
            if data.get('simulated') is not results['get_version'].get('simulated'):
                raise ValueError('inconsistent simulation state')
        results[command] = data
    return results


async def run(port):
    completed = asyncio.get_running_loop().create_future()
    claimed = False

    async def handler(ws):
        nonlocal claimed
        if claimed:
            await ws.close(code=1008, reason='one session only')
            return
        claimed = True
        try:
            # Don't print untrusted/raw device data or transport identifiers.
            result = await handshake(ws)
            print(json.dumps({'handshake': 'ok', 'queries': list(result),
                              'simulated': result['get_version'].get('simulated') is True}))
            if not completed.done():
                completed.set_result(None)
        except Exception:
            if not completed.done():
                completed.set_exception(RuntimeError('handshake failed'))

    async with serve(handler, '127.0.0.1', port, origins=[None], compression=None,
                     max_size=8192, max_queue=4, open_timeout=5, close_timeout=2):
        print('Ready: loopback-only, one session, three read-only queries', flush=True)
        await asyncio.wait_for(completed, 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=4399)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('port out of range')
    asyncio.run(run(args.port))
