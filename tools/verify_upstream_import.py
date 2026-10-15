"""Verify vendored bytes, source blob IDs, tracked file set, modes, and local Cargo paths."""
import hashlib
import json
from pathlib import Path
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / 'docs/upstream-import-manifest.json').read_text(encoding='utf-8'))
    vendor = ROOT / manifest['vendor_root']
    errors = []
    expected = {r['path'] for r in manifest['files']}
    actual = {p.relative_to(vendor).as_posix() for p in vendor.rglob('*') if p.is_file()}
    if actual != expected:
        errors.append({'file_set_difference': sorted(actual ^ expected)})
    cargo_paths = 0
    for row in manifest['files']:
        path = vendor / row['path']
        if not path.is_file():
            errors.append({'missing': row['path']})
            continue
        data = path.read_bytes()
        blob_id = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256'] or blob_id != row['git_blob_sha1']:
            errors.append({'content_mismatch': row['path']})
        if path.name == 'Cargo.toml':
            config = tomllib.loads(data.decode('utf-8'))
            for dep in config.get('dependencies', {}).values():
                if isinstance(dep, dict) and 'path' in dep:
                    cargo_paths += 1
                    resolved = (path.parent / dep['path']).resolve()
                    if not resolved.is_relative_to(vendor.resolve()) or not (resolved / 'Cargo.toml').is_file():
                        errors.append({'broken_cargo_path': row['path'], 'dependency': dep['path']})
    tracked = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '--stage', '-z', '--', manifest['vendor_root']])
    index = {}
    for entry in tracked.split(b'\0'):
        if entry:
            meta, name = entry.split(b'\t', 1)
            mode, oid, stage = meta.decode().split()
            index[name.decode()] = (mode, oid, stage)
    for row in manifest['files']:
        name = manifest['vendor_root'] + '/' + row['path']
        if index.get(name) != (row['git_mode'], row['git_blob_sha1'], '0'):
            errors.append({'git_index_mismatch': name})
    if set(index) != {manifest['vendor_root'] + '/' + name for name in expected}:
        errors.append({'tracked_vendor_set_mismatch': True})
    result = {'files_verified': len(expected), 'local_cargo_paths_verified': cargo_paths,
              'errors': errors, 'build_performed': False, 'device_accessed': False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
