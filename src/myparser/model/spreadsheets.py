# CONSTANTS
SP_DESCRIPTION_MAX_TITLE_LENGTH = 40
OUTPUT_DEFAULT_HTML = "default.html"
OUTPUT_REPORT_HTML = "_report.html"

class SP_DESCRIPTION_COLUMNS ():
    # Columns names
    NAME_SP = "descricao.xlsx"
    CODIGO = "codigo"
    NIVEL = "nivel"
    NOME_SIMPLES = "nome_simples"
    NOME_COMPLETO = "nome_completo"
    UNIDADE = "unidade"
    DESC_SIMPLES = "desc_simples"
    DESC_COMPLETA = "desc_completa"
    CENARIO = "cenario"
    RELACAO = "relacao"
    FONTES = "fontes"
    META = "meta"

    # Others constants
    PLURAL_NOMES_SIMPLES = "nomes_simples"
    PLURAL_NOMES_COMPLETOS = "nomes_completos"

class SP_COMPOSITION_COLUMNS ():
    NAME_SP = "composicao.xlsx"
    CODIGO_PAI = "codigo_pai"
    CODIGO_FILHO = "codigo_filho"

class SP_VALUES_COLUMNS ():
    NAME_SP = "valores.xlsx"
    ID = "id"
    NOME = "nome"

class SP_PROPORTIONALITIES_COLUMNS ():
    NAME_SP = "proporcionalidades.xlsx"
    ID = "id"
    NOME = "nome"

class SP_SCENARIO_COLUMNS ():
    NAME_SP = "cenarios.xlsx"
    NOME = "nome"
    DESCRICAO = "descricao"
    SIMBOLO = "simbolo"

class SP_TEMPORAL_REFERENCE_COLUMNS ():
    NAME_SP = "referencia_temporal.xlsx"
    NOME = "nome"
    DESCRICAO = "descricao"
    SIMBOLO = "simbolo"
