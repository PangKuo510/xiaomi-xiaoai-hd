"""Extract only fixed runtime libraries from a private HD rootfs TAR into ignored local cache."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile

NAMES = {'ld-2.25.so', 'ld-linux-armhf.so.3', 'libc-2.25.so', 'libc.so.6',
         'libpthread-2.25.so', 'libpthread.so.0', 'libdl-2.25.so', 'libdl.so.2',
         'librt-2.25.so', 'librt.so.1', 'libm-2.25.so', 'libm.so.6', 'libgcc_s.so.1'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rootfs-tar', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / '.local-cross/hd-runtime'
    lib = root / 'lib'
    lib.mkdir(parents=True, exist_ok=True)
    found = []
    with tarfile.open(args.rootfs_tar, 'r:gz') as archive:
        for member in archive:
            name = PurePosixPath(member.name.removeprefix('./'))
            if str(name.parent) != 'lib' or name.name not in NAMES:
                continue
            dest = lib / name.name
            if dest.exists() or dest.is_symlink():
                raise SystemExit('Runtime destination exists; use a fresh local cache')
            if member.isfile():
                with archive.extractfile(member) as source, dest.open('wb') as target:
                    shutil.copyfileobj(source, target)
                dest.chmod(0o755)
                found.append({'library': name.name, 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()})
            elif member.issym() and '/' not in member.linkname and member.linkname in NAMES:
                dest.symlink_to(member.linkname)
                found.append({'library': name.name, 'symlink': member.linkname})
            else:
                raise SystemExit('Unexpected runtime entry type')
    required = {'ld-linux-armhf.so.3','libc.so.6','libpthread.so.0','libdl.so.2','librt.so.1','libm.so.6','libgcc_s.so.1'}
    if not all((lib/name).is_file() for name in required):
        raise SystemExit('Required runtime libraries missing')
    (root/'local-library-manifest.json').write_text(json.dumps(found,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'runtime_libraries_prepared':len(found),'credentials_or_configuration_extracted':False}))


if __name__ == '__main__':
    main()
