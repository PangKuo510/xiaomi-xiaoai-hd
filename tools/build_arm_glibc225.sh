#!/bin/sh
set -eu
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
CACHE=${HD_CROSS_HOME:-"${XDG_CACHE_HOME:-$HOME/.cache}/xiaomi-xiaoai-hd-cross"}
export RUSTC="$CACHE/rust/bin/rustc"
export CARGO_TARGET_ARMV7_UNKNOWN_LINUX_GNUEABIHF_LINKER="$REPO/tools/arm_glibc225_linker.sh"
export CARGO_ENCODED_RUSTFLAGS=$(printf '%s\037%s\037%s\037%s' '-C' 'link-arg=-Wl,--build-id=sha1' "--remap-path-prefix=$REPO=/src/xiaomi-xiaoai-hd" "--remap-path-prefix=$HOME=/builder")
export ZIG_GLOBAL_CACHE_DIR="$CACHE/zig-cache"
cd "$REPO"
cargo build --locked --release --target armv7-unknown-linux-gnueabihf --manifest-path packages/hd-handshake/Cargo.toml
mkdir -p artifacts/armv7-glibc225
cp packages/hd-handshake/target/armv7-unknown-linux-gnueabihf/release/hd-handshake artifacts/armv7-glibc225/hd-handshake
sha256sum artifacts/armv7-glibc225/hd-handshake
