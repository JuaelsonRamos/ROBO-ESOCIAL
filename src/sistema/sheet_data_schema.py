from __future__ import annotations

from src.exc import SheetCell, SheetParsing, ValidatorException
from src.sistema.validator import (
    IntegerString,
    LetterString,
    Option,
    String,
    UTCDate,
    Validator,
    cell_value_to_string,
)

import string

from typing import Never

from openpyxl.cell.cell import Cell
from unidecode import unidecode_expect_nonascii as unidecode


class SheetModel:
    @classmethod
    def model_code_from_cell(cls, cell: Cell) -> int | Never:
        try:
            cell_value = cell_value_to_string(cell.value)
        except ValidatorException.RuntimeError as err:
            raise SheetParsing.TypeError(err) from err
        cell_value = unidecode(cell_value).strip(string.whitespace).lower()
        if cell_value == '':
            empty_base_err = SheetCell.ValueError(
                'cell containing sheet model description is empty'
            )
            raise SheetParsing.EmptyString(empty_base_err) from empty_base_err
        model_spec: tuple[str, ...] = tuple(cell_value.split(' '))
        if len(model_spec) != 2:
            raise SheetParsing.ValueError(f'cannot infer model code by {cell_value=}')
        match model_spec:
            case ('modelo', '1'):
                return 1
            case ('modelo', '2'):
                return 2
        raise SheetParsing.ValueError(
            f"canont infer worksheet's model by cell {cell.coordinate=}"
        )

    @classmethod
    def model_name_from_cell(cls, cell: Cell) -> str:
        code = cls.model_code_from_cell(cell)
        return 'Modelo 1' if code == 1 else 'Modelo 2'


class _ModeloSchemaBase:
    _schema: tuple[Validator, ...] | None = None
    _unique_titles: frozenset[str] | None = None

    @classmethod
    def get_schema(cls) -> tuple[Validator, ...]:
        if cls._schema is None:
            raise RuntimeError('sheet model not yet loaded')
        return cls._schema

    @classmethod
    def get_unique_titles(cls) -> frozenset[str]:
        if cls._unique_titles is None:
            titles = []
            for validator in cls.get_schema():
                titles.extend(validator.known_titles)
            cls._unique_titles = frozenset(titles)
        return cls._unique_titles

    @classmethod
    def is_loaded(cls) -> bool:
        return cls._schema is not None

    @classmethod
    def lazy_load_schema(cls):
        if cls._schema is not None:
            return


class Modelo1Schema(_ModeloSchemaBase):
    @classmethod
    def lazy_load_schema(cls):
        if cls._schema is not None:
            return
        cls._schema = (
            IntegerString.new(
                ('Cód RH da Unid.', 'Cod.Unid', 'Cód Unid.'), allow_empty=False
            ),
            String.new(('Nome Unidade',), allow_empty=False),
            IntegerString.new(
                ('Cód. Setor', 'Cód. RH Setor', 'Cod.Setor'), allow_empty=False
            ),
            LetterString.new(('Nome Setor',), allow_empty=False),
            IntegerString.new(
                ('Cod.Cargo', 'Cód. Cargo', 'Cód. RH Cargo'), allow_empty=False
            ),
            String.new(('Nome Cargo',), allow_empty=False),
            String.new(('Matrícula',), allow_empty=False),
            IntegerString.new(
                ('Cód. Funcionário', 'Cod Funcionário'), allow_empty=False
            ),
            LetterString.new(
                ('Nome Funcionário',), allow_empty=False, allow_punctuation=False
            ),
            UTCDate.new(('Dt. Nascimento', 'Dt.Nascimento'), allow_empty=False),
            Option.new(('Sexo',), ('M', 'F')),
            Option.new(('Situação',), ('N', 'S', 'P')),
            UTCDate.new(('Dt.Admissão', 'Dt. Admissão'), allow_empty=False),
            UTCDate.new(('Dt. Demissão', 'Dt.Demissão')),
            IntegerString.new(('Estado Civil',)),
            String.new(('Pis/Pasep',)),
            IntegerString.new(('Contratação',)),
            String.new(('Rg', 'RG'), allow_letters=False, allow_whitespace=False),
            String.new(('UF- RG', 'UF-RG')),
            String.new(('CPF',), allow_whitespace=False, allow_letters=False),
            IntegerString.new(('CTPS',)),
            String.new(('Endereço',)),
            String.new(('Bairro',)),
            String.new(('Cidade',)),
            # TODO: Actually study the correct validators for all the ones bellow:
            String.new(('UF',)),
            String.new(('Cep',)),
            String.new(('Tel',)),
            String.new(('Naturalidade',)),
            String.new(('Cor',)),
            String.new(('E-mail',)),
            String.new(('Deficiencia', 'Deficiência')),
            String.new(('CBO',)),
            String.new(('GFIP',)),
            String.new(('Endereço Unidade',)),
            String.new(('Bairro Unidade',)),
            String.new(('Cidade Unidade',)),
            String.new(('Estado Unidade',)),
            String.new(('Cep Unidade',)),
            String.new(('CNPJ Unidade',)),
            String.new(('Inscrição Unidade',)),
            String.new(('Tel1 Unidade',)),
            String.new(('Tel2 Unidade',)),
            String.new(('Tel3 Unidade',)),
            String.new(('Tel4 Unidade',)),
            String.new(('Contato Unidade', 'Contato Unid')),
            String.new(('Cnae',)),
            String.new(('Número Endereço Funcionário', 'Número End. Funcionário')),
            String.new(
                ('Complemento Endereço Funcionário', 'Complemento End. Funcionário')
            ),
            String.new(('Razão Social da Unidade', 'Razão Social Unid.')),
            String.new(('Nome da Mae do Funcionário', 'Nome da Mãe do Funcionário')),
            String.new(
                ('Cód RH Centro Custo.', 'Cod. Centro Custo', 'Cód Centro Custo')
            ),
            String.new(('Dt. Ultima Movimentação', 'Dt. Última Movimentação')),
            String.new(('Cód. Unidade Contratante', 'Cod. Unidade contratante')),
            String.new(('Razão Social',)),
            String.new(('CNPJ',)),
            String.new(('Turno',)),
            String.new(('Dt. Emissão CTPS', 'Dt.Emissão.Cart.Prof')),
            String.new(('Série CTPS',)),
            String.new(('CNAE 2.0',)),
            String.new(('CNAE Livre',)),
            String.new(('Descrição CNAE Livre',)),
            String.new(('CEI',)),
            String.new(('Função',)),
            String.new(('CNAE 7',)),
            String.new(('Tipo de CNAE Utilizado',)),
            String.new(('Descr. Detalhada Cargo', 'Descrição Detalhada do Cargo')),
            String.new(('Nº endereço Unidade', 'Nr Endereço Unidade')),
            String.new(
                ('Complemento Endereço Unidade', 'Complemento endereço Unidade')
            ),
            String.new(('Regime Revezamento', 'Regime de Revezamento')),
            String.new(('Órgão expedidor do RG', 'Campo Livre 1')),
            String.new(('Campo Livre 1', 'Livre1')),
            String.new(('Campo Livre 2', 'Livre2')),
            String.new(('Livre3', 'Campo Livre 3')),
            String.new(('Telefone SMS',)),
            String.new(('Grau de Risco',)),
            String.new(('UF CTPS',)),
            String.new(('Nome Centro Custo',)),
            String.new(('Autoriza SMS',)),
            String.new(('Endereço Cobrança Unidade',)),
            String.new(('Número Endereço Cobrança Unidade',)),
            String.new(('Bairro Cobrança Unidade',)),
            String.new(('Cidade Cobrança Unidade',)),
            String.new(('Estado Cobrança Unidade',)),
            String.new(('Cep Cobrança Unidade',)),
            String.new(('Complemento Endereço Cobrança Unidade',)),
            String.new(('Remuneração Mensal (R$)', 'Remuneração Mensal')),
            String.new(('Telefone Comercial',)),
            String.new(('Telefone Celular',)),
            String.new(('Data Emissão do RG',)),
            String.new(
                ('Código do País de Nascimento', 'Código do país de Nascimento')
            ),
            String.new(('Origem Descrição Detalhada',)),
            String.new(('Unidade Contratante',)),
            String.new(('Escolaridade',)),
            String.new(('Categoria (eSocial)', 'Código Categoria (eSocial)')),
            String.new(('Matrícula RH',)),
            String.new(('Gênero',)),
            String.new(('Nome Social',)),
            String.new(('Tipo de Admissão',)),
            String.new(('Grau de Instrução',)),
            String.new(('Nome do Pai', 'Nome do Pai do Funcionário')),
            String.new(('Tipo de Vínculo',)),
            String.new(('Nome do Turno',)),
            String.new(('Texto Livre', 'Campo livre 4')),
            String.new(('CPF Unidade',)),
            String.new(('CAEPF Unidade',)),
            String.new(('Tipo Sanguíneo',)),
            String.new(
                ('Dt. Inicio Periodo Aquisitivo', 'Data Inicio Periodo Aquisitivo')
            ),
            String.new(('Data Fim Periodo Aquisitivo', 'Dt. Fim Periodo Aquisitivo')),
            String.new(('CNO Unidade',)),
            String.new(('Desconsiderar para o eSocial',)),
            String.new(('Dt. Validade RG',)),
            String.new(('Desconsiderar Unidade para o eSocial',)),
        )


class Modelo2Schema(_ModeloSchemaBase):
    @classmethod
    def lazy_load_schema(cls):
        if cls._schema is not None:
            return
        cls._schema = ()
