#!/bin/sh
set -eu
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$REPO"
export HD_TEST_CLIENT_COMMAND=$(python3 - <<'PY'
import json
from pathlib import Path
r=Path.cwd()
print(json.dumps(['qemu-arm','-cpu','cortex-a7','-L',str(r/'.local-cross/hd-runtime'),str(r/'artifacts/armv7-glibc225/hd-handshake')]))
PY
)
.venv-handshake/bin/python -m unittest discover -s host -p 'test_*.py' -v
