import sys
from cx_Freeze import setup, Executable

exe_options = {
    "build_exe": "installer/build",
    "packages": [
        "src",
        "tkinter",
        "selenium",
        "pandas",
        "xlrd",
        "openpyxl",
        "undetected_chromedriver",
        "unidecode",
        "ctypes",
    ],
    "path": [
        "C:\Program Files\Python311\Lib",
        "C:\Program Files\Python311\DLLs",
        "./.venv-dev/Lib/site-packages",
    ],
    "include_msvcr": True,
    "include_files": [("./assets/", "lib/assets")],
    "optimize": 0,
}

base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="My Cython App",
    version="0.0.0",
    options={"build_exe": exe_options},
    executables=[Executable("installer/entrypoint.py", base=base)],
)
