"""Validate ARM hard-float ELF against local HD runtime without running device code."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def readelf(option, path):
    return subprocess.check_output(['readelf', option, '--wide', str(path)], text=True, env={**os.environ,'LC_ALL':'C'})


def needed(path):
    return re.findall(r'\(NEEDED\).*\[(.*?)\]', readelf('-d', path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = args.binary.read_bytes()
    header = readelf('-h', args.binary)
    attributes = readelf('-A', args.binary)
    interp = re.search(r'Requesting program interpreter: (.*?)\]', readelf('-l',args.binary))
    versions = sorted(set(re.findall(r'\bGLIBC_([0-9]+(?:\.[0-9]+)+)\b', readelf('-V',args.binary))),
                      key=lambda s: tuple(map(int,s.split('.'))))
    errors = []
    checks = {'elf32':'Class:                             ELF32' in header,
              'arm':bool(re.search(r'Machine:\s+ARM\b',header)),
              'little_endian':'little endian' in header,
              'eabi5':'Version5 EABI' in header,
              'pie':bool(re.search(r'Type:\s+DYN',header)) and 'PIE' in readelf('-d',args.binary),
              'stripped':'.symtab' not in readelf('-S',args.binary),
              # EF_ARM_ABI_FLOAT_HARD is authoritative; Zig CRT may omit the optional VFP-args attribute.
              'hard_float':'hard-float ABI' in header,
              'interpreter':interp is not None and interp[1]=='/lib/ld-linux-armhf.so.3',
              'glibc_at_most_2_25':bool(versions) and all(tuple(map(int,v.split('.'))) <= (2,25) for v in versions),
              'no_rpath':not re.search(r'\((?:RPATH|RUNPATH)\)',readelf('-d',args.binary)),
              'no_private_build_paths':str(Path.home()).encode() not in data and str(Path(__file__).resolve().parents[1]).encode() not in data}
    errors.extend(name for name,passed in checks.items() if not passed)
    queue = list(needed(args.binary))
    libraries = {}
    while queue:
        name = queue.pop(0)
        if name in libraries:
            continue
        if '/' in name or not (args.runtime/'lib'/name).is_file():
            errors.append('missing_library:'+name)
            continue
        path = args.runtime/'lib'/name
        libraries[name] = path
        queue.extend(n for n in needed(path) if n not in libraries)
    provided = set()
    for path in libraries.values():
        for line in readelf('--dyn-syms',path).splitlines():
            fields = line.split()
            if len(fields) >= 8 and fields[6] != 'UND':
                symbol = fields[7].replace('@@','@')
                provided.add(symbol)
                provided.add(symbol.split('@')[0])
    missing_symbols = []
    for line in readelf('--dyn-syms',args.binary).splitlines():
        fields = line.split()
        if len(fields)>=8 and fields[6]=='UND' and fields[4]!='WEAK':
            symbol = fields[7]
            if symbol not in provided:
                missing_symbols.append(symbol)
    if missing_symbols:
        errors.append('missing_required_dynamic_symbols')
    report = {'date':'2026-10-15','target':'armv7-unknown-linux-gnueabihf',
        'requested_glibc_baseline':'2.25','elf_class':'ELF32','machine':'ARM',
        'endianness':'little','abi':'EABI5 hard-float','arm_attributes':attributes.strip(),
        'interpreter':interp[1] if interp else None,
        'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'direct_dependencies':needed(args.binary),
        'resolved_runtime_libraries':sorted(libraries),'glibc_versions_required':versions,
        'max_glibc_required':versions[-1] if versions else None,'missing_dynamic_symbols':missing_symbols,
        'checks':checks,'errors':errors,'device_accessed':False,
        'limitations':'ELF/symbol checks only; HD hardware, kernel and real backend execution remain untested.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    raise SystemExit(bool(errors))


if __name__=='__main__':
    main()
