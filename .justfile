set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Excluir o powershell do Windows Defender faz ele inicializar mais rápido:
# https://superuser.com/a/1411591

default: run
alias doc := docs

export PYTHONPATH := `(Get-Item .).FullName` + "src;"

run:
  #! powershell.exe
  . ./.venv/Scripts/Activate.ps1
  python ./src/main.py

docs +FLAGS="":
  #! powershell.exe
  . ./.venv/Scripts/Activate.ps1
  sphinx-autobuild ./docs/sphinx/source ./docs/sphinx/build \
    {{ if FLAGS =~ "-w|--watch" { "--watch src" } else { "" } }} \
    {{ if FLAGS =~ "-o|--open|--open-browser" { "--open-browser" } else { "" } }}

clean_cython:
  #! powershell.exe
  Remove-Item -Recurse -ErrorAction:Ignore -Path ./build,./build_cython

clean: clean_cython
  #! powershell.exe
  Remove-Item -Recurse -ErrorAction:Ignore -Path ./.venv-dist,./dist,./installer/build

build: clean
  #! powershell.exe
  python -m venv .venv-dist
  . ./.venv-dist/Scripts/Activate.ps1
  pip install -r ./dist-requirements.txt
  python setup.py build
  pip install .
  python exe.py build
