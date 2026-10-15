"""Local protocol tests; only launches the Rust client with --mock on loopback."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import unittest
from websockets.asyncio.server import serve
from websockets.asyncio.client import connect
from handshake_server import handshake

ROOT = Path(__file__).resolve().parents[1]
WSL_ROOT = '/mnt/d/' + ROOT.as_posix().split(':', 1)[1].lstrip('/') if os.name == 'nt' else str(ROOT)


def binary_args(*extra):
    path = WSL_ROOT + '/packages/hd-handshake/target/debug/hd-handshake'
    return (['wsl.exe', '-e', path] if os.name == 'nt' else [path]) + list(extra)


class HandshakeTests(unittest.IsolatedAsyncioTestCase):
    async def run_client(self, handler):
        done = asyncio.get_running_loop().create_future()

        async def wrapped(ws):
            try:
                result = await handler(ws)
                done.set_result(result)
            except BaseException as error:
                if not done.done():
                    done.set_exception(error)

        async with serve(wrapped, '127.0.0.1', 0, origins=[None], compression=None, max_size=8192) as server:
            port = server.sockets[0].getsockname()[1]
            child = subprocess.Popen(binary_args('--mock', '--server', f'ws://127.0.0.1:{port}'),
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                result = await asyncio.wait_for(done, 15)
                code = await asyncio.wait_for(asyncio.to_thread(child.wait), 5)
                self.assertEqual(code, 0)
                return result
            finally:
                if child.poll() is None:
                    child.kill()
                    await asyncio.to_thread(child.wait)
                child.communicate()

    async def test_three_query_roundtrip_and_no_unsolicited_messages(self):
        async def handler(ws):
            with self.assertRaises(asyncio.TimeoutError):
                await asyncio.wait_for(ws.recv(), .15)
            result = await handshake(ws)
            self.assertEqual(result['get_model'], {'model': 'XMYX01JY', 'hardware': 'M01'})
            self.assertIs(result['get_status']['read_only'], True)
            self.assertIs(result['get_version']['simulated'], True)
            with self.assertRaises(asyncio.TimeoutError):
                await asyncio.wait_for(ws.recv(), .15)
            await ws.close()
        await self.run_client(handler)

    async def test_mutating_commands_and_payloads_rejected_over_websocket(self):
        async def handler(ws):
            for command in ['run_shell', 'start_play', 'start_recording', 'set_boot', 'mic_on']:
                await ws.send(json.dumps({'Request': {'id': 'negative', 'command': command, 'payload': None}}))
                value = json.loads(await ws.recv())['Response']
                self.assertEqual(value['code'], -1)
                self.assertEqual(value['msg'], 'command_not_allowed')
            await ws.send(json.dumps({'Request': {'id': 'payload', 'command': 'get_status', 'payload': {'url': 'ignored'}}}))
            self.assertEqual(json.loads(await ws.recv())['Response']['msg'], 'payload_not_allowed')
            await ws.send('not json')
            self.assertEqual(json.loads(await ws.recv())['Response']['msg'], 'invalid_request')
            # A rejected request must not break subsequent read-only queries.
            await handshake(ws)
            await ws.close()
        await self.run_client(handler)

    async def fake_client_test(self, transform, expected_error=ValueError):
        result = asyncio.get_running_loop().create_future()

        async def handler(ws):
            try:
                await handshake(ws, timeout=.1)
                result.set_result(False)
            except expected_error:
                result.set_result(True)

        async with serve(handler, '127.0.0.1', 0, max_size=8192) as server:
            port = server.sockets[0].getsockname()[1]
            async with connect(f'ws://127.0.0.1:{port}') as ws:
                request = json.loads(await ws.recv())['Request']
                reply = transform(request)
                if reply is not None:
                    await ws.send(json.dumps(reply))
                self.assertTrue(await asyncio.wait_for(result, 2))

    async def test_response_id_mismatch_rejected(self):
        await self.fake_client_test(lambda r: {'Response': {'id': 'wrong', 'code': 0, 'data': {}}})

    async def test_unsupported_client_rejected(self):
        await self.fake_client_test(lambda r: {'Response': {'id': r['id'], 'code': 0, 'data': {'client': 'other', 'protocol': 1}}})

    async def test_server_timeout_is_bounded(self):
        await self.fake_client_test(lambda r: None, asyncio.TimeoutError)

    async def test_client_refuses_lan_endpoint_before_connection(self):
        result = await asyncio.to_thread(subprocess.run,
            binary_args('--mock', '--server', 'ws://example.invalid:4399'),
            capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)

    async def test_full_server_cli_with_mock_client(self):
        import socket
        import sys
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        server = subprocess.Popen([sys.executable, str(ROOT/'host/handshake_server.py'), '--port', str(port)],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        client = None
        try:
            ready = await asyncio.wait_for(asyncio.to_thread(server.stdout.readline), 5)
            self.assertIn(b'Ready:', ready)
            client = subprocess.Popen(binary_args('--mock', '--server', f'ws://127.0.0.1:{port}'),
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = await asyncio.wait_for(asyncio.to_thread(server.communicate), 10)
            self.assertEqual(server.returncode, 0, stderr.decode())
            summary = json.loads(stdout.decode())
            self.assertEqual(summary['handshake'], 'ok')
            self.assertIs(summary['simulated'], True)
            self.assertNotIn('volume', summary)
            self.assertEqual(await asyncio.wait_for(asyncio.to_thread(client.wait), 5), 0)
        finally:
            for process in (client, server):
                if process:
                    if process.poll() is None:
                        process.kill()
                        await asyncio.to_thread(process.wait)
                    process.communicate()


if __name__ == '__main__':
    unittest.main()
