#!/bin/sh
# Local tools only; downloads verified official Rust and Zig distributions.
set -eu
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
CACHE=${HD_CROSS_HOME:-"${XDG_CACHE_HOME:-$HOME/.cache}/xiaomi-xiaoai-hd-cross"}
mkdir -p "$CACHE/downloads" "$CACHE/rust" "$CACHE/zig"
fetch_rust() {
    package=$1
    filename="$package.tar.xz"
    url="https://static.rust-lang.org/dist/$filename"
    if [ ! -f "$CACHE/downloads/$filename" ]; then
        curl --fail --location --retry 2 -o "$CACHE/downloads/$filename" "$url"
    fi
    curl --fail --location --retry 2 -o "$CACHE/downloads/$filename.sha256" "$url.sha256"
    expected=$(cut -d ' ' -f 1 "$CACHE/downloads/$filename.sha256")
    actual=$(sha256sum "$CACHE/downloads/$filename" | cut -d ' ' -f 1)
    [ "$expected" = "$actual" ] || { echo 'Rust archive checksum mismatch' >&2; exit 1; }
    python3 - "$REPO/docs/arm-toolchain-lock.json" "$url" "$actual" <<'PY'
import json, sys
records = json.load(open(sys.argv[1]))['downloads']
if not any(r['url']==sys.argv[2] and r['sha256']==sys.argv[3] for r in records):
    raise SystemExit('Rust archive differs from committed toolchain lock')
PY
    tar -xJf "$CACHE/downloads/$filename" -C "$CACHE/downloads"
    "$CACHE/downloads/$package/install.sh" --prefix="$CACHE/rust" --disable-ldconfig
}
if [ ! -f "$CACHE/rust/.hd-1.93.1-ready" ]; then
    fetch_rust rustc-1.93.1-x86_64-unknown-linux-gnu
    fetch_rust rust-std-1.93.1-x86_64-unknown-linux-gnu
    fetch_rust rust-std-1.93.1-armv7-unknown-linux-gnueabihf
    touch "$CACHE/rust/.hd-1.93.1-ready"
fi
if [ ! -x "$CACHE/zig/zig" ]; then
    curl --fail --location --retry 2 -o "$CACHE/downloads/zig-index.json" https://ziglang.org/download/index.json
    python3 - "$CACHE" "$REPO/docs/arm-toolchain-lock.json" <<'PY'
import hashlib, json, pathlib, subprocess, sys
root = pathlib.Path(sys.argv[1])
record = json.loads((root/'downloads/zig-index.json').read_text())['0.13.0']['x86_64-linux']
locked = json.load(open(sys.argv[2]))['downloads']
if not any(r['url']==record['tarball'] and r['sha256']==record['shasum'] for r in locked):
    raise SystemExit('Zig download differs from committed toolchain lock')
archive = root/'downloads/zig-linux-x86_64-0.13.0.tar.xz'
subprocess.run(['curl','--fail','--location','--retry','2','-o',str(archive),record['tarball']],check=True)
if hashlib.sha256(archive.read_bytes()).hexdigest() != record['shasum']:
    raise SystemExit('Zig archive checksum mismatch')
subprocess.run(['tar','-xJf',str(archive),'-C',str(root/'zig'),'--strip-components=1'],check=True)
PY
fi
echo 'Official Rust 1.93.1 (host + ARMv7 std) and Zig 0.13.0 ready in local cache.'
