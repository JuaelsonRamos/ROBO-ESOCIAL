<h1 align="center">CONTRIBUIÇÕES</h1>

## Requisitos

- [Python 3.11](https://www.python.org/downloads/release/python-3119/)
- [NodeJS LTS](https://nodejs.org/) (para ferramentas como [prettier](https://prettier.io/))
- [Git](https://git-scm.com/downloads/win)
- [VSCode](https://code.visualstudio.com/Download) (para ferramentas como [Tasks](https://code.visualstudio.com/docs/editor/tasks) e [normalização de configurações](https://code.visualstudio.com/docs/editor/profiles))

## Configurando Ambiente

Após clonar o repositório, a primeira coisa a se fazer é criar um ambiente virtual:

```powershell
python -m venv .venv
```

Importe as configurações do shell do seu ambiente virtual:

```powershell
. ./.venv/Scripts/Activate.ps1 # Powershell
```

Depois, instalar todas as dependências Python:

```powershell
python -m pip install -U pip
pip install -r requirements.txt
```

E as dependências Node:

```powershell
npm install
```

## Configurando o Visual Studio Code

No Visual Studio Code:

1. Clique no ícone de configurações ![ícone configurações vscode](./docs/assets/gear.svg)
2. Clique em Profiles (Perfís)
3. Importe o perfil [`.vscode/robo-esocial.code-profile`](.vscode/robo-esocial.code-profile)

Em versões mais antigas do VSCode, você poderá ser questionado sobre baixar as extensões listadas no perfil, caso aconteça, concorde em baixá-las.

Após instaladas, você pode instalar outras extensões e adicionar (não sobrescrever existentes) opções de configuração. Essas modificações serão salvas localmente.

Você pode importar este perfil e duplicá-lo para criar variantes pessoais baseadas neles.

> [!NOTE]
> Erros não esperados podem ocorrer com a modificação do perfil oficial do VSCode. Entre com contato para ajuda.
>
> Estes erros não são de responsabilidade da gerência do projeto devido ao fato de não serem configurações oficiais. É recomendado reinstalar o perfil oficial para ajudar com o processo **pessoal** de resolução deste problema.

> [!CAUTION]
> Modificações neste perfil (configurações/extensões) que editam o código **não são permitidas**.
>
> A valorização da consistência de aparência e convenções do código é muito importante!
>
> Entre em contato caso acredite que sua modificação deva ser considerada.
