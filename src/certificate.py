from __future__ import annotations

import ssl
import hashlib

from datetime import datetime
from typing import Any, Sequence


class CertificateHelper:
    # Jun 11 10:46:39 2027 GMT
    datetime_format = '%b %d %H:%M:%S %Y %Z'

    def __init__(self):
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.context.load_default_certs(ssl.Purpose.CLIENT_AUTH)
        self._sys_certs_cache = None
        self._sys_certs_bytes_cache = None
        self._sys_certs_count_cache = None

    def count_sys_certs(self):
        if self._sys_certs_count_cache is None:
            self._sys_certs_count_cache = len(self.get_sys_certs())
        return self._sys_certs_count_cache

    def get_sys_certs(self):
        if self._sys_certs_cache is None:
            self._sys_certs_cache = self.context.get_ca_certs()
        return self._sys_certs_cache

    def get_sys_certs_as_bytes(self):
        if self._sys_certs_bytes_cache is None:
            self._sys_certs_bytes_cache = self.context.get_ca_certs(binary_form=True)
        return self._sys_certs_bytes_cache

    def get_ca_bytes_from_cert_dict(self, cert_dict: dict):
        try:
            i = self.get_sys_certs().index(cert_dict)
            return self.get_sys_certs_as_bytes()[i]
        except (ValueError, IndexError):
            return None

    def sort_ca_cert_dict_sequence(
        self, certs: Sequence[dict], ascending: bool = True
    ) -> Sequence[dict]:
        indexes = []
        sys_certs = self.get_sys_certs()
        for cert in certs:
            try:
                indexes.append(sys_certs.index(cert))
            except (IndexError, ValueError):
                continue
        indexes.sort(reverse=not ascending)
        return tuple(sys_certs[i] for i in indexes)

    def get_md5_of_many_ca_cert_dicts(
        self, certs: Sequence[dict]
    ) -> Sequence[tuple[str, dict]]:
        sys_certs = self.get_sys_certs()
        result = []
        for i, arg_cert_hash in enumerate(certs):
            try:
                sys_cert_index = sys_certs.index(arg_cert_hash)
                cert_data = self.get_sys_certs_as_bytes()[sys_cert_index]
                md5 = hashlib.md5(cert_data, usedforsecurity=False).hexdigest().upper()
                result.append((md5, certs[i]))
            except IndexError:
                continue
        return result

    def get_br_ca_cert_dicts(self):
        def get_country_str(cert_dict, key):
            return cert_dict[key][0][0][1]

        return [
            c
            for c in self.get_sys_certs()
            if get_country_str(c, 'issuer').lower() == 'br'
            or get_country_str(c, 'subject').lower() == 'br'
        ]

    @classmethod
    def is_expired(cls, cert_dict) -> bool:
        valid_up_to = datetime.strptime(cert_dict['notAfter'], cls.datetime_format)
        return datetime.now() >= valid_up_to

    @classmethod
    def parse_ca_issuer_subject_info(
        cls, cert_dict: dict[str, Any]
    ) -> dict[str, dict[str, str | float]]:
        info = {'issuer': {}, 'subject': {}}
        for key in info.keys():
            info_subject = {}
            all_info_sets: Sequence[Sequence[Sequence[str]]] = cert_dict[key]
            for info_set in all_info_sets:
                info_unit = {}
                if len(info_set) == 0:
                    continue
                elif len(info_set) == 1:
                    pair = info_set[0]
                    info_unit[pair[0]] = pair[1]
                else:
                    buffer = {}
                    for info_pair in info_set:
                        for name, value in info_pair:
                            buffer[name] = value
                    info_unit.update(buffer)
                info_subject.update(info_unit)
            info[key].update(info_subject)
        return info
