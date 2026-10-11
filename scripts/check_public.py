"""Check the intended tracked publication slice, excluding private ignored material."""
import re
import subprocess
from pathlib import Path

PATTERNS=[r'313east\.cc',r'/Users/',r'192\.168\.',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'gh[pousr]_[A-Za-z0-9]{30,}',r'AKIA[A-Z0-9]{16}']
def main():
    files=subprocess.check_output(['git','ls-files','-z'],text=True).split('\0')
    failures=[]
    for name in filter(None,files):
        if name=='scripts/check_public.py':continue
        p=Path(name)
        if not p.is_file():continue
        try:text=p.read_text()
        except UnicodeDecodeError:continue
        for pattern in PATTERNS:
            if re.search(pattern,text):failures.append(name)
        if name.startswith(('.local/','factory-private/','secrets/')):failures.append(name)
    if failures:raise SystemExit('Publication rejected for files: '+', '.join(sorted(set(failures))))
    print(f'Publication slice checked: {len(list(filter(None,files)))} tracked files; no private endpoint/path/key patterns found.')
if __name__=='__main__':main()
