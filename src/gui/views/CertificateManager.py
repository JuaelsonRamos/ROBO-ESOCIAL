from __future__ import annotations

from src.certificate import CertificateHelper
from src.gui.utils.units import padding
from src.gui.views.View import View

import tkinter as tk
import tkinter.ttk as ttk

from datetime import datetime
from typing import Callable


class ActionButton(ttk.Button):
    def __init__(
        self,
        master: ttk.Widget,
        text: str = 'ActionButton',
        command: str | Callable = '',
    ) -> None:
        super().__init__(
            master,
            width=15,
            padding=padding(left=5, right=5),
            text=text,
            command=command,
        )
        self.parent_widget = master
        self.tk_callback = command

    def set_command(self, command: str | Callable):
        self.tk_callback = command
        self.config(command=command)

    def disable(self):
        self.config(state=tk.DISABLED)

    def active(self):
        self.config(state=tk.NORMAL)


class CertificateList(ttk.Treeview):
    datetime_format = '%d/%m/%Y %H:%M'
    date_format = '%d/%m/%Y'
    time_format = '%H:%M'

    def __init__(self, master: ttk.Frame):
        self.parent_widget = master
        self.columns = (
            'issued_by',
            'issued_to',
            'valid_from',
            'valid_to',
            'is_expired',
            'md5',
        )
        super().__init__(
            master,
            show='headings',
            columns=self.columns,
            selectmode='browse',
        )
        self.update_btn: ttk.Button = None  # type: ignore
        self.bind('<Visibility>', self.reload_from_system_certificates)

        self.heading('issued_by', text='Emitido Por', anchor=tk.W)
        self.column('issued_by', anchor=tk.W, minwidth=150, width=150)

        self.heading('issued_to', text='Emitido Por', anchor=tk.W)
        self.column('issued_to', anchor=tk.W, minwidth=150, width=150)

        self.heading('valid_from', text='Válido De', anchor=tk.CENTER)
        self.column('valid_from', anchor=tk.CENTER, minwidth=100, width=100)

        self.heading('valid_to', text='Válido Até', anchor=tk.CENTER)
        self.column('valid_to', anchor=tk.CENTER, minwidth=100, width=100)

        self.heading('is_expired', text='Já Expirou?', anchor=tk.CENTER)
        self.column('is_expired', anchor=tk.CENTER, minwidth=50, width=50)

        self.heading('md5', text='Identificator Ùnico', anchor=tk.CENTER)
        self.column('md5', anchor=tk.CENTER, minwidth=150, width=150)

    def create_update_button(self, frame: ttk.Frame):
        self.update_btn = ttk.Button(
            frame, text='Atualizar', command=self.reload_from_system_certificates
        )

    def _column_data_from_cert_dict(
        self, cert_dict: dict, info: dict, expired: bool, md5: str
    ) -> tuple[str, ...]:
        local_tzinfo = datetime.now().astimezone().tzinfo
        time_from = (
            datetime.strptime(cert_dict['notBefore'], CertificateHelper.datetime_format)
            .replace(tzinfo=local_tzinfo)
            .strftime(self.datetime_format)
        )
        time_to = (
            datetime.strptime(cert_dict['notAfter'], CertificateHelper.datetime_format)
            .replace(tzinfo=local_tzinfo)
            .strftime(self.datetime_format)
        )
        issued_by = ''
        issued_to = ''
        cert_info = CertificateHelper.parse_ca_issuer_subject_info(cert_dict)
        issued_by = cert_info['issuer']['organizationName']
        if not isinstance(issued_by, str):
            issued_by = str(issued_by)
        issued_to = cert_info['subject']['organizationName']
        if not isinstance(issued_to, str):
            issued_to = str(issued_to)
        is_expired = 'Sim' if expired else 'Não'
        return (issued_by, issued_to, time_from, time_to, is_expired, md5)

    def reload_from_system_certificates(self, event: tk.Event | None = None):
        cert_helper = CertificateHelper()
        if cert_helper.count_sys_certs() == 0:
            if self.update_btn is not None:
                self.update_btn.config(state=tk.DISABLED)
            return
        br_certs = cert_helper.get_br_ca_cert_dicts()
        md5_cert_pair = cert_helper.get_md5_of_many_ca_cert_dicts(br_certs)
        for md5, cert in md5_cert_pair:
            cert_info = cert_helper.parse_ca_issuer_subject_info(cert)
            cert_expired = cert_helper.is_expired(cert)
            values = self._column_data_from_cert_dict(
                cert, cert_info, cert_expired, md5
            )
            if self.exists(md5):
                self.item(md5, values=values)
                continue
            self.insert('', 'end', md5, values=values)
        all_iids = self.get_children()
        md5_set = set(pair[0] for pair in md5_cert_pair)
        excess = md5_set.difference(all_iids)
        if len(excess) == 0:
            return
        self.delete(*excess)


class CertificateManager(View):
    def __init__(self, master):
        super().__init__(master, 'Certificados')
        self.tree = CertificateList(self.content_frame)
        self.tree.create_update_button(self.title_frame)
        self.yscroll = ttk.Scrollbar(
            self.content_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.xscroll = ttk.Scrollbar(
            self.content_frame, orient=tk.HORIZONTAL, command=self.tree.xview
        )

    def reload_tree(self):
        self.tree.event_generate

    def pack(self):
        super().pack()
        self.xscroll.pack(side=tk.BOTTOM, fill=tk.X, expand=tk.FALSE)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        self.yscroll.pack(side=tk.LEFT, fill=tk.Y, expand=tk.FALSE)
        self.tree.update_btn.pack(side=tk.RIGHT, ipadx=2)
