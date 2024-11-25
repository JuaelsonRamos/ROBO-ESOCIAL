from __future__ import annotations

import sys
import string

import jsonc


def main():
    if len(sys.argv) == 1:
        print(repr(RuntimeError('JSON files not specified')))
        sys.exit(1)
    files = sys.argv[1:]
    for path in files:
        with open(path, 'rt') as f:
            original = jsonc.load(f)
        content: str = jsonc.dumps(original, indent=2, comments=True)
        content = content.strip(string.whitespace)
        content += '\n'
        with open(path, 'wt') as f:
            f.write(content)


if __name__ == '__main__':
    main()
