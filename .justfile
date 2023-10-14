set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Excluir o powershell do Windows Defender faz ele inicializar mais rápido:
# https://superuser.com/a/1411591

default: run
alias doc := docs

export PYTHONPATH := `(Get-Item .).FullName` + "src;"

dist_venv := ".venv-dist"
build_venv := ".venv-build"

run:
  #! powershell.exe
  . ./.venv/Scripts/Activate.ps1
  python ./installer/entrypoint.py

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
  Remove-Item -Recurse -ErrorAction:Ignore -Path ./dist,./installer/build,./LEGAL,./LEGAL_dist

make_venv:
  #! powershell.exe
  Remove-Item -Recurse -ErrorAction:Ignore -Path {{dist_venv}},{{build_venv}}
  python -m venv {{dist_venv}}
  python -m venv {{build_venv}}

  . {{dist_venv}}/Scripts/Activate.ps1
  pip install -r dist-requirements.txt

  deactivate

  . {{build_venv}}/Scripts/Activate.ps1
  pip install -r build-requirements.txt

licenses:
  #! powershell.exe
  Remove-Item -Recurse -ErrorAction:Ignore -Path ./LEGAL,./LEGAL_dist
  New-Item -Path . -Name LEGAL_dist -ItemType directory
  New-Item -Path . -Name LEGAL -ItemType directory
  New-Item -Path . -Name LEGAL/compiled -ItemType directory

  $dist_python = (Get-Item ./{{dist_venv}}/Scripts/python.exe).FullName
  $common_args = "--python=$dist_python","--from=mixed","--order=license","--ignore-packages=src"

  . {{build_venv}}/Scripts/Activate.ps1
  pip-licenses @common_args --with-maintainers --with-authors --with-urls --format=markdown --output-file=.\LEGAL\relacao.md
  pip-licenses @common_args --with-maintainers --with-authors --with-urls --format=json --output-file=.\LEGAL\relacao.json
  pip-licenses @common_args --summary --format=markdown --output-file=.\LEGAL\resumo.md
  pip-licenses @common_args --summary --format=json --output-file=.\LEGAL\resumo.json
  pip-licenses @common_args --with-license-file --format=json --output-file=.\LEGAL\info-arquivos.json

  python exe.py licenses

exe: clean
  #! powershell.exe
  . ./{{dist_venv}}/Scripts/Activate.ps1
  python setup.py build
  pip install .
  just licenses
  python exe.py build_exe

build:
  just make_venv
  just exe
