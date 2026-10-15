#!/bin/sh
set -eu
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
CACHE=${HD_CROSS_HOME:-"${XDG_CACHE_HOME:-$HOME/.cache}/xiaomi-xiaoai-hd-cross"}
exec "$CACHE/zig/zig" cc -target arm-linux-gnueabihf.2.25 "$@"
