"""Package the locally validated binary and dependency notices; never package HD firmware libraries."""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path(os.environ.get('HD_CROSS_HOME', Path(os.environ.get('XDG_CACHE_HOME',Path.home()/'.cache'))/'xiaomi-xiaoai-hd-cross'))


def main():
    report = json.loads((ROOT/'docs/arm-build-inspection.json').read_text())
    binary = (ROOT/'artifacts/armv7-glibc225/hd-handshake').read_bytes()
    if report['errors'] or hashlib.sha256(binary).hexdigest()!=report['sha256']:
        raise SystemExit('Binary not validated or changed')
    files = {'hd-handshake':binary, 'inspection.json':json.dumps(report,indent=2).encode()+b'\n'}
    records = []
    metadata = json.loads((ROOT/'.local-cross/cargo-metadata.json').read_text())
    for package in metadata['packages']:
        if package['name']=='hd-handshake':
            continue
        records.append({k:package.get(k) for k in ('name','version','license','repository')})
        source = Path(package['manifest_path']).parent
        for path in source.rglob('*'):
            if path.is_file() and path.name.lower().startswith(('license','copying','notice','copyright')):
                relative = path.relative_to(source).as_posix()
                files[f"licenses/{package['name']}-{package['version']}/{relative}"] = path.read_bytes()
    rust = CACHE/'downloads/rustc-1.93.1-x86_64-unknown-linux-gnu'
    for name in ('LICENSE-MIT','LICENSE-APACHE','COPYRIGHT'):
        files['licenses/rust-1.93.1/'+name] = (rust/name).read_bytes()
    files['licenses/zig-0.13.0/LICENSE'] = (CACHE/'zig/LICENSE').read_bytes()
    for path in (CACHE/'zig/lib/libc/glibc/LICENSES').rglob('*'):
        if path.is_file():
            files['licenses/zig-glibc/'+path.relative_to(CACHE/'zig/lib/libc/glibc/LICENSES').as_posix()] = path.read_bytes()
    files['dependencies.json'] = json.dumps(records,indent=2).encode()+b'\n'
    files['README.txt'] = (
        'HD handshake 0.1.0 - local validation artifact, NOT installed or hardware-tested.\n'
        'ARMv7 hard-float, dynamic glibc <= 2.25. Loopback only; mock mode tested under QEMU.\n'
        'No firmware, private device libraries, credentials, or installer included.\n'
        'Run only in a controlled test environment. This is not a general Open-XiaoAI client.\n'
        'Build source and notices: https://github.com/PangKuo510/xiaomi-xiaoai-hd\n'
        'This artifact does not introduce a new public license for project-owned code.\n'
        'Third-party rights remain with their respective authors; see bundled notices.\n'
    ).encode()
    dest = ROOT/'dist/hd-handshake-armv7-glibc225.tar.gz'
    dest.parent.mkdir(exist_ok=True)
    with dest.open('wb') as raw, gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as gz:
        with tarfile.open(fileobj=gz,mode='w') as archive:
            for name,data in sorted(files.items()):
                info = tarfile.TarInfo(name)
                info.size=len(data)
                info.mode=0o755 if name=='hd-handshake' else 0o644
                archive.addfile(info,io.BytesIO(data))
    manifest={'artifact':dest.name,'bytes':dest.stat().st_size,
              'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
              'client_sha256':report['sha256'],'archive_entries':len(files),
              'cargo_packages_listed':len(records),'includes_hd_runtime_libraries':False}
    (ROOT/'dist/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))
    downloads = []
    for path in sorted((CACHE/'downloads').glob('rust*.tar.xz')):
        downloads.append({'url':'https://static.rust-lang.org/dist/'+path.name,
                          'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    zig = json.loads((CACHE/'downloads/zig-index.json').read_text())['0.13.0']['x86_64-linux']
    downloads.append({'url':zig['tarball'],'sha256':zig['shasum']})
    (ROOT/'docs/arm-toolchain-lock.json').write_text(json.dumps(
        {'rust':'1.93.1','zig':'0.13.0','downloads':downloads},indent=2)+'\n')


if __name__=='__main__':
    main()
