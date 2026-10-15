"""Bounded pattern audit of tracked files and reachable Git history. Never prints matches."""
import argparse
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'github_token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
    'aws_access_key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'api_key': re.compile(r'\bsk-[A-Za-z0-9_-]{16,}\b'),
    'ipv4': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    'mac': re.compile(r'\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b'),
    'serial_literal': re.compile(r'(?i)\b(?:serial|device_sn|serial_number)[\x22\x27]?\s*[=:]\s*[\x22\x27]?[a-z0-9]{12,}'),
    'password_hash': re.compile(r'\$(?:1|5|6)\$[A-Za-z0-9./]{1,16}\$[A-Za-z0-9./]{20,}'),
    'user_home': re.compile(r'(?i)(?:[A-Z]:[/\\]Users[/\\][A-Z0-9_.-]+|/home/[A-Z0-9_.-]+)'),
}


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def scan(text):
    for category, pattern in RULES.items():
        for match in pattern.finditer(text):
            value = match.group()
            if category == 'ipv4':
                try:
                    address = ipaddress.ip_address(value)
                    if address.is_loopback or address.is_unspecified or not address.is_private:
                        continue
                except ValueError:
                    continue
            if category == 'api_key' and set(value[3:]) <= {'x', 'X', '-'}:
                continue
            yield category, text.count('\n', 0, match.start()) + 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', action='store_true')
    parser.add_argument('--reference-file', action='append', type=Path, default=[],
                        help='Optional local device evidence; only match literals in memory, never print them')
    args = parser.parse_args()
    private_literals = set()
    for path in args.reference_file:
        text = path.read_text(encoding='utf-8', errors='replace')
        private_literals.update(re.findall(r'(?im)^Serial\s*:\s*([a-f0-9]{16,})\s*$', text))
        private_literals.update(re.findall(r'(?im)^\s*SSID:\s*(.+)$', text))
        for match in RULES['mac'].finditer(text):
            if match.group() != ':'.join(['00']*6):
                private_literals.add(match.group())
        for match in RULES['ipv4'].finditer(text):
            try:
                address = ipaddress.ip_address(match.group())
                if address.is_private and not address.is_loopback and not address.is_unspecified:
                    private_literals.add(match.group())
            except ValueError:
                pass
    manifest = json.loads((ROOT/'docs/upstream-import-manifest.json').read_text(encoding='utf-8'))
    public_upstream = {manifest['vendor_root']+'/'+r['path']: r['sha256'] for r in manifest['files']}
    records = []
    if args.history:
        for row in git('rev-list', '--objects', '--all').decode().splitlines():
            oid, _, name = row.partition(' ')
            if name and git('cat-file', '-t', oid).strip() == b'blob':
                records.append((name, git('cat-file', 'blob', oid)))
    else:
        for name in git('ls-files', '-z').decode().split('\0'):
            if name:
                records.append((name, (ROOT/name).read_bytes()))
    findings = []
    for name, data in records:
        text = data.decode('utf-8', errors='replace')
        source_is_public = public_upstream.get(name) == hashlib.sha256(data).hexdigest()
        for literal in private_literals:
            if literal in text:
                findings.append({'path':name,'line':text.count('\n',0,text.index(literal))+1,
                                 'category':'known_private_reference','classification':'review_required'})
        for category, line in scan(text):
            findings.append({'path':name,'line':line,'category':category,
                             'classification':'unchanged_public_upstream_example' if source_is_public else 'review_required'})
    review = [r for r in findings if r['classification']=='review_required']
    print(json.dumps({'scope':'reachable_history' if args.history else 'tracked_worktree',
        'blobs_scanned':len(records),'private_reference_literals_checked':len(private_literals),'review_required':review,
        'public_upstream_examples': [r for r in findings if r['classification']!='review_required'],
        'limitations':'Pattern scan, not proof of absence. Git author/public account attribution and public source commit hashes are not private device IDs.'},ensure_ascii=False,indent=2))
    raise SystemExit(bool(review))


if __name__ == '__main__':
    main()
