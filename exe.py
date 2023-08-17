"""Criação do executável."""

import sys
from typing import List
from cx_Freeze import Executable, setup
import json
from urllib.parse import urlparse
from setuptools import Command
from markdown import Markdown, markdown
import pdfkit
import os

__all__ = ["Licenses", "criar_info_licencas"]

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
        "C:\\Program Files\\Python311\\Lib",
        "C:\\Program Files\\Python311\\DLLs",
        "./.venv-dist/Lib/site-packages",
    ],
    "include_msvcr": True,
    "include_files": [
        ("./assets/", "lib/assets"),
        ("./LEGAL_dist", "LEGAL"),
    ],
    "optimize": 0,
}

base = "Win32GUI" if sys.platform == "win32" else None


def criar_info_licencas() -> None:
    """Cria diretório preparado com todas as informações de licença necessárias e retorna o caminho
    de destino do novo diretório.

    Alguns possíveis erros são ignorados porque são supostos a não acontecer. O sistema de arquivos
    deve ser preparado na linha de comando (justfile) e o formato dos JSON são definidos e
    garantidos pelo programa que os gera. É esperado que o formato só mude entre versões major
    (oremos).

    :return: Tuple com caminho fonte e de destino no formato especificado pelo cx_Freeze
    """

    def nao_especificado(text: str) -> str:
        return "Não especificado" if text == "UNKNOWN" else text

    def is_url(line: str) -> bool:
        try:
            url = urlparse(line)
            return all([url.scheme, url.netloc])
        except:
            return False

    md_opts = {
        "output_format": "html",
        "extensions": [
            "markdown.extensions.extra",
            "markdown.extensions.codehilite",
            "markdown.extensions.smarty",
        ],
    }
    html_opts = {"user-style-sheet": "./templates/LEGAL/style.css", "encoding": "utf-8"}
    compiled_html = "./LEGAL/compiled/all.html"
    compiled_md = "./LEGAL/compiled/all.md"

    # Criandos os arquivos de licença em texto puro
    with open("./LEGAL/info-arquivos.json", "rb") as license_files_info:
        info = json.load(license_files_info)
        for package in info:
            name = package["Name"]
            version = package["Version"]
            license = package["License"]
            text = package["LicenseText"]
            new_file_name = f"./LEGAL_dist/{name}-{version.lower()}.LICENSE"
            description = (
                f"Nome: {name}\n"
                f"Versão: {nao_especificado(version)}\n"
                f"Licença: {nao_especificado(license)}\n"
            )

            if text == "UNKNOWN":
                description += f"Conteúdo da licença: {nao_especificado(text)}\n"
                with open(new_file_name, "wt", encoding="utf-8") as file:
                    file.write(description)
                continue

            bigger_line = max(len(line) for line in text.split("\n") if not is_url(line))
            description += f"\nConteúdo da licença:\n{'-' * bigger_line}\n\n{text.rstrip()}\n"
            with open(new_file_name, "wt", encoding="utf-8") as file:
                file.write(description)

    # Compilando planilha de relação dos pacotes
    with (
        open("./templates/LEGAL/lista_pacotes.md", "rt", encoding="utf-8") as template,
        open("./LEGAL/relacao.md", "rt", encoding="utf-8") as info_sheet,
        open(compiled_html, "wt", encoding="utf-8") as html,
        open(compiled_md, "wt", encoding="utf-8") as md,
    ):
        formatted: str = template.read().format(spreadsheet=info_sheet.read())
        md.write(formatted)
        html.write(markdown(formatted, **md_opts))

    # Compilando planilha de contagem de licenças
    with (
        open("./templates/LEGAL/resumo_licencas.md", "rt", encoding="utf-8") as template,
        open("./LEGAL/resumo.md", "rt", encoding="utf-8") as info_sheet,
        open(compiled_html, "at", encoding="utf-8") as html,
        open(compiled_md, "at", encoding="utf-8") as md,
    ):
        formatted: str = template.read().format(spreadsheet=info_sheet.read())
        md.write(formatted)
        html.write(markdown(formatted, **md_opts))

    # Compilando todas as licenças em markdown e html
    with (
        open("./LEGAL/relacao.json", "rb") as package_info,
        open("./LEGAL/info-arquivos.json", "rb") as license_files_info,
    ):
        info = json.load(package_info)
        license_info = json.load(license_files_info)
        license_texts = [lic["LicenseText"] for lic in license_info]
        for package, text in zip(info, license_texts):
            with (
                open("./templates/LEGAL/pagina_licenca.md", "rt", encoding="utf-8") as template,
                open(compiled_html, "at", encoding="utf-8") as html,
                open(compiled_md, "at", encoding="utf-8") as md,
            ):
                formatted: str = template.read().format(
                    name=package["Name"],
                    license=nao_especificado(package["License"]),
                    version=nao_especificado(package["Version"]),
                    author=nao_especificado(package["Author"]),
                    maintainers=nao_especificado(package["Maintainer"]),
                    url=nao_especificado(package["URL"]),
                    license_text=nao_especificado(text),
                )
                md.write(formatted)
                html.write(markdown(formatted, **md_opts))

    # Adicionando as páginas que não precisam de processamento ao início do
    # documento na ordem especificada.
    with (os.scandir("./templates/LEGAL/standalone/") as folder,):
        standalone_pages: List[os.DirEntry[str]] = list(folder)
        standalone_pages.sort(key=lambda f: int(f.name.split("-")[0]))
        for page in standalone_pages:
            with (
                open(page.path, "rt", encoding="utf8") as stand_page,
                open(compiled_html, "r+", encoding="utf-8") as html,
                open(compiled_md, "r+", encoding="utf-8") as all_md,
            ):
                md_content, html_content = all_md.read(), html.read()
                all_md.seek(0, 0)
                html.seek(0, 0)
                all_md.write(stand_page.read() + md_content)
                html.write(markdown(stand_page.read(), **md_opts) + html_content)

    # Criando sumário e adicionando ao início do documento
    with (
        open(compiled_md, "rt", encoding="utf-8") as all_md,
        open(compiled_html, "r+", encoding="utf-8") as html,
    ):
        opts = md_opts.copy()
        opts["extensions"].append("markdown.extensions.toc")
        md = Markdown(**opts)
        md.convert(all_md.read())
        html_content = html.read()
        html.seek(0, 0)
        html.write(md.toc + html_content)

    # Criando documento
    pdfkit.from_file(
        compiled_html,
        verbose=True,
        output_path="./LEGAL_dist/Relação.pdf",
        options=html_opts,
    )


class Licenses(Command):
    user_options = []

    def initialize_options(self) -> None:
        pass

    def finalize_options(self) -> None:
        pass

    def run(self) -> None:
        criar_info_licencas()


setup(
    name="ROBO-ESOCIAL",
    version="0.0.0",
    options={"build_exe": exe_options},
    cmdclass={"licenses": Licenses},
    license_files=["LICENSE", "LEGAL/"],
    executables=[Executable("installer/entrypoint.py", base=base)],
)
