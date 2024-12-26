from __future__ import annotations

import io
import json
import hashlib

from typing import Literal


class FirefoxConfig:
    encoding = 'utf-8'
    override_ini: dict[str, dict[str, str | float | bool | int]] = {
        'App': {'Vendor': 'Mozilla', 'Name': 'Firefox'},
        'XRE': {'EnableProfileMigrator': False},
    }
    policies_json: dict = {}
    user_js: dict[str, str | float | bool] = {}

    @classmethod
    def parse_override_ini(cls) -> bytes:
        # documentation
        # -override https://wiki.mozilla.org/Firefox/CommandLineOptions#-override_/path/to/override.ini
        # overview of defaults https://github.com/microsoft/playwright/issues/18094
        # source file https://searchfox.org/mozilla-central/source/build/application.ini.in
        if len(cls.override_ini) == 0:
            return bytes()
        with io.BytesIO() as buffer:
            for section, options in cls.override_ini.items():
                buffer.write(f'[{section}]\n'.encode(cls.encoding))
                for key, value in options.items():
                    if isinstance(value, str):
                        browser_value = value
                    elif isinstance(value, (float, int)):
                        browser_value = str(value)
                    elif isinstance(value, bool):
                        browser_value = str(int(value))
                    else:
                        raise RuntimeError('unknown application.ini data type')
                    buffer.write(f'{key}={browser_value}\n'.encode(cls.encoding))
                buffer.write(b'\n')
            return buffer.getvalue()

    @classmethod
    def hash_override_ini(cls) -> hashlib._Hash:
        return hashlib.md5(cls.parse_override_ini(), usedforsecurity=False)

    @classmethod
    def parse_policies_json(cls) -> bytes:
        # documentation
        # policies-templates https://github.com/mozilla/policy-templates/
        if len(cls.policies_json) == 0:
            return bytes()
        json_str = json.dumps(
            cls.policies_json,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(',', ':'),
        )
        return json_str.encode(cls.encoding)

    @classmethod
    def hash_policies_json(cls) -> hashlib._Hash:
        return hashlib.md5(cls.parse_policies_json(), usedforsecurity=False)

    @classmethod
    def parse_user_js(
        cls, *, function: Literal['user_pref', 'pref', 'lockPref'] = 'user_pref'
    ) -> bytes:
        # documentation
        # libpref https://firefox-source-docs.mozilla.org/modules/libpref/index.html
        if len(cls.user_js) == 0:
            return bytes()
        string_limit_1MiB = 1024 * 1024
        with io.BytesIO() as buffer:
            for key, value in cls.user_js.items():
                if isinstance(value, str):
                    if len(value) > string_limit_1MiB:
                        # strings are 8-bit C character arrays, so len() is same as
                        # effective size
                        continue
                    browser_value = f'"{value}"'
                elif isinstance(value, float):
                    browser_value = str(value) if value % 1 > 0 else str(int(value))
                elif isinstance(value, bool):
                    browser_value = str(value).lower()
                else:
                    raise RuntimeError('cannot parse value in user_js dict')
                buffer.write(
                    f'{function}("{key}",{browser_value});'.encode(cls.encoding)
                )
            return buffer.getvalue()

    @classmethod
    def hash_user_js(cls) -> hashlib._Hash:
        return hashlib.md5(cls.parse_user_js(), usedforsecurity=False)
