# Adapta Parser

![Coverage Status](reports/coverage/coverage_badge.svg)
![Tests Status](reports/coverage/tests_badge.svg)

## Introdução
Bem-vindo ao repositório do Adapta Parser, uma ferramenta avançada para análise e validação de arquivos de planilhas, especialmente projetada para preparar e verificar dados antes de sua submissão à plataforma Adaptabrasil.

## Características Técnicas

### Linguagem de Programação
- **Python**: O Adapta Parser é desenvolvido em Python, aproveitando sua versatilidade e as extensas bibliotecas disponíveis para manipulação de dados.

### Dependências
- **Pandas**: Utilizado para a leitura, manipulação e análise de dados em arquivos de planilhas.
- **OpenPyXL**: Uma biblioteca para leitura e escrita de arquivos Excel, necessária para manipular arquivos `.xlsx`.
- **Argparse**: Facilita a criação de interfaces de linha de comando, permitindo a passagem de argumentos para o script.
- **PyHunspell**: Uma interface Python para o verificador ortográfico Hunspell.

#### Dependências de produção
- **Python 3.6+**: A versão mínima do Python necessária para executar o Adapta Parser.
- **LibHunspell**: Uma biblioteca de verificação ortográfica, necessária para a verificação ortográfica.
- **Wkhtmltopdf**: Uma ferramenta de linha de comando para converter HTML em PDF, necessária para gerar relatórios em PDF.
  
##### GNU/LINUX
Certifique-se de que `python-dev`, `libhunspell-dev` e `wkhtmltopdf` estejam instalados,

```shell
    # Instalando as dependências
    sudo apt-get install python3-dev libhunspell-dev wkhtmltopdf

    # Para correção de erros ortográficos
    pip install hunspell

    # Para gerar relatórios em PDF
    pip install pdfkit
```
##### Windows
Nos sistemas Windows, a instalação do `wkhtmltopdf` e `libhunspell` é um pouco mais complicada. Aqui estão as instruções para instalar essas dependências no Windows.

###### wkhtmltopdf no Windows
Para instalar o `wkhtmltopdf`, baixe o instalador do site oficial: https://wkhtmltopdf.org/downloads.html

###### libhunspell no Windows
- Alternativa 1: Usando o Chocolatey
  
  Se você tiver o Chocolatey instalado, você pode instalar o `libhunspell` usando o seguinte comando:

  ```shell
  choco install hunspell.portable
  ```

- Alternativa 2: Instalação manual
  
  Para instalar o `libhunspell` no Windows, você pode usar o pacote pré-compilado disponível em https://sourceforge.net/projects/ezwinports/files/hunspell-1.3.2-3-w32-bin.zip/download para download. Você pode descompactar o arquivo ZIP e copiar os arquivos da pasta `bin/` para a pasta `C:\Windows\System32`.

- Alternativa 3: Compiling with Mingw64 and MSYS2
  
  Primeiro, clone o repositório do hunspell:
  ```shell
  git clone https://github.com/hunspell/hunspell.git
  ```
  Realize o download do Msys2, atualize tudo e instale os seguintes pacotes:

  ```shell
  # Instalando o MSYS2
  pacman -S base-devel mingw-w64-x86_64-toolchain mingw-w64-x86_64-libtool

  # Compilando o hunspell
  autoreconf -vfi
  ./configure
  make
  sudo make install
  sudo ldconfig
  ```
- REFERÊNCIAS do hunspell: 
  
- https://github.com/hunspell/hunspell
- https://stackoverflow.com/questions/58458901/how-do-i-install-hunspell-on-windows10


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
python3 main.py --input_folder=input_data/data_ground_truth_01/ --output_folder=output_data/
```

#### Argumentos

- `--input_folder` (obrigatório): Especifica o caminho para a pasta de entrada contendo os arquivos `.xlsx` a serem analisados. Este argumento é obrigatório e deve ser seguido pelo caminho da pasta.

  Exemplo:
  ```
  --input_folder=caminho/para/pasta
  ```

- `--output_folder` (padrão: `output_data/`): Especifica o caminho para a pasta de saída onde os resultados da análise serão salvos. Se não for fornecido, os resultados serão salvos na pasta `output_data/`.
  
  Exemplo:
  ```
  --output_folder=caminho/para/pasta
  ```

- `--no-spellchecker`: Quando este argumento é usado, o script não executa a verificação ortográfica nos arquivos `.xlsx`. É útil se você deseja acelerar o processo de análise ou se a verificação ortográfica não é necessária.
  Exemplo:
  ```
  --no-spellchecker
  ```

- `--lang-dict` (padrão: `pt`): Define qual a linguagem do dicionário ortográfico a ser usado. O valor padrão é `pt` (português). Você pode alterar para `en` (inglês) ou qualquer outro idioma suportado. Para adicionar novas palavras ao dicionário extra do verificador ortográfico, adicione-as ao arquivo `dictionaries/extra-words.dic`, onde a primeira linha deve ser o número de palavras adicionadas e as linhas seguintes devem conter as palavras adicionadas.
  Exemplos:
  ```
  --lang-dict=pt
  --lang-dict=en
  ```

- `--no-warning-titles-length`: Quando este argumento é usado, o script não emite avisos sobre títulos de planilhas que excedem o limite de caracteres. Isso pode ser útil se você deseja ignorar avisos sobre títulos longos.
  Exemplo:
  ```
  --no-warning-titles-length
  ```

- `--debug`: Executa o programa em modo de depuração. Isso pode incluir a impressão de mensagens de depuração adicionais, úteis para desenvolvimento ou diagnóstico de problemas.
  Exemplo:
  ```
  --debug
  ```

- `--no-time`: Quando este argumento é usado, o script não exibe informações de tempo de execução, além de omitir a data e hora da execução nos relatórios. Isso pode ser útil se você deseja reduzir a quantidade de saída gerada.
  Exemplo:
  ```
  --no-time
  ```

- `--no-version`: Quando este argumento é usado, o script não exibe a versão do Adapta Parser no relatório de saída Isso pode ser útil se você deseja reduzir a quantidade de saída gerada.
  - Exemplo:
  ```
  --no-version
  ```

- `--sector`: Quando este argumento é usado, o script exibe o setor estratégico no relatório de saída. Isso pode ser útil se você deseja adicionar informações adicionais ao relatório.
  - Exemplo:
  ```
  --sector=nome_do_setor
  ```

- `--protocol`: Quando este argumento é usado, o script exibe o protocolo no relatório de saída. Isso pode ser útil se você deseja adicionar informações adicionais ao relatório.
  - Exemplo:
  ```
  --protocol=nome_do_protocolo
  ```

- `--user`: Quando este argumento é usado, o script exibe o nome do usuário no relatório de saída. Isso pode ser útil se você deseja adicionar informações adicionais ao relatório.
  - Exemplo:
  ```
  --user=nome_do_usuario
  ```

- `--file`: Nome do arquivo submetido para análise. Isso pode ser útil se você deseja adicionar informações adicionais ao relatório. Se não for fornecido, o nome do arquivo submetido não será exibido no relatório.
  - Exemplo:
  ```
  --file=nome_do_arquivo.zip
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


### Erros comuns

#### Enum34
```shell
pip install enum34
```
#### Pre-commit install 
```shell
pre-commit install
```
#### Install genbadge

```shell
pip install genbadge[all]
          
```
