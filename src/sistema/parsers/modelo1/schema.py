from __future__ import annotations

from src.sistema.validators import *


schema: dict[str, Validator] = {
    'cod_unid': IntegerString(allow_empty=False, allow_zero=False),
    'cod_rh_unid': IntegerString(allow_empty=False, allow_zero=False),
    'nome_unidade': String(
        allow_empty=False, expect_unicode=True, case_sensitive=False
    ),
    'cod_setor': IntegerString(allow_empty=False, allow_zero=False),
    'cod_rh_setor': IntegerString(allow_empty=False, allow_zero=False),
    'nome_setor': LetterString(
        allow_empty=False, expect_unicode=True, case_sensitive=False
    ),
    'cod_cargo': IntegerString(allow_empty=False, allow_zero=False),
    'cod_rh_cargo': IntegerString(allow_empty=False, allow_zero=False),
    'nome_cargo': String(allow_empty=False, expect_unicode=True, case_sensitive=False),
    'matricula': String(allow_empty=False, case_sensitive=False),
    'cod_funcionario': IntegerString(allow_empty=False, allow_zero=True),
    'nome_funcionario': LetterString(
        allow_empty=False, expect_unicode=True, case_sensitive=False
    ),
    'dt_nascimento': Date(allow_empty=False),
    'sexo': Option(options=['M', 'F'], case_sensitive=False, allow_empty=False),
    'situacao': Option(
        options=['S', 'N', 'P', 'A', 'F'], case_sensitive=False, allow_empty=False
    ),
    'dt_admissao': Date(allow_empty=False),
    'dt_demissao': Date(),
    'estado_civil': Option(options=[str(i + 1) for i in range(8)], allow_empty=False),
    'pis_pasep': String(case_sensitive=False),
    'contratacao': Option(options=[str(i + 1) for i in range(20)], allow_empty=False),
    'rg': String(case_sensitive=False, max_string_length=17),
    'uf_rg': String(
        case_sensitive=False,
        max_string_length=2,
    ),
    'cpf': String(case_sensitive=False, allow_empty=False, max_string_length=16),
    'ctps': String(expect_unicode=True, case_sensitive=False, max_string_length=30),
    'endereco': String(
        expect_unicode=True, case_sensitive=False, max_string_length=110
    ),
    'bairro': String(expect_unicode=True, case_sensitive=False, max_string_length=80),
    'cidade': String(expect_unicode=True, case_sensitive=False, max_string_length=50),
    'uf': String(expect_unicode=True, case_sensitive=False, max_string_length=2),
    'cep': String(expect_unicode=True, case_sensitive=False, max_string_length=9),
    'tel': String(expect_unicode=True, case_sensitive=False, max_string_length=20),
    'naturalidade': String(
        expect_unicode=True, case_sensitive=False, max_string_length=50
    ),
    'cor': Option(options=[str(i + 1) for i in range(6)]),
    'email': String(max_string_length=400, case_sensitive=False, expect_unicode=True),
    'deficiencia': String(max_string_length=750, expect_unicode=True),
    'cbo': String(max_string_length=10, case_sensitive=False),
    'gfip': String(max_string_length=2),
    'endereco_unidade': String(
        allow_empty=False,
        case_sensitive=False,
        expect_unicode=True,
        max_string_length=110,
    ),
    'bairro_unidade': String(
        allow_empty=False,
        case_sensitive=False,
        expect_unicode=True,
        max_string_length=80,
    ),
    'cidade_unidade': String(
        allow_empty=False,
        case_sensitive=False,
        expect_unicode=True,
        max_string_length=50,
    ),
    'estado_unidade': String(
        allow_empty=False,
        case_sensitive=False,
        expect_unicode=True,
        max_string_length=2,
    ),
    'cep_unidade': String(
        allow_empty=False,
        case_sensitive=False,
        expect_unicode=True,
        max_string_length=9,
    ),
    'cnpj_unidade': String(
        allow_empty=False,
        case_sensitive=False,
        expect_unicode=True,
        max_string_length=14,
    ),
    'inscricao_unidade': String(
        allow_empty=False,
        case_sensitive=False,
        expect_unicode=True,
        max_string_length=20,
    ),
    'tel1_unidade': String(
        allow_empty=False,
        case_sensitive=False,
        expect_unicode=True,
        max_string_length=15,
    ),
    'tel2_unidade': String(
        case_sensitive=False, expect_unicode=True, max_string_length=15
    ),
    'tel3_unidade': String(
        case_sensitive=False, expect_unicode=True, max_string_length=15
    ),
    'tel4_unidade': String(
        case_sensitive=False, expect_unicode=True, max_string_length=15
    ),
    'contato_unidade': String(
        allow_empty=False,
        case_sensitive=False,
        expect_unicode=True,
        max_string_length=150,
    ),
    'cnae': LetterString(
        case_sensitive=False, expect_unicode=True, max_string_length=150
    ),
    'numero_end_funcionario': String(max_string_length=20, allow_empty=False),
    'complemento_end_funcionario': String(
        case_sensitive=False, expect_unicode=True, max_string_length=300
    ),
    'razao_social_da_unidade': String(
        max_string_length=200,
        case_sensitive=False,
        expect_unicode=True,
        allow_empty=False,
    ),
    'nome_da_mae_do_funcionario': String(
        max_string_length=200, expect_unicode=True, case_sensitive=False
    ),
    'cod_centro_custo': String(
        max_string_length=40, expect_unicode=True, case_sensitive=False
    ),
    'cod_rh_centro_custo': String(
        max_string_length=40, expect_unicode=True, case_sensitive=False
    ),
    'dt_ultima_movimentacao': Date(),
    'cod_unidade_contratante': String(max_string_length=8, case_sensitive=False),
    'razao_social': String(
        max_string_length=200, expect_unicode=True, case_sensitive=False
    ),
    'cnpj': String(max_string_length=14, case_sensitive=False),
    'turno': String(max_string_length=8, case_sensitive=False, expect_unicode=True),
    'dt_emissao_ctps': Date(),
    'serie_ctps': String(max_string_length=25, case_sensitive=False),
    'cnae_2_0': String(max_string_length=10),
    'cnae_livre': String(),
    'descricao_cnae_livre': String(),
    'cei': String(),
    'funcao': String(),
    'cnae_7': String(),
    'tipo_de_cnae_utilizado': String(),
    'descricao_detalhada_do_cargo': String(),
    'no_endereco_unidade': String(),
    'complemento_endereco_unidade': String(),
    'regime_de_revezamento': String(),
    'campo_livre_1': String(),
    'campo_livre_2': String(),
    'campo_livre_3': String(),
    'telefone_sms': String(),
    'grau_de_risco': String(),
    'uf_ctps': String(),
    'nome_centro_custo': String(),
    'autoriza_sms': String(),
    'endereco_cobranca_unidade': String(),
    'numero_endereco_cobranca_unidade': String(),
    'bairro_cobranca_unidade': String(),
    'cidade_cobranca_unidade': String(),
    'estado_cobranca_unidade': String(),
    'cep_cobranca_unidade': String(),
    'complemento_endereco_cobranca_unidade': String(),
    'remuneracao_mensal_rs': String(),
    'telefone_comercial': String(),
    'telefone_celular': String(),
    'data_emissao_do_rg': String(),
    'codigo_do_pais_de_nascimento': String(),
    'origem_descricao_detalhada': String(),
    'unidade_contratante': String(),
    'escolaridade': String(),
    'categoria_esocial': String(),
    'matricula_rh': String(),
    'genero': String(),
    'nome_social': String(),
    'tipo_de_admissao': String(),
    'grau_de_instrucao': String(),
    'nome_do_pai': String(),
    'tipo_de_vinculo': String(),
    'nome_do_turno': String(),
    'campo_livre_4': String(),
    'cpf_unidade': String(),
    'caepf_unidade': String(),
    'tipo_sanguineo': String(),
    'data_inicio_periodo_aquisitivo': String(),
    'data_fim_periodo_aquisitivo': String(),
    'cno_unidade': String(),
    'desconsiderar_para_o_esocial': String(),
    'dt_validade_rg': String(),
    'desconsiderar_unidade_para_o_esocial': String(),
}
