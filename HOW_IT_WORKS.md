# Como Funciona

Este documento detalha a arquitetura e o fluxo de execução do projeto `data-validate`, fornecendo uma visão geral de como os componentes interagem para validar os dados das planilhas.

## Estrutura de Diretórios

A estrutura do projeto foi organizada para separar responsabilidades, facilitando a manutenção e a escalabilidade.

```
data-validate/
├── assets/               # Badges de cobertura e testes
├── data/                 # Dados de entrada e saída
│   ├── input/            # Planilhas a serem validadas
│   └── output/           # Relatórios e logs gerados
├── data_validate/        # Código-fonte da aplicação
│   ├── config/           # Configurações globais
│   ├── controllers/      # Orquestração do fluxo de validação
│   ├── helpers/          # Funções utilitárias
│   ├── middleware/       # Camada de inicialização e configuração
│   ├── models/           # Modelos de dados que representam as planilhas
│   ├── static/           # Arquivos estáticos (dicionários, templates)
│   └── validators/       # Lógica de validação (estrutura, ortografia, etc.)
├── dev-reports/          # Relatórios de desenvolvimento (cobertura, etc.)
├── docs/                 # Documentação gerada
├── scripts/              # Scripts de automação
├── tests/                # Testes unitários e de integração
├── Makefile              # Comandos de automação (test, clean, badge)
├── pyproject.toml        # Definição do projeto e dependências (Poetry)
└── README.md             # Documentação principal
```

### Componentes Principais

-   **`data_validate/main.py`**: Ponto de entrada da aplicação. Ele inicializa o processo de validação.
-   **`data_validate/middleware/bootstrap.py`**: Responsável por configurar o ambiente, como a criação de diretórios e a configuração de logs, antes da execução principal.
-   **`data_validate/controllers/processor.py`**: O coração da aplicação. Ele orquestra a leitura dos dados, a execução das validações em sequência e a geração dos relatórios de saída.
-   **`data_validate/models/`**: Contém classes que modelam a estrutura esperada de cada planilha (e.g., `sp_legend.py`, `sp_value.py`). Eles definem as colunas, tipos de dados e regras de negócio.
-   **`data_validate/validators/`**: Contém a lógica específica para cada tipo de validação. Por exemplo:
    -   `structure/`: Valida a estrutura das planilhas (nomes de colunas, ordem, etc.).
    -   `spell/`: Realiza a verificação ortográfica.
    -   `spreadsheets/`: Contém validações de regras de negócio específicas para cada planilha.
-   **`data_validate/helpers/`**: Funções genéricas e reutilizáveis que auxiliam os outros componentes, como manipulação de DataFrames, leitura de arquivos e formatação de logs.
-   **`data/`**: Diretório crucial para a operação. Os dados a serem validados são colocados em `data/input/`, e os resultados, incluindo logs de erros e relatórios, são salvos em `data/output/`.

## Fluxo de Execução

O processo de validação segue as seguintes etapas:

1.  **Inicialização**: O `main.py` é executado, acionando o `Bootstrap` para preparar o ambiente.
2.  **Carga de Dados**: O `Processor` lê as planilhas do diretório `data/input/`.
3.  **Execução das Validações**: O `Processor` invoca uma série de validadores em uma ordem predefinida:
    -   **Validação de Estrutura**: Verifica se as planilhas e colunas existem e estão nomeadas corretamente.
    -   **Validação de Conteúdo**: Aplica as regras definidas nos `models` e `validators` para cada planilha, como:
        -   Verificação de tipos de dados.
        -   Checagem de valores obrigatórios.
        -   Validação de relações entre diferentes planilhas.
        -   Verificação ortográfica em campos de texto.
4.  **Coleta de Erros**: Cada validador retorna uma lista de erros e avisos encontrados. O `Processor` agrega todos esses resultados.
5.  **Geração de Relatórios**: Ao final, o `Processor` utiliza os erros e avisos coletados para gerar relatórios detalhados em `data/output/`, geralmente em formatos como `.txt`, `.csv` ou `.html`.

## Como Usar

O projeto utiliza `Poetry` para gerenciamento de dependências e `Make` para automação de tarefas comuns.

### Instalação

Para instalar as dependências, execute:

```sh
poetry install
```

### Execução da Validação

Para rodar o pipeline completo de validação:

```sh
bash scripts/run_main_pipeline.sh
```

### Execução dos Testes

O `Makefile` fornece comandos para executar os testes:

```sh
# Rodar todos os testes
make test

# Rodar testes com relatório de cobertura
make test-cov
```

### Geração de Badges

Para gerar os badges de cobertura e testes (salvos em `assets/coverage/`):

```sh
make make-badge
```

