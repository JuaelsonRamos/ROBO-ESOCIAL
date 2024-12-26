from __future__ import annotations

import io
import json
import hashlib

from typing import Any, Literal


class FirefoxConfig:
    # documentation
    # installer config https://firefox-source-docs.mozilla.org/browser/installer/windows/installer/FullConfig.html
    # about: links https://kb.mozillazine.org/About_protocol_links
    encoding = 'utf-8'
    override_ini: dict[str, dict[str, str | float | bool | int]] = {
        'App': {'Vendor': 'Mozilla', 'Name': 'Firefox'},
        'XRE': {'EnableProfileMigrator': False},
    }
    policies_json: dict[str, Any] = {
        'policies': {
            'AppAutoUpdate': False,
            'AutofillAddressEnabled': False,
            'AutofillCreditCardEnabled': False,
            'BackgroundAppUpdate': False,
            'BlockAboutAddons': not __debug__,
            'BlockAboutConfig': not __debug__,
            'BlockAboutProfiles': not __debug__,
            'BlockAboutSupport': not __debug__,
            'DisableAppUpdate': True,
            'DisableDeveloperTools': not __debug__,
            'DisableFeedbackCommands': not __debug__,
            'DisableFirefoxAccounts': not __debug__,
            'DisableFirefoxStudies': True,
            'DisableForgetButton': True,
            'DisableFormHistory': not __debug__,
            'DisablePasswordReveal': not __debug__,
            'DisablePocket': True,
            'DisablePrivateBrowsing': not __debug__,
            'DisableProfileImport': True,
            'DisableProfileRefresh': not __debug__,
            'DisableSafeMode': not __debug__,
            'DisableSecurityBypass': {
                'InvalidCertificate': True,
                'SafeBrowsing': True,
            },
            'DisableSetDesktopBackground': True,
            'DisableSystemAddonUpdate': True,
            'DisableTelemetry': True,
            'DisplayBookmarksToolbar': 'never' if not __debug__ else 'always',
            'DisplayMenuBar': 'never' if not __debug__ else 'always',
            'DontCheckDefaultBrowser': True,
            'EnableTrackingProtection': {
                'Lock': True,
                'Cryptomining': True,
                'EmailTracking': True,
            },
            'EncryptedMediaExtensions': {
                'Enabled': True,
                'Locked': True,
            },
            'FirefoxSuggest': {
                'WebSuggestions': False,
                'SponsoredSuggestions': False,
                'ImproveSuggest': False,
                'Locked': True,
            },
            'HardwareAcceleration': True,
            'NoDefaultBookmarks': True,
            'OfferToSaveLogins': False,
            'OfferToSaveLoginsDefault': False,
            'OverrideFirstRunPage': '',  # not displayerd
            'OverridePostUpdatePage': '',  # not displayed
            'PasswordManagerEnabled': __debug__,
            'Permissions': {
                'Camera': {
                    'Locked': not __debug__,
                    'BlockNewRequests': True,
                },
                'Microphone': {
                    'Locked': not __debug__,
                    'BlockNewRequests': True,
                },
                'Notifications': {
                    'Locked': not __debug__,
                    'BlockNewRequests': True,
                },
                'Autoplay': {
                    'Locked': not __debug__,
                    'BlockNewRequests': True,
                },
                'VirtualReality': {
                    'Locked': not __debug__,
                    'BlockNewRequests': True,
                },
                'Location': {
                    'Locked': not __debug__,
                    'BlockNewRequests': True,
                },
            },
            'PictureInPicture': {
                'Locked': True,
                'Enabled': False,
            },
            # 'PopupBlocking': {},  # TODO consider blocking
            'PrimaryPassword': False,
            'PrivateBrowsingModeAvailability': 1,  # not available
            'SanitizeOnShutdown': {
                'FormData': True,
                'Locked': not __debug__,
            },
            'SearchBar': 'separate',  # not displayed
            'SearchSuggestEnabled': __debug__,
            'ShowHomeButton': False,
            'StartDownloadsInTempDirectory': False,
            'SupportMenu': False,
            'TranslateEnabled': False,
            'UserMessaging': {
                'Locked': True,
                'ExtensionRecommendations': False,
                'FeatureRecommendations': False,
                'UrlbarInterventions': False,
                'SkipOnboarding': True,
                'MoreFromMozilla': False,
                'FirefoxLabs': False,
            },
            'WindowsSSO': False,
        }
    }
    user_js: dict[str, str | float | bool] = {
        'prefs.converted-to-utf8': True,
        'browser.startup.page': 0,
        'browser.tabs.loadOnNewTab': -1,
        'update.interval': 1000 * 60 * 60 * 24,  # 1 day in milliseconds
        'update.severity': 2,
        'update.showSlidingNotification': False,
        'update_notifications.enabled': False,
    }

    @classmethod
    def parse_override_ini(cls) -> bytes:
        # documentation
        # -override https://wiki.mozilla.org/Firefox/CommandLineOptions#-override_/path/to/override.ini
        # overview of defaults https://github.com/microsoft/playwright/issues/18094
        # source file https://searchfox.org/mozilla-central/source/build/application.ini.in
        # overview explanation https://virtuallyjason.blogspot.com/2013/10/cutomizing-mozilla-firefox-for.html
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
        # User.js file https://kb.mozillazine.org/User.js_file
        # Locking proferences https://kb.mozillazine.org/Locking_preferences
        # about:config entries https://kb.mozillazine.org/About:config_entries
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
