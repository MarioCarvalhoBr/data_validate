
# Data Validate
## Sistema de validação e processamento de planilhas para a plataforma AdaptaBrasil

<div align="center">


|                 |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Testing Linux   | [![Linux Build](https://github.com/MarioCarvalhoBr/data_validate/actions/workflows/linux-ci-build-ubuntu-24-04.yml/badge.svg)](https://github.com/MarioCarvalhoBr/data_validate/actions/workflows/linux-ci-build-ubuntu-24-04.yml) [![Linux Lint](https://github.com/MarioCarvalhoBr/data_validate/actions/workflows/linux-lint-ubuntu-24-04.yml/badge.svg)](https://github.com/MarioCarvalhoBr/data_validate/actions/workflows/linux-lint-ubuntu-24-04.yml) [![Linux Unit Tests](https://github.com/MarioCarvalhoBr/data_validate/actions/workflows/linux-unit-tests-ubuntu-24-04.yml/badge.svg)](https://github.com/MarioCarvalhoBr/data_validate/actions/workflows/linux-unit-tests-ubuntu-24-04.yml) |
| Testing Windows | [![Windows Build](https://github.com/MarioCarvalhoBr/data_validate/actions/workflows/windows-ci-build-windows-2022.yml/badge.svg)](https://github.com/MarioCarvalhoBr/data_validate/actions/workflows/windows-ci-build-windows-2022.yml) [![Windows Unit Tests](https://github.com/MarioCarvalhoBr/data_validate/actions/workflows/windows-unit-tests-windows-2022.yml/badge.svg)](https://github.com/MarioCarvalhoBr/data_validate/actions/workflows/windows-unit-tests-windows-2022.yml)                                                                                                                                                                               |
| Coverage        | ![Coverage Status](https://raw.githubusercontent.com/MarioCarvalhoBr/data_validate/refs/heads/main/assets/coverage/coverage_badge.svg) ![Tests Status](https://raw.githubusercontent.com/MarioCarvalhoBr/data_validate/refs/heads/main/assets/coverage/tests_badge.svg)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Package         | ![Last Commit](https://img.shields.io/github/last-commit/MarioCarvalhoBr/data_validate?style=flat&logo=git&logoColor=white&color=0080ff) ![Top Language](https://img.shields.io/github/languages/top/MarioCarvalhoBr/data_validate?style=flat&color=0080ff) ![Language Count](https://img.shields.io/github/languages/count/MarioCarvalhoBr/data_validate?style=flat&color=0080ff)                                                                                                                                                                                                                                                                       |
| Meta            | ![Version](https://img.shields.io/badge/version-0.7.65b683.dev10-orange.svg) [![License - MIT](https://img.shields.io/github/license/MarioCarvalhoBr/data_validate)](https://img.shields.io/github/license/MarioCarvalhoBr/data_validate)                                                                                                                                                                                                                                                                                                                                                                                                |

<p><em>Built with the tools and technologies:</em></p>

<img alt="Markdown" src="https://img.shields.io/badge/Markdown-000000.svg?style=flat&amp;logo=Markdown&amp;logoColor=white" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="TOML" src="https://img.shields.io/badge/TOML-9C4121.svg?style=flat&amp;logo=TOML&amp;logoColor=white" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="precommit" src="https://img.shields.io/badge/precommit-FAB040.svg?style=flat&amp;logo=pre-commit&amp;logoColor=black" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="Babel" src="https://img.shields.io/badge/Babel-F9DC3E.svg?style=flat&amp;logo=Babel&amp;logoColor=black" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="Ruff" src="https://img.shields.io/badge/Ruff-D7FF64.svg?style=flat&amp;logo=Ruff&amp;logoColor=black" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="GNU%20Bash" src="https://img.shields.io/badge/GNU%20Bash-4EAA25.svg?style=flat&amp;logo=GNU-Bash&amp;logoColor=white" class="inline-block mx-1" style="margin: 0px 2px;">
<br>
<img alt="Pytest" src="https://img.shields.io/badge/Pytest-0A9EDC.svg?style=flat&amp;logo=Pytest&amp;logoColor=white" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="Python" src="https://img.shields.io/badge/Python-3776AB.svg?style=flat&amp;logo=Python&amp;logoColor=white" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="GitHub%20Actions" src="https://img.shields.io/badge/GitHub%20Actions-2088FF.svg?style=flat&amp;logo=GitHub-Actions&amp;logoColor=white" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="Poetry" src="https://img.shields.io/badge/Poetry-60A5FA.svg?style=flat&amp;logo=Poetry&amp;logoColor=white" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="pandas" src="https://img.shields.io/badge/pandas-150458.svg?style=flat&amp;logo=pandas&amp;logoColor=white" class="inline-block mx-1" style="margin: 0px 2px;">
</div>

**Data Validate** é um validador e processador de planilhas robusto e multilíngue, desenvolvido especificamente para automatizar a checagem de integridade e estrutura de arquivos de dados da plataforma AdaptaBrasil. É especialmente útil para projetos que exigem padronização e validação rigorosa de dados tabulares, como pesquisas científicas, bancos de dados ambientais e sistemas de indicadores.

## 📋 Índice

- [Características](#-características)
- [Arquitetura](#-arquitetura)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [Validações Implementadas](#-validações-implementadas)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Testes](#-testes)
- [Desenvolvimento](#-desenvolvimento)
- [Documentação](#-documentação)
- [Contribuição](#-contribuição)
- [Licença](#-licença)

## 🚀 Características e protocolo de validação

### Protocolo de Validação
O Data Validate implementa a especificação detalhada no protocolo de validação [versão 1.13](assets/protocolo-1.13.pdf), que define regras claras para a estrutura e conteúdo das planilhas utilizadas na plataforma AdaptaBrasil.

### Principais Funcionalidades

- **Validação Estrutural**: Verifica estrutura de planilhas, nomes de colunas e organização
- **Validação de Conteúdo**: Aplica regras de negócio específicas para cada tipo de planilha
- **Verificação Ortográfica**: Sistema multilíngue de correção ortográfica com dicionários personalizados
- **Validação Hierárquica**: Verifica relações entre indicadores e estruturas em árvore
- **Relatórios Detalhados**: Gera relatórios HTML, PDF e logs detalhados de validação
- **Suporte Multilíngue**: Suporte a internacionalização em português e inglês
- **Sistema de Logs**: Logging detalhado para auditoria e debugging

### Tecnologias Utilizadas

- **Python 3.12+**: Linguagem principal
- **Pandas**: Manipulação e análise de dados
- **PyEnchant**: Verificação ortográfica
- **Calamine**: Leitura de arquivos Excel
- **Babel**: Internacionalização
- **PDFKit**: Geração de relatórios PDF
- **Poetry**: Gerenciamento de dependências

## 🏗️ Arquitetura

O projeto segue uma arquitetura modular baseada em padrões de design limpos:

```
📁 data_validate/
├── 🎛️ controllers/     # Orquestração e controle de fluxo
├── 📊 models/          # Modelos de dados para planilhas
├── ✅ validators/      # Lógica de validação
├── 🛠️ helpers/        # Utilitários e funções auxiliares
├── ⚙️ config/         # Configurações globais
├── 🔧 middleware/     # Camada de inicialização
└── 📄 static/         # Recursos estáticos (templates, dicionários)
```

### Fluxo de Processamento

1. **Inicialização**: Bootstrap configura ambiente e dependências
2. **Carregamento**: Leitura e pré-processamento de planilhas
3. **Validação**: Execução sequencial de validadores especializados
4. **Agregação**: Coleta e organização de erros e avisos
5. **Relatório**: Geração de relatórios detalhados de saída

## 📦 Instalação

### Pré-requisitos

- Python 3.12 ou superior
- Poetry para gerenciamento de dependências
- Wkhtmltopdf (para geração de PDFs)

### Instalação de Dependências de Sistema
##### GNU/LINUX
Certifique-se de que `python-dev` e `wkhtmltopdf` estejam instalados,

```shell
    # Instalando as dependências
    sudo apt install python3-dev wkhtmltopdf
```
##### Windows
Para instalar o `wkhtmltopdf`, baixe o instalador do site oficial: https://wkhtmltopdf.org/downloads.html
Ou usando o `chocolatey`:
```shell
    choco install -y wkhtmltopdf
```

### Instalação via PyPI

#### Crie um ambiente virtual (opcional, mas recomendado)
```bash
#  1.0 Crie e ative um ambiente virtual (opcional, mas recomendado)
python -m venv .venv

# 1.0 Ative o ambiente virtual
source .venv/bin/activate # No Linux/MacOS
.venv\Scripts\activate # No Windows
```

#### Instale o pacote via pip
```bash
pip install canoa-data-validate
```

#### Exemplo de uso após instalação via PyPI
```bash
canoa-data-validate --input_folder data/input --output_folder data/output --locale pt_BR --debug
```

### Instalação via repositório GitHub

```bash
# 1.1 Clone o repositório
git clone https://github.com/MarioCarvalhoBr/data_validate.git
cd data_validate

#  1.2 Crie e ative um ambiente virtual (opcional, mas recomendado)
python -m venv .venv

# 1.3 Ative o ambiente virtual
source .venv/bin/activate # No Linux/MacOS
.venv\Scripts\activate # No Windows

# 2. Instale o Poetry (se necessário)
pip install poetry

# 3. Instale as dependências
poetry install

# 4. Ative o ambiente virtual
eval $(poetry env activate)
```

#### Comando completo
```bash
python -m data_validate.main
    --input_folder data/input
    --output_folder data/output
    --locale pt_BR
    --debug
```

#### Comando abreviado
```bash
python -m data_validate.main --i data/input --o data/output --l pt_BR --d
```

### Script de Pipeline

```bash
# Execução completa do pipeline
bash scripts/run_main_pipeline.sh
```

### Modos de Execução

#### Modo Desenvolvimento (Recomendado)
```bash
# Com debug ativo e logs detalhados
python -m data_validate.main --input_folder data/input --debug
```

#### Modo Produção
```bash
# Sem logs, sem tempo, sem versão no relatório
python -m data_validate.main
    --input_folder data/input
    --output_folder data/output
    --no-time
    --no-version
```

#### Modo Rápido (sem verificação ortográfica e tamanhos de títulos)
```bash
# Para execuções rápidas, pulando spell check e avisos de comprimento de títulos
python -m data_validate.main
    --input_folder data/input
    --no-spellchecker
    --no-warning-titles-length
```

### Parâmetros de Linha de Comando

#### Argumentos Principais

| Parâmetro | Abreviação | Tipo | Descrição | Padrão | Obrigatório |
|-----------|------------|------|-----------|--------|-------------|
| `--input_folder` | `--i` | str | Caminho para a pasta de entrada com planilhas | - | ✅ |
| `--output_folder` | `--o` | str | Caminho para a pasta de saída dos relatórios | `output_data/` | ❌ |
| `--locale` | `-l` | str | Idioma da interface (pt_BR ou en_US) | `pt_BR` | ❌ |

#### Argumentos de Ação

| Parâmetro | Abreviação | Tipo | Descrição | Padrão |
|-----------|------------|------|-----------|--------|
| `--debug` | `--d` | flag | Ativa modo debug com logs detalhados | `False` |
| `--no-time` | | flag | Oculta informações de tempo de execução | `False` |
| `--no-version` | | flag | Oculta versão do script no relatório final | `False` |
| `--no-spellchecker` | | flag | Desativa verificação ortográfica | `False` |
| `--no-warning-titles-length` | | flag | Desativa avisos de comprimento de títulos | `False` |

#### Argumentos de Relatório (Opcionais)

| Parâmetro | Tipo | Descrição | Padrão |
|-----------|------|-----------|--------|
| `--sector` | str | Nome do setor estratégico para o relatório | `None` |
| `--protocol` | str | Nome do protocolo para o relatório | `None` |
| `--user` | str | Nome do usuário para o relatório | `None` |
| `--file` | str | Nome específico do arquivo a ser analisado | `None` |

### Estrutura de Dados

#### Entrada (`data/input/`)
Coloque suas planilhas Excel (.xlsx) na pasta de entrada. O sistema processa:

- **sp_description.xlsx**: Descrições e metadados dos indicadores
- **sp_value.xlsx**: Valores dos indicadores
- **sp_scenario.xlsx**: Cenários de análise
- **sp_temporal_reference.xlsx**: Referências temporais
- **sp_composition.xlsx**: Composições hierárquicas
- **sp_proportionality.xlsx**: Proporções e relacionamentos
- **sp_legend.xlsx**: Legendas e categorias
- **sp_dictionary.xlsx**: Dicionários e vocabulários

#### Saída (`data/output/`)
O sistema gera:

- **Relatórios HTML**: Visualização interativa dos resultados
- **Relatórios PDF**: Geração de relatórios em formato PDF
- **Logs detalhados**: Registros de execução e erros

## ✅ Validações Implementadas

### Validação Estrutural
- ✅ Verificação de existência de arquivos obrigatórios
- ✅ Validação de nomes e ordem de colunas
- ✅ Checagem de tipos de dados esperados

### Validação de Conteúdo
- ✅ **Códigos sequenciais**: Verificação de sequência numérica (1, 2, 3...)
- ✅ **Valores únicos**: Detecção de duplicatas em campos chave
- ✅ **Relacionamentos**: Validação de integridade referencial entre planilhas
- ✅ **Níveis hierárquicos**: Verificação de estruturas em árvore
- ✅ **Cenários e temporalidade**: Validação de combinações válidas

### Validação de Formato
- ✅ **Capitalização**: Padronização de texto mantendo acrônimos
- ✅ **Pontuação**: Verificação de regras de pontuação específicas
- ✅ **Caracteres especiais**: Detecção de CR/LF e caracteres inválidos
- ✅ **Comprimento de texto**: Validação de limites de caracteres
- ✅ **HTML**: Detecção de tags HTML não permitidas

### Validação Ortográfica
- ✅ **Múltiplos idiomas**: Suporte a pt_BR e en_US
- ✅ **Dicionários personalizados**: Termos técnicos e específicos do domínio
- ✅ **Sugestões de correção**: Recomendações automáticas

### Validação de Dados
- ✅ **Valores numéricos**: Verificação de tipos e intervalos
- ✅ **Casas decimais**: Validação de precisão numérica
- ✅ **Dados obrigatórios**: Verificação de campos não vazios
- ✅ **Combinações válidas**: Validação de relacionamentos entre dados

## 📁 Estrutura do Projeto

```
data_validate/
├── 📊 assets/                    # Badges e recursos visuais
├── 📁 data/                      # Dados de entrada e saída
│   ├── input/                    # Planilhas para validação
│   └── output/                   # Relatórios e logs gerados
├── 🐍 data_validate/             # Código-fonte principal
│   ├── config/                   # Configurações globais
│   ├── controllers/              # Orquestração e controle
│   │   ├── context/              # Contextos de dados
│   │   └── report/               # Geração de relatórios
│   ├── helpers/                  # Utilitários e funções auxiliares
│   │   ├── base/                 # Classes base
│   │   ├── common/               # Funções comuns
│   │   └── tools/                # Ferramentas especializadas
│   ├── middleware/               # Inicialização e bootstrap
│   ├── models/                   # Modelos de dados das planilhas
│   ├── static/                   # Recursos estáticos
│   │   ├── dictionaries/         # Dicionários ortográficos
│   │   ├── locales/              # Arquivos de tradução
│   │   └── report/               # Templates de relatórios
│   └── validators/               # Validadores especializados
│       ├── hierarchy/            # Validação hierárquica
│       ├── spell/                # Verificação ortográfica
│       ├── spreadsheets/         # Validação de planilhas
│       └── structure/            # Validação estrutural
├── 📝 docs/                      # Documentação gerada
├── 🧪 tests/                     # Testes unitários
├── 📋 scripts/                   # Scripts de automação
└── ⚙️ Configuração               # Arquivos de configuração
    ├── pyproject.toml
    ├── pytest.ini
    ├── Makefile
    └── .coveragerc
```

## 🧪 Testes

O projeto utiliza pytest para testes unitários com cobertura completa.

### Comandos de Teste

```bash
# Execultar tudo
make all-cov

# Executar todos os testes
make test

# Testes com cobertura
make test-cov

# Testes rápidos (para em erro)
make test-fast

# Gerar relatório HTML de cobertura
make html-report

# Ver todos os comandos disponíveis
make help
```

### Métricas de Cobertura

- **Cobertura atual**: 8.10% (em desenvolvimento)
- **Threshold mínimo**: 4%
- **Módulos com 100% de cobertura**: Formatação de texto e números

### Executar Testes Específicos

```bash
# Testar módulos específicos
python -m pytest tests/unit/helpers/common/generation/ -v
python -m pytest tests/unit/helpers/common/formatting/ -v
```

## 🛠️ Desenvolvimento

### Configuração do Ambiente de Desenvolvimento

```bash
# Instalar dependências de desenvolvimento
poetry install --with dev

# Configurar pre-commit hooks
pre-commit install

# Formatação de código black
make black

# Formatação de código ruff
ruff check . --fix
```

### Comandos Make Disponíveis

| Comando | Descrição |
|---------|-----------|
| `make all-cov` | Executa testes com cobertura completa |
| `make test` | Executa todos os testes |
| `make test-cov` | Testes com relatório de cobertura |
| `make test-fast` | Testes rápidos (para no primeiro erro) |
| `make coverage` | Gera apenas relatório de cobertura |
| `make html-report` | Relatório HTML de cobertura |
| `make clean` | Remove arquivos temporários |
| `make black` | Formata código com Black |
| `make make-badge` | Gera badges de cobertura e testes |
| `make help` | Mostra todos os comandos |

### Estrutura de Testes

```
tests/
└── unit/
    └── helpers/
        └── common/
            ├── formatting/           # Testes de formatação
            ├── generation/           # Testes de geração
            ├── processing/           # Testes de processamento
            └── validation/           # Testes de validação
```

## 📚 Documentação

### Gerar Documentação

```bash
# Gerar documentação com pdoc
pdoc ./data_validate/ -o ./docs --logo "https://avatars.githubusercontent.com/u/141270342?s=400&v=4"
```

### Documentos Disponíveis

- **[HOW_IT_WORKS.md](../../../HOW_IT_WORKS.md)**: Arquitetura detalhada do sistema
- **[TESTING.md](../../../TESTING.md)**: Guia completo de testes e cobertura
- **[CODE_OF_CONDUCT.md](../../../CODE_OF_CONDUCT.md)**: Diretrizes de desenvolvimento
- **[CHANGELOG.md](../../../CHANGELOG.md)**: Histórico de versões

## 🔧 Dependências Principais

### Produção
- **pandas** (>=2.2.3): Manipulação de dados
- **chardet** (>=5.2.0): Detecção de encoding
- **calamine** (>=0.5.3): Leitura de arquivos Excel
- **pyenchant** (>=3.2.2): Verificação ortográfica
- **pdfkit** (>=1.0.0): Geração de PDFs
- **babel** (>=2.17.0): Internacionalização

### Desenvolvimento
- **pytest** (^8.4.1): Framework de testes
- **coverage** (^7.10.6): Cobertura de código
- **ruff** (^0.12.11): Linting rápido
- **black** (^25.1.0): Formatação de código
- **pre-commit** (^4.3.0): Hooks de pré-commit

## 💡 Exemplos de Uso

### Validação Básica

```bash
# Validação mínima (apenas pasta de entrada é obrigatória)
python -m data_validate.main --input_folder data/input

# Validação com pasta específica e debug
python -m data_validate.main \
    --input_folder /caminho/para/planilhas \
    --output_folder /caminho/para/relatorios \
    --debug
```

### Validação com Diferentes Idiomas

```bash
# Interface em português (padrão)
python -m data_validate.main --input_folder data/input --locale pt_BR

# Interface em inglês
python -m data_validate.main --input_folder data/input --locale en_US
```

### Validação com Argumentos Avançados

```bash
# Execução completa com todos os argumentos
python -m data_validate.main \
    --input_folder data/input \
    --output_folder data/output \
    --locale pt_BR \
    --debug \
    --sector "Biodiversidade" \
    --protocol "Protocolo v2.1" \
    --user "Pesquisador"
```

### Validação com Flags de Otimização

```bash
# Execução rápida sem verificação ortográfica e avisos de comprimento
python -m data_validate.main \
    --input_folder data/input \
    --no-spellchecker \
    --no-warning-titles-length \
    --no-time \
    --no-version
```

### Usando Abreviações (para desenvolvimento rápido)

```bash
# Comando mais conciso usando abreviações
python -m data_validate.main --i data/input --o data/output --l pt_BR --d
```

### Pipeline Completo

```bash
# Executar pipeline completo com logs
bash scripts/run_main_pipeline.sh
```

## 📊 Tipos de Planilhas Suportadas

| Planilha | Descrição | Validações Principais |
|----------|-----------|----------------------|
| **sp_description** | Descrições de indicadores | Códigos sequenciais, níveis hierárquicos, formatação |
| **sp_value** | Valores dos indicadores | Integridade referencial, tipos numéricos, casas decimais |
| **sp_scenario** | Cenários de análise | Valores únicos, pontuação, relacionamentos |
| **sp_temporal_reference** | Referências temporais | Sequência temporal, símbolos únicos |
| **sp_composition** | Composições hierárquicas | Estrutura em árvore, relacionamentos pai-filho |
| **sp_proportionality** | Proporções | Validação matemática, consistência |
| **sp_legend** | Legendas e categorias | Consistência categórica, valores válidos |
| **sp_dictionary** | Dicionários | Integridade de vocabulário |

## ⚡ Performance e Otimização

- **Processamento eficiente**: Uso otimizado de pandas para grandes datasets
- **Validação paralela**: Execução simultânea de validações independentes
- **Cache inteligente**: Reutilização de dados carregados
- **Logs estruturados**: Sistema de logging otimizado para performance

## 🔍 Monitoramento e Qualidade

### Badges de Status
- **Cobertura de Testes**: Gerada automaticamente com genbadge
- **Status dos Testes**: Atualizada a cada execução
- **Versão**: Sincronizada com pyproject.toml

### Métricas de Qualidade
- Cobertura de código mínima: 4%
- Testes automatizados com pytest
- Linting com ruff e flake8
- Formatação automática com black

## 🤝 Contribuição

### Processo de Desenvolvimento

1. **Fork** o repositório
2. **Clone** seu fork localmente
3. **Crie** uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
4. **Implemente** suas mudanças com testes
5. **Execute** testes (`make test-cov`)
6. **Commit** seguindo as [diretrizes](../../../CODE_OF_CONDUCT.md)
7. **Push** para sua branch (`git push origin feature/nova-funcionalidade`)
8. **Abra** um Pull Request

### Diretrizes de Código

- Siga o padrão PEP 8
- Mantenha cobertura de testes >= 4%
- Use type hints
- Documente funções públicas
- Execute `make black` antes do commit

## 📋 Roadmap

### Versão 0.7.0 (Planejada)
- [ ] Validação de metadados FAIR
- [ ] Suporte a formatos adicionais (CSV, JSON)
- [ ] Interface web básica
- [ ] API REST

### Versão 1.0.0 (Planejada)
- [ ] Interface gráfica completa
- [ ] Validação de schemas customizáveis
- [ ] Integração com bases de dados
- [ ] Suporte a workflows automatizados

## 📄 Licença

Este projeto está licenciado sob a **MIT License** - veja o arquivo [LICENSE](../../../LICENSE) para detalhes.

## 👥 Autores
- **Pedro Andrade** - *Coordenador* - [MAIL](mailto:pedro.andrade@inpe.br) e [GitHub](https://www.github.com/pedro-andrade-inpe)
- **Mário de Araújo Carvalho** - *Colaborador e Desenvolvedor* - [GitHub](https://github.com/MarioCarvalhoBr)
- **Mauro Assis** - *Colaborador* - [GitHub](https://www.github.com/assismauro)
- **Miguel Gastelumendi** - *Colaborador* - [GitHub](https://github.com/miguelGastelumendi)

## 🔗 Links Úteis

- **Homepage**: [AdaptaBrasil GitHub](https://github.com/AdaptaBrasil/)
- **Documentação**: [Docs](https://github.com/MarioCarvalhoBr/data_validate/docs)
- **Issues**: [Bug Tracker](https://github.com/MarioCarvalhoBr/data_validate/issues)
- **Changelog**: [Histórico de Versões](../../../CHANGELOG.md)

## 🐛 Solução de Problemas

### Desinstalando o canoa-data-validate instalado via PyPI

```bash
pip uninstall canoa-data-validate
```

### Argumentos Obrigatórios
```bash
# Erro: "argument --input_folder is required"
# Solução: Sempre especifique a pasta de entrada
python -m data_validate.main --input_folder data/input
```

### Performance Lenta
```bash
# Para execução mais rápida, desative verificações demoradas
python -m data_validate.main \
    --input_folder data/input \
    --no-spellchecker \
    --no-warning-titles-length
```

### Logs Excessivos
```bash
# Para reduzir saída no console
python -m data_validate.main \
    --input_folder data/input \
    --no-time \
    --no-version
```

### Problemas de Encoding
```bash
# O sistema detecta automaticamente encoding com chardet
# Para arquivos problemáticos, verifique se estão em UTF-8
```

### Dependências Ausentes
```bash
# Instalar dependências completas
poetry install

# Para problemas com pdfkit no Linux
sudo apt-get install wkhtmltopdf

# Para problemas com pyenchant
sudo apt-get install libenchant-2-2
```

---

**Desenvolvido com ❤️ pela equipe AdaptaBrasil para validação rigorosa de dados científicos e ambientais.**
