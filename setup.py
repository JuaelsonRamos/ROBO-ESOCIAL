from setuptools import setup, Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize
from typing import List
from os.path import relpath, abspath
from pathlib import PurePath
from glob import glob


def get_extensions(files: List[str], project_root: str) -> List[Extension]:
    extensions = []
    for file in files:
        relative = PurePath(relpath(file, project_root))
        if relative.stem == "__init__":
            parts = relative.parent.parts
            if len(parts) == 1:  # apenas "src", por exemplo
                continue
            extensions.append(Extension(".".join(parts), [file]))
        else:
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
