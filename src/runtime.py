from __future__ import annotations

import argparse


is_debug = __debug__


class CommandLineArguments(argparse.ArgumentParser):
    no_playwright: bool
    no_tkinter: bool

    def __init__(self):
        super().__init__(
            allow_abbrev=False,
            prog='ROBO-ESOCIAL',
            argument_default=None,
            exit_on_error=False,
            add_help=True,
        )
        self.add_argument('--no-playwright', action='store_true')
        self.add_argument('--no-tkinter', action='store_true')

    def parse_argv(self):
        args = self.parse_args()
        self.no_playwright = args.no_playwright
        self.no_tkinter = args.no_tkinter
        return self
