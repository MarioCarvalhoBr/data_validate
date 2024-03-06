# Adapta Parser

![Coverage Status](assets/images/coverage_badge.svg)

## Introdução
Bem-vindo ao repositório do Adapta Parser, uma ferramenta avançada para análise e validação de arquivos de planilhas, especialmente projetada para preparar e verificar dados antes de sua submissão à plataforma Adaptabrasil.

## Características Técnicas

### Linguagem de Programação
- **Python**: O Adapta Parser é desenvolvido em Python, aproveitando sua versatilidade e as extensas bibliotecas disponíveis para manipulação de dados.

### Dependências
- **Pandas**: Utilizado para a leitura, manipulação e análise de dados em arquivos de planilhas.
- **OpenPyXL**: Uma biblioteca para leitura e escrita de arquivos Excel, necessária para manipular arquivos `.xlsx`.
- **Argparse**: Facilita a criação de interfaces de linha de comando, permitindo a passagem de argumentos para o script.


## Criando o ambiente virtual com conda
```shell
conda create -n adapta_data -c conda-forge python numpy pandas -y
conda activate adapta_data
pip install -r requirements.txt
```

## Instalação

Instale os requerimentos

```bash
  pip install -r requirements.txt
```

### Funcionalidades
- **Verificação de Formato de Arquivo**: Assegura que os arquivos de entrada estão no formato `.xlsx`.
- **Análise de Hierarquia e Indicadores**: Examina as relações de hierarquia e os indicadores nas planilhas.
- **Detecção de Inconsistências**: Identifica e relata inconsistências nos dados, como formatos de dados errados ou campos obrigatórios ausentes.
- **Validação de Relações de Dados**: Verifica as relações e dependências entre diferentes conjuntos de dados.

### Estrutura do Projeto
- **myparser.py**: Contém a lógica principal e as funções de verificação.
- **main.py**: Ponto de entrada do programa, lida com argumentos da linha de comando.
- **test_parser.py**: Script para testar o parser, garantindo a consistência e a confiabilidade dos resultados.

### Execução
Para executar o Adapta Parser, use o seguinte comando:
    
```bash
python3 main.py --input_folder=input_data/data_ground_truth/
```

#### Argumentos

- `--input_folder` (obrigatório): Especifica o caminho para a pasta de entrada contendo os arquivos `.xlsx` a serem analisados. Este argumento é obrigatório e deve ser seguido pelo caminho da pasta.

  Exemplo:
  ```
  --input_folder=caminho/para/pasta
  ```

- `--no-spellchecker`: Quando este argumento é usado, o script não executa a verificação ortográfica nos arquivos `.xlsx`. É útil se você deseja acelerar o processo de análise ou se a verificação ortográfica não é necessária.

  Exemplo:
  ```
  --no-spellchecker
  ```

- `--type_dict` (padrão: `full`): Define qual dicionário ortográfico será utilizado durante a análise. As opções são `tiny` para um dicionário menor e mais rápido, ou `full` para um dicionário mais abrangente. Se não especificado, o padrão é `full`.
Os dicionários estão localizados na pasta `dictionaries/`. Atualmente, contém apenas palavras para o idioma português na pasta `dictionaries/pt_BR/`, onde são armazenados os dicionários `tiny.txt` e `full.txt`.
  Exemplos:
  ```
  --type_dict=tiny
  --type_dict=full
  ```

- `--debug`: Executa o programa em modo de depuração. Isso pode incluir a impressão de mensagens de depuração adicionais, úteis para desenvolvimento ou diagnóstico de problemas.

  Exemplo:
  ```
  --debug
  ```

- `--no-warning-titles-length`: Quando este argumento é usado, o script não emite avisos sobre títulos de planilhas que excedem o limite de caracteres. Isso pode ser útil se você deseja ignorar avisos sobre títulos longos.

  Exemplo:
  ```
  --no-warning-titles-length
  ```

### Testes
#### Instalando o coverage
```bash
pip install coverage
```
Execute o código `test_parser.py` para realizar testes automatizados, garantindo que o parser funcione conforme esperado em diferentes cenários de dados.
```bash
pytest --collect-only
pytest -v -s
# Ou
pytest tests/unit/test_parser.py -v
# Ou
coverage run -m pytest  -v -s
coverage run -m pytest tests/unit/test_parser.py -v 
coverage report -m
# Ou
coverage run --source=src/ -m pytest -v -s && coverage report -m
```

### Lint com ruff 
#### Instalando  o ruff
```bash
pip install ruff
```
#### Execute o código abaixo para realizar o lint do código.
```bash
ruff myparser.py
Ou
ruff check . --fix
Ou
ruff check --target-version=py310 .
```

## Autores
- [@assismauro](https://www.github.com/assismauro)
- [@MarioCarvalhoBr](https://www.github.com/MarioCarvalhoBr)
- [@pedro-andrade-inpe](https://www.github.com/pedro-andrade-inpe)
