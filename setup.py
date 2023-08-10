""" Configuração de compilação e instalação do código fonte como pacote."""

# pylint: disable=all

from glob import glob
from os.path import abspath, relpath
from pathlib import PurePath
from typing import List

from Cython.Build import cythonize
from Cython.Distutils import build_ext
from setuptools import Extension, setup

__all__ = ["get_extensions"]


def get_extensions(files: List[str], project_root: str) -> List[Extension]:
    extensions = []
    for file in files:
        relative = PurePath(relpath(file, project_root))
        extensions.append(
            Extension(".".join(relative.parent.joinpath(relative.stem).parts), [file])
        )
    return extensions


extensions = get_extensions([*glob("src/*.py"), *glob("src/**/*.py")], abspath("."))

extensions = cythonize(
    extensions,
    build_dir="build_cython",
    compiler_directives={
        "language_level": "3",
        "always_allow_keywords": True,
        "embedsignature": True,
    },
)

setup(
    name="src",
    version="0.0.0",
    cmdclass={
        "build_ext": build_ext,
    },
    ext_modules=extensions,
    zip_safe=False,
    include_package_data=True,
)
