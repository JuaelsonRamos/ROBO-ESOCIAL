""" Criação do executável."""

import sys
from cx_Freeze import Executable, setup

exe_options = {
    "build_exe": "installer/build",
    "packages": [
        "src",
        "tkinter",
        "selenium",
        "pandas",
        "xlrd",
        "openpyxl",
        "webdriver_manager",
        "undetected_chromedriver",
        "unidecode",
        "ctypes",
    ],
    "path": [
        "C:\\Program Files\\Python311\\Lib",
        "C:\\Program Files\\Python311\\DLLs",
        "./.venv-dist/Lib/site-packages",
    ],
    "include_msvcr": True,
    "include_files": [("./assets/", "lib/assets")],
    "optimize": 0,
}



base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="ROBO-ESOCIAL",
    version="0.0.0",
    options={"build_exe": exe_options},
    license_files=["LICENSE", "LEGAL/"],
    executables=[Executable("installer/entrypoint.py", base=base)],
)
