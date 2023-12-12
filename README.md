# Adapra Parser

## Introdução
Bem-vindo ao repositório do Adapra Parser, uma ferramenta avançada para análise e validação de arquivos de planilhas, especialmente projetada para preparar e verificar dados antes de sua submissão à plataforma Adaptabrasil.

## Características Técnicas

### Linguagem de Programação
- **Python**: O Adapra Parser é desenvolvido em Python, aproveitando sua versatilidade e as extensas bibliotecas disponíveis para manipulação de dados.

### Dependências
- **Pandas**: Utilizado para a leitura, manipulação e análise de dados em arquivos de planilhas.
- **OpenPyXL**: Uma biblioteca para leitura e escrita de arquivos Excel, necessária para manipular arquivos `.xlsx`.
- **Argparse**: Facilita a criação de interfaces de linha de comando, permitindo a passagem de argumentos para o script.

## Instalação

Instale os requerimentos

```bash
  pip install -r requeriments.txt
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
Para executar o Adapra Parser, use o seguinte comando:
    
```bash
python3 main.py --input_folder=input/
```

### Testes
Execute `test_parser.py` para realizar testes automatizados, garantindo que o parser funcione conforme esperado em diferentes cenários de dados.
```bash
pytest test_parser.py
```

## Autores
- [@assismauro](https://www.github.com/assismauro)
- [@MarioCarvalhoBr](https://www.github.com/MarioCarvalhoBr)
- [@pedro-andrade-inpe](https://www.github.com/pedro-andrade-inpe)
