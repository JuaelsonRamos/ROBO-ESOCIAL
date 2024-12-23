from __future__ import annotations

from .custom_types import RowDataType, Url, timestamp

from src.exc import Database
from src.gui.tkinter_global import TkinterGlobal

import re
import string

from datetime import datetime
from typing import Generic, Literal, TypeVar, TypedDict, cast, get_args

from sqlalchemy import (
    BLOB,
    INTEGER,
    REAL,
    TEXT,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    MetaData,
    delete,
    func,
    insert,
    select,
    sql,
    update,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


re_whitespace = re.compile(f'[{string.whitespace}+]')


class SQLDocstring(TypedDict):
    doc: str
    comment: str


def doc(text: str) -> SQLDocstring:
    text = text.replace('\n', ' ')
    text = re_whitespace.sub(' ', text).strip(string.whitespace).strip('.').title()
    return {'doc': text, 'comment': text}


TD = TypeVar('TD', bound=dict[str, RowDataType])


class Base(DeclarativeBase, Generic[TD]):
    metadata = MetaData()
    type_annotation_map = {
        # standard sqlite3 type associaions
        int: INTEGER,
        bytes: BLOB,
        str: TEXT,
        float: REAL,
        # custom type associations
        datetime: DateTime,
        timestamp: REAL,
        Url: Url,
        bool: Boolean,
    }

    typed_dict: TD

    # Common columns
    _id: Mapped[int] = mapped_column(
        autoincrement=True, primary_key=True, nullable=False, unique=True
    )

    @classmethod
    def sync_count(cls) -> int:
        with TkinterGlobal.sqlite.begin() as conn:
            query = func.count().select().select_from(cls)
            result = conn.execute(query).scalar_one_or_none()
            if result is None:
                return 0
            return result

    @classmethod
    def sync_delete_one_from_id(cls, _id: int):
        with TkinterGlobal.sqlite.begin() as conn:
            query = delete(cls).where(cls._id == _id)
            conn.execute(query)
            return _id

    @classmethod
    def sync_delete_many_from_id(cls, *row_ids: int):
        with TkinterGlobal.sqlite.begin() as conn:
            query = delete(cls).where(cls._id.in_(row_ids))
            conn.execute(query)
            return row_ids if isinstance(row_ids, tuple) else tuple(row_ids)

    @classmethod
    def sync_insert_one(cls, data: TD) -> int:
        with TkinterGlobal.sqlite.begin() as conn:
            query = insert(cls).values(**data)
            result = conn.execute(query)
            if result.inserted_primary_key is None:
                raise Database.InsertError
            return cast(int, result.inserted_primary_key[0])

    @classmethod
    def sync_insert_many(cls, *row_data: TD):
        with TkinterGlobal.sqlite.begin() as conn:
            query = insert(cls).values(*row_data)
            result = conn.execute(query)
            if len(result.inserted_primary_key_rows) == 0:
                raise Database.InsertError
            return tuple(cast(int, row[0]) for row in result)

    @classmethod
    def sync_select_one_from_id(cls, _id: int):
        with TkinterGlobal.sqlite.begin() as conn:
            query = select(cls).where(cls._id == _id)
            return conn.execute(query).one_or_none()

    @classmethod
    def sync_select_many_from_id(cls, *row_ids: int):
        with TkinterGlobal.sqlite.begin() as conn:
            query = select(cls).where(cls._id.in_(row_ids))
            result = conn.execute(query).all()
            return result if isinstance(result, tuple) else tuple(result)

    @classmethod
    def sync_update_one_from_id(cls, data: TD, _id: int):
        with TkinterGlobal.sqlite.begin() as conn:
            query = update(cls).where(cls._id == _id).values(**data)
            conn.execute(query)
            return _id

    @classmethod
    def sync_update_many_from_id(cls, data: TD, *row_ids: int):
        with TkinterGlobal.sqlite.begin() as conn:
            query = update(cls).where(cls._id.in_(row_ids)).values(**data)
            conn.execute(query)
            return row_ids if isinstance(row_ids, tuple) else tuple(row_ids)


BrowserType = Literal['firefox', 'chromium']
BrowserEnum = Enum(
    *get_args(BrowserType),
    name='browsertype',
    create_constraint=True,
    validate_strings=True,
)

SameSiteType = Literal['Strict', 'Lax', 'None']
SameSiteEnum = Enum(
    *get_args(SameSiteType),
    name='samesite',
    create_constraint=True,
    validate_strings=True,
)


class CommonColumns:
    @classmethod
    def created(cls):
        return mapped_column(
            nullable=False, unique=False, server_default=sql.func.now()
        )

    @classmethod
    def url(cls):
        return mapped_column(
            nullable=False,
            unique=False,
        )

    @classmethod
    def last_modified(cls):
        return mapped_column(
            nullable=True,
            unique=False,
            server_default=sql.null(),
            server_onupdate=sql.func.now(),
            **doc("""
                Datetime value is only non-null in case it has been modified at least
                once, while a creation date is always present
            """),
        )


class Cookie(Base):
    __tablename__ = 'cookie'
    browser: Mapped[BrowserType] = mapped_column(
        BrowserEnum,
        nullable=False,
        unique=False,
        **doc('which playwright browser does these cookies are valid for'),
    )
    name: Mapped[str] = mapped_column(nullable=False, unique=False)
    value: Mapped[str] = mapped_column(nullable=False, unique=False, default='')
    domain: Mapped[Url] = mapped_column(nullable=False, unique=False)
    path: Mapped[str] = mapped_column(nullable=False, unique=False)
    expires: Mapped[float] = mapped_column(nullable=False, unique=False)
    http_only: Mapped[bool] = mapped_column(nullable=False, unique=False)
    secure: Mapped[bool] = mapped_column(nullable=False, unique=False)
    same_site: Mapped[SameSiteType] = mapped_column(
        SameSiteEnum, nullable=False, unique=False
    )


_local_storage_value_doc = """
    Length of name and value are theorically infinite as long as the total storage
    taken by name=value pairs doesn't exceed 5MiB, whether thats five 1MiB pairs
    (strings), or one 5MiB pair, doesn't matter
"""


class LocalStorage(Base):
    __tablename__ = 'localstorage'
    created: Mapped[datetime] = CommonColumns.created()
    last_modified: Mapped[datetime] = CommonColumns.last_modified()
    origin_id: Mapped[int] = mapped_column(
        ForeignKey('origin._id'), nullable=False, unique=False
    )
    name: Mapped[str] = mapped_column(
        nullable=False,
        unique=False,
        default='',
        **doc(_local_storage_value_doc),
    )
    value: Mapped[str] = mapped_column(
        nullable=False,
        unique=False,
        **doc(_local_storage_value_doc),
    )


class Origin(Base):
    __tablename__ = 'origin'
    created: Mapped[datetime] = CommonColumns.created()
    origin: Mapped[Url] = mapped_column(nullable=False, unique=False)


_origin_localstorage_doc = doc('Association table: one origin to many local_storage')


class Origin_LocalStorage(Base):
    __tablename__ = 'origin_localstorage'
    __table_args__ = {'comment': _origin_localstorage_doc['comment']}
    __doc__ = _origin_localstorage_doc['doc']
    origin_id: Mapped[int] = mapped_column(
        ForeignKey('origin._id'), nullable=False, unique=False
    )
    localstorage_id: Mapped[int] = mapped_column(
        ForeignKey('localstorage._id'), nullable=False, unique=False
    )


_cookie_browsercontext_doc = doc(
    'Association table: one browsercontext to many cookies'
)


class Cookie_BrowserContext(Base):
    __tablename__ = 'cookie_browsercontext'
    __table_args__ = {'comment': _cookie_browsercontext_doc['comment']}
    __doc__ = _cookie_browsercontext_doc['doc']
    browsercontext_id: Mapped[int] = mapped_column(
        ForeignKey('browsercontext._id'),
        nullable=False,
        unique=False,
    )
    cookie_id: Mapped[int] = mapped_column(
        ForeignKey('cookie._id'), nullable=False, unique=False
    )


_origin_browsercontext_doc = doc(
    'Association table: one browsercontext to many origins'
)


class Origin_BrowserContext(Base):
    __tablename__ = 'origin_browsercontext'
    __table_args__ = {'comment': _origin_browsercontext_doc['comment']}
    __doc__ = _origin_browsercontext_doc['doc']
    browsercontext_id: Mapped[int] = mapped_column(
        ForeignKey('browsercontext._id'),
        nullable=False,
        unique=False,
    )
    origin_id: Mapped[int] = mapped_column(
        ForeignKey('origin._id'), nullable=False, unique=False
    )


CertificateOptions: tuple[str, ...] = ('PFX', 'CRT', 'PEM')
CertificateType = Literal[*CertificateOptions]
CertificateEnum = Enum(
    *get_args(CertificateType),
    name='certificate',
    create_constraint=True,
    validate_strings=True,
)


class ClientCertificate(Base):
    __tablename__ = 'clientcertificate'
    created: Mapped[datetime] = CommonColumns.created()
    last_modified: Mapped[datetime] = CommonColumns.last_modified()
    browsercontext_id: Mapped[int] = mapped_column(
        ForeignKey('browsercontext._id'),
        nullable=True,
        unique=False,
        **doc('one client_certificate to many browsercontexts'),
    )
    origin: Mapped[str] = mapped_column(nullable=False, unique=False)
    cert_path: Mapped[str] = mapped_column(
        nullable=True, unique=True, server_default=sql.null()
    )
    cert: Mapped[bytes] = mapped_column(
        nullable=True, unique=True, server_default=sql.null()
    )
    key_path: Mapped[bytes] = mapped_column(
        nullable=True, unique=True, server_default=sql.null()
    )
    key: Mapped[bytes] = mapped_column(
        nullable=True, unique=True, server_default=sql.null()
    )
    pfx_path: Mapped[str] = mapped_column(
        nullable=True, unique=True, server_default=sql.null()
    )
    pfx: Mapped[bytes] = mapped_column(
        nullable=True, unique=True, server_default=sql.null()
    )
    passphrase: Mapped[str] = mapped_column(
        nullable=True, unique=False, server_default=sql.null()
    )
    using_type: Mapped[str] = mapped_column(
        CertificateEnum,
        nullable=True,
        unique=False,
        **doc('What kind of certificate is row refering to'),
    )
    description: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
        **doc('Unique user-defined description for that certificate'),
    )


ColorSchemeType = Literal['light', 'dark', 'no-preference', 'null']
ColorSchemeEnum = Enum(
    *get_args(ColorSchemeType),
    name='colorscheme',
    create_constraint=True,
    validate_strings=True,
)

ReducedMotionType = Literal['reduce', 'no-preference', 'null']
ReducedMotionEnum = Enum(
    *get_args(ReducedMotionType),
    name='reducedmotion',
    create_constraint=True,
    validate_strings=True,
)

ForcedColorsType = Literal['active', 'none', 'null']
ForcedColorsEnum = Enum(
    *get_args(ForcedColorsType),
    name='forcedcolors',
    create_constraint=True,
    validate_strings=True,
)

LocaleType = Literal['pt', 'pt-BR']
LocaleEnum = Enum(
    *get_args(LocaleType),
    name='locale',
    create_constraint=True,
    validate_strings=True,
)

TimezoneIdType = Literal[
    # Simple chart of timezone identifiers at: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    # Some timezone identifiers link to others, e.g. 'America/Porto_Acre'
    # is linked to 'America/Rio_Branco'. Maybe because it's deprecated, since
    # it's listed in the 'backward' list, which I suppose stands for
    # 'Backwards Compatibility'? I didn't read through, just grabbed the values
    # because I know they are valid. I've written 'America/Recife' into a
    # couple of config files throughout time, and the timezone data has
    # always displayed correctly.
    'America/Araguaina',
    'America/Bahia',
    'America/Belem',
    'America/Boa_Vista',
    'America/Campo_Grande',
    'America/Cuiaba',
    'America/Eirunepe',
    'America/Fortaleza',
    'America/Maceio',
    'America/Manaus',
    'America/Noronha',
    'America/Porto_Velho',
    'America/Recife',
    'America/Rio_Branco',
    'America/Santarem',
    'America/Sao_Paulo',
]
TimezoneIdEnum = Enum(
    *get_args(TimezoneIdType),
    name='timezoneid',
    create_constraint=True,
    validate_strings=True,
)


class BrowserContext(Base):
    __tablename__ = 'browsercontext'
    created: Mapped[datetime] = CommonColumns.created()
    last_modified: Mapped[datetime] = CommonColumns.last_modified()
    accept_downloads: Mapped[bool] = mapped_column(nullable=False, unique=False)
    offline: Mapped[bool] = mapped_column(nullable=False, unique=False)
    javascript_enabled: Mapped[bool] = mapped_column(nullable=False, unique=False)
    is_mobile: Mapped[bool] = mapped_column(nullable=False, unique=False)
    has_touch: Mapped[bool] = mapped_column(nullable=False, unique=False)
    color_scheme: Mapped[ColorSchemeType] = mapped_column(
        ColorSchemeEnum, nullable=False, unique=False
    )
    reduced_motion: Mapped[ReducedMotionType] = mapped_column(
        ReducedMotionEnum, nullable=False, unique=False
    )
    forced_colors: Mapped[ForcedColorsType] = mapped_column(
        ForcedColorsEnum, nullable=False, unique=False
    )
    locale: Mapped[LocaleType] = mapped_column(LocaleEnum, nullable=False, unique=False)
    timezone_id: Mapped[TimezoneIdType] = mapped_column(
        TimezoneIdEnum, nullable=False, unique=False
    )


class ProcessingEntry(Base):
    __tablename__ = 'processingentry'
    created: Mapped[datetime] = CommonColumns.created()


ActionOfOriginType = Literal['processing', 'preview', 'recording']
ActionOfOriginEnum = Enum(
    *get_args(ActionOfOriginType),
    name='actionoforigin',
    create_constraint=True,
    validate_strings=True,
)


class ImageMedia(Base):
    __tablename__ = 'imagemedia'
    created: Mapped[datetime] = CommonColumns.created()
    blob: Mapped[bytes] = mapped_column(
        unique=False,
        nullable=False,
        **doc("""
            Blobs are part of a specific processing entry but two binary blobs may
            be equal by pure chance
        """),
    )
    sha512: Mapped[str] = mapped_column(unique=False, nullable=False)
    processingentry_id: Mapped[int] = mapped_column(
        ForeignKey('processingentry._id'),
        unique=False,
        nullable=True,
        **doc('One processingentry to many image_media'),
    )
    timeline_index: Mapped[int] = mapped_column(
        unique=False,
        nullable=True,
        **doc("""
            Index indicating it's position in the order of images created. Image 0 was
            the first created, and so on
        """),
    )
    action_of_origin: Mapped[ActionOfOriginType] = mapped_column(
        ActionOfOriginEnum,
        unique=False,
        nullable=False,
        **doc("""
            Action that originated the image, identical images may be originated from
            diferent actions by pure chance, but they wouldn't be treated differently,
            even if the difference could be noticed"
        """),
    )
    size: Mapped[int] = mapped_column(nullable=False, unique=False)
    width: Mapped[int] = mapped_column(nullable=False, unique=False)
    height: Mapped[int] = mapped_column(nullable=False, unique=False)
