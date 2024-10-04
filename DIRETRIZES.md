# Diretrizes de Contribuição

Esse documento lista e explica todas as regras que você deve respeitar ao contribuir para este projeto, assim como as ferramentas que utilizamos para analisar o código.

<details>
  <summary>SUMÁRIO</summary>

- [Diretrizes de Contribuição](#diretrizes-de-contribuição)
- [Ferramentas de Análise](#ferramentas-de-análise)
  - [Formatação](#formatação)
  - [Análise de Código](#análise-de-código)
  - [Tipagem](#tipagem)
    - [Erros](#erros)
      - [`Class definition for "Class" depends on itself`](#class-definition-for-class-depends-on-itself)
  - [Editores](#editores)
    - [Visual Studio Code](#visual-studio-code)
- [Regras](#regras)
  - [Documentação](#documentação)
    - [Variáveis](#variáveis)
    - [Funções / Métodos](#funções--métodos)
    - [Classes](#classes)
    - [Referências](#referências)
    - [Código](#código)
    - [Multiplas linhas](#multiplas-linhas)
    - [Outros](#outros)

</details>

# Ferramentas de Análise

## Formatação

O formatador escolhido é o [Black](https://github.com/psf/black), parcialmente pela sua política anti-backslash (`\`) e também por sua habilidade de formatar de acordo com a semântica do código -- ao checar se o código após a formatação é semanticamente igual ao código após a formatação com base na [AST](https://en.wikipedia.org/wiki/Abstract_syntax_tree).

Da documentação do Black:

>Backslashes e strings de multiplas linhas são dois lugares da gramática do Python que quebra indentação importante em multiplas linhas. Você nunca precisa de backslashes. Eles são usados para forçar a gramática à aceitar quebras de linhas que pelo contrário seriam erros de análise da linguagem. Isso os torna confusos de se olhar e sensíveis de se modificar. Isse é o motivo do Black sempre se livrar deles.
>
>Se você está buscando usar backslashes, isso é um sinal claro de que você pode fazer melhor se refatorar seu código ligeiramente.

Esse tipo de conhecimento baseado em boas práticas gerais e específicas do Python, assim como parcialmente adquirido com o passar do tempo através de feedback dos usuários torna o Black a melhor opção no momento. Veja a seção [Code Style](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html) da documentação do Black para mais informações, assim como as nossas configurações específicas em [`pyproject.toml`](./pyproject.toml).

## Análise de Código

A ferramenta principal de análise de código (linter) escolhida é o [Pylint](https://github.com/pylint-dev/pylint), pois, é a mais completa disponível, apenas de ser dolorosamente lenta. Enquanto for viável valorizaremos a segurança sobre a velocidade.

Do GitHub do Pylint:

>O Pylint não é mais inteligente que você: ele pode até te avisar sobre coisas que você fez concientemente ou checar por algumas coisas que você não se importa.

Da mesma forma que o melhor antivírus é o próprio usuário, o melhor analista de código é o próprio programador, mas pessoas diferentes têm prioridades e habitos diferentes, enquanto um programa é capaz de checar uma quantidade arbitrária de casos de maneira igualmente eficiente e completamente inviezada.

Adicionalmente utilizamos o [Bandit](https://github.com/PyCQA/bandit) para identificar coisas no código que possam comprometer a segurança da aplicação ou dos dados com que ela lida.

## Tipagem

Tipos são extremamente importantes e um dos pontos mais fracos de linguagens como o Python. Para contornar isso, utilizamos uma ferramenta para checar e reforçar utilização de tipos e boas práticas relacionadas. Para essa tarefa utilizamos o [Pyright](https://github.com/microsoft/pyright), que, no Visual Studio Code, já vem incluso com a extensão "Pylance", que por sua vez vem incluso com a extensão "Python".

**É de extrema importância e extrema necessidade que você declare tipos em suas variáveis e funções!** Use e abuse do módulo `typing`!

Assim como as outras ferramentas, dê uma olhada no arquivo de configuração e na documentação da ferramenta caso queira ter uma noção do que ela está fazendo com o seu código. **Sugestões de mudança de configuração para essa e outras ferramentas são aceitas**.

### Erros

#### `Class definition for "Class" depends on itself`

De acordo com [essa](https://github.com/microsoft/pyright/issues/4518) issue, esse é um problema que acontece de forma aleatória, infelizmente. Salve o arquivo de novo ou reinicie seu editor.

## Editores

Enquanto não há restrição no editor de código que se pode usar, tentamos uncluir configurações para os editores que a equipe decide utilizar (na medida do possível, é claro). Um desses casos é o fato de que não existem extenssões confiáveis para o `autoflake` e o `pydocstringformatter` para o Visual Studio Code, portanto, pedimos que instale uma extensão para rodar certos comandos ao salvar o arquivo, e através dela disponibilizamos a configuração para rodá-los.

### Visual Studio Code

Para codar esse projeto no vscode, instale as seguintes extensões:

- [EditorConfig](https://marketplace.visualstudio.com/items?itemName=EditorConfig.EditorConfig)
- [Run On Save](https://marketplace.visualstudio.com/items?itemName=emeraldwalk.RunOnSave)
- [Black Formatter](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter)
- [isort](https://marketplace.visualstudio.com/items?itemName=ms-python.isort)
- [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
- [Pylint](https://marketplace.visualstudio.com/items?itemName=ms-python.pylint)

# Regras

## Documentação

Em Python documentação vem na forma de **docstrings**, que são strings com 3 aspas de cada lado (`"""assim"""`). Elas devem ser constituídas de aspas duplas por uma questão de padrão e padronização. O formatador de código vai mudá-las para aspas duplas automaticamente, mas é bom você se adaptar às melhores práticas desde o início.

Docstrings aparecem na primeira linha de uma função, classe ou módulo e descrevem o que fazem, retornam e os erros que podem acontecer.

### Variáveis

Variáveis no meio do código, por padrão, não possuem uma forma de serem documentadas, mas há uma forma de documentá-las presente na ferramenta [Sphinx](https://www.sphinx-doc.org/en/master/index.html), que usamos para gerar documentação sobre o código. Para isso utilize uma docstring imediatamente após a variável, por exemplo:

```python
tempo: int = 1e9
"""Tempo em nanosegundos (1 bilhão == 1 segundo)."""
```

Com esse tipo de documentação breve eliminamos a necessidade de nomes de variáveis longos e que contém palavras abreviadas. Editores provavelmente não vão conseguir identificar esses pedaços de documentação, mas a documentação gerada vai, além de estarem em plena vista para o desenvolvedor que estiver navegando o código. Nada lhe impede de apertar F12 (no caso do vscode) para pular para a definição da variável.

### Funções / Métodos

Documentação de objetos mais complexos, como funções/métodos, seus parâmetros e erros serão feitos com a sintaxe markup do Sphinx, que a este ponto já está virando o padrão da indústria. Aqui você pode ver todas as opções disponíveis, mas mais adiante você verá as vamos utilizar ness projeto.

Aqui estão todas as opções especiais de documentação que utilizaremos nesse projeto:
```python
async def metodo(tempo: int, distancia: float, nome: str) -> set:
    """Calcula quanto tempo uma pessoa leva para percorrer uma dada
    distância e retorna a intercessão de seus melhores tempos.

    :param tempo: Tempo em segundos inteiros
    :param distancia: Distância percorrida em metros
    :param nome: Nome da pessoa que percorreu a distância
    :return: Conjunto oriundo da intercessão citada
    :raises TypeError: Um dos parâmetros for de tipo incorreto
    :raises ValueError: O tempo ou a distância forem menores ou iguais a zero
    """
    ...
```

É de suma importância que os tipos dos parâmetros e retorno sejam especificados em código para que o seu editor lhe dê dicas baseadas neles, também para que a ferramenta de análise de tipos possa saber quais os tipos das variáveis, e por último, para que não seja necessário especificar os tipos dentro da docstring.

Descrição:

- `:param <identificador>:`: Descrição da função do parâmetro.
- `:return:`: Descrição do valor que a função vai retornar.
- `:raise <exception>:`: Tipo do erro e motivo da função dar aquele erro.

### Classes

Classes seguem um padrão similar aos das funções. Os tipos dos parâmetros passados para a classe, que por debaixo dos panos são passados para o método `__init__` são escritos na docstring da própria classe, ao envés da docstring do método.

```python
class Funcionario:
    """Funcionário da empresa.

    :final:
    :param nome: Nome do funcionário
    :param idade: Idade do funcionário
    :param altura: Altura do funcionário
    :raises ValueError: Funcionário não encontrado no banco de dados
    """

    def __init__(self, nome: str, idade: int, altura: float) -> None:
        ...
```

Descrição:

- `:final:`: Classe não pode ser modificada depois de inicializada (esse comportamento deve ser implementado na classe além da documentação).
- `:param <identificador>:`: Descrição da função do parâmetro.
- `:raises <exception>:`: Tipo do erro e motivo da função dar aquele erro.

Note que não há um `:return:` porque o método `__init__` não pode retornar nenhum valor, diferentemente do método `__new__`, que deve retornar uma instância da própria classe, o que nesse caso não é importante.

`raise` nesse caso pode se referir a um erro que ocorre fora do método `__init__`, como por exemplo um método com o decorador `@property`.

```python
class Funcionario:
    @property
    def nome(self) -> str:
        """Nome do funcionário."""
        if self._encontrado:
            return self._nome
        else:
            raise ValueError("Funcionário não encontrado.")
```

### Referências

Por último, o Sphinx nos deixa referênciar nas documentações objetos que serão linkados ná página de documentação gerada. Se eu referênciar uma função da documentação da classe `Funcionario`, na página gerada haverá um link para a documentação daquela função referênciada. As palavras-chaves utilizadas para referência são as seguintes:

```python
"""
    :mod: Módulo
    :func: Função
    :data: Variável definida fora de classes ou funções
    :const: "Variável" constante
    :class: Classe
    :meth: Método
    :attr: Atributo de classe
    :exc: Exception
    :obj: Objeto sem tipo definido
"""
```

O conteúdo dessas referências são o caminho para o objeto no formato de importação envolto em graves ( ` ), como em:

```python
"""
    :class:`caminho.da.Classe`
    :meth:`modulo1.modulo2.Classe.metodo`
    :exc:`modulo_erros.FuncionarioNaoEncontradoError`
    ...
"""
```

### Código

Para adicionar código no meio da documentação envolvemos o texto com duas graves de cada lado ( \``assim`` ), por exemplo:

```python
def soma(a: int, b: int) -> int:
    """Soma dois números inteiros.

    Exemplo: ``soma(40, 53)``
    """
```

Desta forma o texto envolvido em graves será mostrado em formato de código.

### Multiplas linhas

Caso sua descrição seja muito complexo, é possível continuar escrevendo em outra linha se você adicionar um nível de indentação abaixo do descritor (`:param:`, `:raises:`, etc).

```python
def piramide(n: int) -> str:
    """Cria uma pirâmide de asteríscos com um numero de andáres igual ao especificado.

    :param n: Número de andáres que a pirâmide terá, pois,
        pirâmides são conhecidas por serem objetos grandes
        com sistemas complexos de armadilhas dentro de si,
        o que toma muito espaço.
    """
```

### Outros

- [unexport](https://github.com/hakancelikdev/unexport): Organizar importações.
- [autoflake](https://github.com/PyCQA/autoflake): Remove importações e variáveis não utilizadas.
- [docformatter](https://github.com/PyCQA/docformatter): Formatador de docstrings.
