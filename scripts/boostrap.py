from __future__ import annotations

import os
import sys
import tomllib

from pathlib import Path


with open('pyproject.toml', 'rb') as f:
    pyproject = tomllib.load(f)
    try:
        pyproject = pyproject['tool']['esocial']
    except IndexError as err:
        raise ValueError('missing pyproject.toml section') from err


def make_dirs():
    try:
        build = pyproject['build']
        path = Path(build['base_dir'])
        path.mkdir(parents=True, exist_ok=True)
        other_dirs = (
            build['output_dir'],
            build['playwright']['download_dir'],
        )
        for other in other_dirs:
            sub_dir = path.joinpath(other)
            sub_dir.mkdir(parents=True, exist_ok=True)
    except IndexError as err:
        raise ValueError('missing configuration property') from err


def install_playwright_deps():
    try:
        build = pyproject['build']
        playwright = build['playwright']
        path = Path(build['base_dir']).joinpath(playwright['download_dir'])
        assert path.is_dir()
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(path.expanduser().absolute())
        browsers = playwright['install_browsers']
        assert isinstance(browsers, list)
        assert all(isinstance(value, str) for value in browsers)
        # first argument is skipped
        args = ['<exe_path_skipped>', 'install']
        if playwright.get('install_deps', False):
            args.append('--with-deps')
        if playwright.get('force', False):
            args.append('--force')
        args.extend(browsers)
    except IndexError as err:
        raise ValueError('missing option') from err

    from playwright.__main__ import main

    tmp = sys.argv
    try:
        sys.argv = args
        main()
    finally:
        sys.argv = tmp
