from __future__ import annotations

from .custom_types import Url, timestamp

from src.utils import Singleton

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, get_args

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
    sql,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
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


@dataclass(frozen=False, init=True, slots=True)
class Docstrings(metaclass=Singleton):
    cookie = {'browser': 'which playwright browser does these cookies are valid for'}
    localstorage = {
        'name_value': """
            length of name and value are theorically infinite as long as the total storage
            taken by name=value pairs doesn't exceed 5MiB, whether thats five 1MiB pairs
            (strings), or one 5MiB pair, doesn't matter
        """
    }
    _common = {
        'last_modified': 'datetime value is only non-null in case it has been modified at least once, while a creation date is always present',
    }
    origin_localstorage = {
        'table': 'Association table: one origin to many local_storage',
    }
    cookie_browsercontext = {
        'table': 'Association table: one browser_context to many cookies',
    }
    origin_browsercontext = {
        'table': 'Association table: one browser_context to many origins',
    }
    clientcertificate = {
        'browsercontext_id': 'one client_certificate to many browser_contexts',
    }
    imagemedia = {
        'blob': 'Blobs are part of a specific processing entry but two binary blobs may be equal by pure chance',
        'timeline_index': "Index indicating it's position in the order of images created. Image 0 was the first created, and so on",
        'processingentry_id': 'one processing_entry to many image_media',
        'action_of_origin': "action that originated the image, identical images may be originated from diferent actions by pure chance, but they wouldn't be treated differently, even if the difference could be noticed",
    }


@dataclass(frozen=False, init=True, slots=True)
class CommonColumns(metaclass=Singleton):
    @property
    def _id(self):
        return mapped_column(
            autoincrement=True, primary_key=True, nullable=False, unique=True
        )

    @property
    def created(self):
        return mapped_column(
            nullable=False, unique=False, server_default=sql.func.now()
        )

    @property
    def url(self):
        return mapped_column(
            nullable=False,
            unique=False,
        )

    @property
    def last_modified(self):
        return mapped_column(
            nullable=True,
            unique=False,
            server_default=sql.null(),
            server_onupdate=sql.func.now(),
        )


docs = Docstrings()
common_columns = CommonColumns()


class Cookie(Base):
    __tablename__ = 'cookie'
    _id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    browser: Mapped[BrowserType] = mapped_column(
        BrowserEnum,
        nullable=False,
        unique=False,
        doc=docs.cookie['browser'],
        comment=docs.cookie['browser'],
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


class LocalStorage(Base):
    __tablename__ = 'localstorage'
    _id: Mapped[int] = common_columns._id
    created: Mapped[datetime] = common_columns.created
    last_modified: Mapped[datetime] = common_columns.last_modified
    origin_id: Mapped[int] = mapped_column(
        ForeignKey('origin._id'), nullable=False, unique=False
    )
    name: Mapped[str] = mapped_column(
        nullable=False,
        unique=False,
        default='',
        doc=docs.localstorage['name_value'],
        comment=docs.localstorage['name_value'],
    )
    value: Mapped[str] = mapped_column(
        nullable=False,
        unique=False,
        doc=docs.localstorage['name_value'],
        comment=docs.localstorage['name_value'],
    )


class Origin(Base):
    __tablename__ = 'origin'
    _id: Mapped[int] = common_columns._id
    created: Mapped[datetime] = common_columns.created
    origin: Mapped[Url] = mapped_column(nullable=False, unique=False)


class Origin_LocalStorage(Base):
    __tablename__ = 'origin_localstorage'
    __table_args__ = {'comment': docs.origin_localstorage['table']}
    __doc__ = docs.origin_localstorage['table']
    _id: Mapped[int] = common_columns._id
    origin_id: Mapped[int] = mapped_column(
        ForeignKey('origin._id'), nullable=False, unique=False
    )
    localstorage_id: Mapped[int] = mapped_column(
        ForeignKey('localstorage._id'), nullable=False, unique=False
    )


class Cookie_BrowserContext(Base):
    __tablename__ = 'cookie_browsercontext'
    __table_args__ = {'comment': docs.cookie_browsercontext['table']}
    __doc__ = docs.cookie_browsercontext['table']
    _id: Mapped[int] = common_columns._id
    browsercontext_id: Mapped[int] = mapped_column(
        ForeignKey('browsercontext._id'),
        nullable=False,
        unique=False,
    )
    cookie_id: Mapped[int] = mapped_column(
        ForeignKey('cookie._id'), nullable=False, unique=False
    )


class Origin_BrowserContext(Base):
    __tablename__ = 'origin_browsercontext'
    __table_args__ = {'comment': docs.origin_browsercontext['table']}
    __doc__ = docs.origin_browsercontext['table']
    _id: Mapped[int] = common_columns._id
    browsercontext_id: Mapped[int] = mapped_column(
        ForeignKey('browsercontext._id'),
        nullable=False,
        unique=False,
    )
    origin_id: Mapped[int] = mapped_column(
        ForeignKey('origin._id'), nullable=False, unique=False
    )


class ClientCertificate(Base):
    __tablename__ = 'clientcertificate'
    _id: Mapped[int] = common_columns._id
    created: Mapped[datetime] = common_columns.created
    last_modified: Mapped[datetime] = common_columns.last_modified
    browsercontext_id: Mapped[int] = mapped_column(
        ForeignKey('browsercontext._id'),
        nullable=False,
        unique=False,
        doc=docs.clientcertificate['browsercontext_id'],
        comment=docs.clientcertificate['browsercontext_id'],
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
    *get_args(LocaleType),
    name='timezoneid',
    create_constraint=True,
    validate_strings=True,
)


class BrowserContext(Base):
    __tablename__ = 'browsercontext'
    _id: Mapped[int] = common_columns._id
    created: Mapped[datetime] = common_columns.created
    last_modified: Mapped[datetime] = common_columns.last_modified
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
    _id: Mapped[int] = common_columns._id
    created: Mapped[datetime] = common_columns.created


ActionOfOriginType = Literal['processing', 'preview', 'recording']
ActionOfOriginEnum = Enum(
    *get_args(ActionOfOriginType),
    name='actionoforigin',
    create_constraint=True,
    validate_strings=True,
)


class ImageMedia(Base):
    __tablename__ = 'imagemedia'
    _id: Mapped[int] = common_columns._id
    created: Mapped[datetime] = common_columns.created
    blob: Mapped[bytes] = mapped_column(
        unique=False,
        nullable=False,
        doc=docs.imagemedia['blob'],
        comment=docs.imagemedia['blob'],
    )
    sha512: Mapped[str] = mapped_column(unique=False, nullable=False)
    processingentry_id: Mapped[int] = mapped_column(
        ForeignKey('processing_entry._id'),
        unique=False,
        nullable=True,
        doc=docs.imagemedia['processingentry_id'],
        comment=docs.imagemedia['processingentry_id'],
    )
    timeline_index: Mapped[int] = mapped_column(
        unique=False,
        nullable=True,
        doc=docs.imagemedia['timeline_index'],
        comment=docs.imagemedia['timeline_index'],
    )
    action_of_origin: Mapped[ActionOfOriginType] = mapped_column(
        ActionOfOriginEnum,
        unique=False,
        nullable=False,
        doc=docs.imagemedia['action_of_origin'],
        comment=docs.imagemedia['action_of_origin'],
    )
    size: Mapped[int] = mapped_column(nullable=False, unique=False)
    width: Mapped[int] = mapped_column(nullable=False, unique=False)
    height: Mapped[int] = mapped_column(nullable=False, unique=False)
