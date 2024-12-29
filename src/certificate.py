from __future__ import annotations

import ssl
import hashlib

from datetime import datetime
from typing import Any, Sequence


class CertificateHelper:
    def __init__(self):
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.context.load_default_certs(ssl.Purpose.CLIENT_AUTH)
        self._sys_certs_cache = None
        self._sys_certs_bytes_cache = None
        self._sys_certs_count_cache = None

    def count_sys_certs(self):
        if self._sys_certs_count_cache is None:
            self._sys_certs_count_cache = len(self.get_sys_certs())

    def get_sys_certs(self):
        if self._sys_certs_cache is None:
            self._sys_certs_cache = self.context.get_ca_certs()
        return self._sys_certs_cache

    def get_sys_certs_as_bytes(self):
        if self._sys_certs_bytes_cache is None:
            self._sys_certs_bytes_cache = self.context.get_ca_certs(binary_form=True)
        return self._sys_certs_bytes_cache

    def get_ca_bytes_from_cert_dict(self, cert_dict: dict):
        self.get_ca_bytes_from_cert_dict_hash(hash(cert_dict))

    def sort_ca_cert_dict_sequence(
        self, certs: Sequence[dict], ascending: bool = True
    ) -> Sequence[dict]:
        order: dict[int, dict] = {}
        bigger_index = max(len(self.get_sys_certs()), len(certs))
        for i in range(bigger_index):
            sys_cert, arg_cert = None, None
            try:
                arg_cert = certs[i]
            except IndexError:
                break
            try:
                sys_cert = self.get_sys_certs()[i]
            except IndexError:
                order[max(order.keys()) + 1] = arg_cert
                continue
            if hash(sys_cert) == hash(arg_cert):
                order[i] = arg_cert
        in_order = tuple(
            pair[1]
            for pair in sorted(
                order.items(), key=lambda key_value: key_value[0], reverse=not ascending
            )
        )
        return in_order

    def get_md5_of_many_ca_cert_dicts(
        self, certs: Sequence[dict]
    ) -> Sequence[tuple[str, dict]]:
        sys_cert_hashed = tuple(hash(cert) for cert in self.get_sys_certs())
        arg_cert_hashed = tuple(hash(cert) for cert in certs)
        result = []
        for i, arg_cert_hash in enumerate(arg_cert_hashed):
            try:
                sys_cert_index = sys_cert_hashed.index(arg_cert_hash)
                cert_data = self.get_sys_certs_as_bytes()[sys_cert_index]
                result.append(
                    (
                        hashlib.md5(cert_data, usedforsecurity=False).hexdigest(),
                        certs[i],
                    )
                )
            except IndexError:
                continue
        return result

    def get_ca_bytes_from_cert_dict_hash(self, cert_dict_hash: int) -> bytes | None:
        index: int | None = None
        for i, cert in enumerate(self.get_sys_certs()):
            if hash(cert) == cert_dict_hash:
                index = i
                break
        if index is None:
            return None
        return self.get_sys_certs_as_bytes()[index]

    def get_br_ca_cert_dicts(self):
        def get_country_str(cert_dict, key):
            return cert_dict[key][0][0][1]

        return [
            c
            for c in self.get_sys_certs()
            if get_country_str(c, 'issuer').lower() == 'br'
            or get_country_str(c, 'subject').lower() == 'br'
        ]

    def is_expired(self, cert_dict) -> bool:
        valid_from = datetime.fromisoformat(cert_dict['notBefore'])
        valid_up_to = datetime.fromisoformat(cert_dict['notAfter'])
        return valid_from <= datetime.now() < valid_up_to

    def parse_ca_issuer_subject_info(self, cert_dict: dict[str, Any]):
        generic_unique_id = cert_dict['serialNumber']
        info = {}
        for key in ('issuer', 'subject'):
            all_cert_info: Sequence[Sequence[Sequence[str]]] = cert_dict[key]
            for info_layer in all_cert_info:
                org_name = ''
                all_org_info = []
                for data_keyvalue_pairs in info_layer:
                    info_unit = {}
                    for data_kind_name, value in data_keyvalue_pairs:
                        info_unit[data_kind_name] = value
                    org_name = info_unit['organizationName']
                    all_org_info.append(info_unit)
                if org_name not in info:
                    info[org_name] = {}
                if generic_unique_id not in info[org_name]:
                    info[org_name][generic_unique_id] = {}
                info[org_name][generic_unique_id][key] = tuple(all_org_info)
        return info
