from __future__ import annotations

import os
import glob
import string
import pathlib
import itertools

from argparse import ArgumentParser
from typing import Any, Callable

import jsonc

from gitignore_parser import parse_gitignore


def format(path: str) -> None:
    with open(path, 'rt') as f:
        original = jsonc.load(f)
    content: str = jsonc.dumps(original, indent=2, comments=True)
    content = content.strip(string.whitespace)
    content += '\n'
    with open(path, 'wt') as f:
        f.write(content)


def main():
    args = ArgumentParser(
        os.path.basename(__file__),
        description=(
            'Format one or multiple JSON or JSONC files using relative/absolute paths,'
            'or glob patterns'
        ),
    )
    args.add_argument(
        '--exclude',
        '-e',
        action='append',
        help='Exclude file path from matching',
        default=[],
    )
    args.add_argument(
        '--exclude-glob',
        '-E',
        action='append',
        help='Exclude glob pattern from matching',
        default=[],
    )
    args.add_argument(
        '--glob', action='store_true', default=False, help='Use only glob patterns'
    )
    args.add_argument(
        'files', action='append', default=[], help='List of files/pattern'
    )
    cli_args = args.parse_args()
    global_gitignore = None
    local_gitignore: dict[str, Callable[[Any], bool]] = {}
    try:
        global_gitignore = parse_gitignore(os.path.abspath('./.gitignore'))
    except Exception:
        pass
    files = cli_args.files
    if cli_args.glob:
        files = itertools.chain.from_iterable([glob.iglob(it) for it in cli_args.files])
    exclude_glob: list[str] = []
    if len(cli_args.exclude_glob) > 0:
        exclude_glob = list(
            itertools.chain.from_iterable(
                [glob.glob(it) for it in cli_args.exclude_glob]
            )
        )
    for path in files:
        p = pathlib.Path(path)
        if p.is_dir():
            continue
        if global_gitignore is not None and global_gitignore(path):
            continue
        dirname = str(p.parent)
        if dirname in local_gitignore and local_gitignore[dirname](path):
            continue
        elif (ignore_file := p.parent.joinpath('.gitignore')).is_file():
            ignore = parse_gitignore(str(ignore_file))
            local_gitignore[dirname] = ignore
            if ignore(path):
                continue
        if path in cli_args.exclude or path in exclude_glob:
            continue
        format(path)


if __name__ == '__main__':
    main()
