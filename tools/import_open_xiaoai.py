"""Import pinned, tracked upstream blobs only; never run upstream code."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

COMMIT = 'bc3396c64e2a435f354eb5cb12a203981f1fe422'
PREFIXES = ('packages/client-rust/', 'examples/migpt/', 'examples/xiaozhi/', 'examples/gemini/')
ROOT_FILES = {'LICENSE', 'agreement.md', 'README.md'}
ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Existing upstream Git checkout')
    args = parser.parse_args()

    def git(*parts):
        return subprocess.check_output(['git', '-C', str(args.source), *parts])

    resolved = git('rev-parse', COMMIT + '^{commit}').decode().strip()
    if resolved != COMMIT:
        raise SystemExit('Unexpected upstream commit')
    target = ROOT / 'vendor/open-xiaoai'
    rows = []
    for entry in git('ls-tree', '-r', '-z', COMMIT).split(b'\0'):
        if not entry:
            continue
        meta, raw_path = entry.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        name = raw_path.decode('utf-8')
        if name not in ROOT_FILES and not name.startswith(PREFIXES):
            continue
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise SystemExit('Unsupported upstream entry: ' + name)
        path = target / name
        if not path.resolve().is_relative_to(target.resolve()):
            raise SystemExit('Invalid upstream path')
        data = git('cat-file', 'blob', oid)
        if path.exists() and path.read_bytes() != data:
            raise SystemExit('Refusing to overwrite changed file: ' + name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        rows.append({'path': name, 'git_mode': mode, 'git_blob_sha1': oid,
                     'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    manifest = {
        'repository': 'https://github.com/idootop/open-xiaoai', 'commit': COMMIT,
        'snapshot_date': '2026-10-15', 'vendor_root': 'vendor/open-xiaoai',
        'selection': list(PREFIXES) + sorted(ROOT_FILES),
        'policy': 'Exact upstream Git blobs; local untracked or modified files are not imported.',
        'status': 'Reference source only; not HD-adapted, built, installed, or executed.',
        'files': rows,
    }
    (ROOT / 'docs/upstream-import-manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'files': len(rows), 'bytes': sum(r['bytes'] for r in rows), 'commit': COMMIT}))


if __name__ == '__main__':
    main()
