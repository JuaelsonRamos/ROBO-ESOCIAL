from __future__ import annotations

import sys
import json


def main():
    if len(sys.argv) == 1:
        print(repr(RuntimeError('JSON files not specified')))
        sys.exit(1)
    files = sys.argv[1:]
    for path in files:
        try:
            with open(path) as f:
                original = json.load(f)
                json.dump(
                    original,
                    f,
                    ensure_ascii=False,
                    indent=2,
                    allow_nan=True,
                    sort_keys=False,
                )
        except Exception as err:
            print(repr(err))
            sys.exit(1)


if __name__ == '__main__':
    main()
