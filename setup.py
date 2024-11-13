"""Configuração de compilação e instalação do código fonte como pacote."""

# pylint: disable=all
from __future__ import annotations

import string
import argparse

from scripts.boostrap import install_playwright_deps, make_dirs


scripts = {
    'make_dirs': make_dirs,
    'install_playwright_deps': install_playwright_deps,
}


def main():
    args = argparse.ArgumentParser(
        prog='setup.py',
        description='Script de configuração e ações automáticas no projeto.',
        add_help=True,
        allow_abbrev=False,
        prefix_chars='-',
    )
    args.add_argument(
        'command',
        help='Baixa dependências binárias da biblioteca Playwright, como navegadores, NodeJS, etc.',
    )
    argv = args.parse_args()
    command = argv.command
    if argv.command is None or argv.command == '':
        command = 'install_playwright_deps'
    elif not isinstance(argv.command, str):
        raise ValueError(f'{type(argv.command)=} should be str')
    else:
        command = command.strip(string.whitespace)
    if command not in scripts:
        raise ValueError(f"script '{command}' desconhecido")
    make_dirs()
    if command == 'make_dirs':
        return
    func = scripts[command]
    func()


if __name__ == '__main__':
    main()
