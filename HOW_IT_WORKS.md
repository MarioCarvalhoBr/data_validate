# HOW_IT_WORKS

## Visão Geral

O Adapta Parser é um validador e processador de planilhas, desenvolvido em Python, que automatiza a checagem de integridade e estrutura de arquivos de dados. Ele é especialmente útil para projetos que exigem padronização e validação rigorosa de dados tabulares, como pesquisas científicas, bancos de dados ambientais e sistemas de indicadores.

## Estrutura do Projeto

- **data_validate/main.py**: Ponto de entrada do sistema. Inicializa argumentos, configura o ambiente, gerencia logs e executa o processamento principal.
- **data_validate/core/**: Contém o processador principal (`processor.py`) e a lógica de geração de relatórios (`report.py`).
- **data_validate/data_model/**: Define os modelos de dados (ex: valores, proporções, cenários, legendas) e suas validações específicas.
- **data_validate/common/**: Utilitários para manipulação de arquivos, argumentos, internacionalização, logs e validações genéricas.
- **data_validate/controller/**: Gerencia a importação de dados e integrações com diferentes fontes/formats.
- **data_validate/validation/**: Estruturas e funções para validação de dados.
- **data_validate/static/**: Arquivos estáticos, como templates de relatórios e mensagens de localização.

## Fluxo de Funcionamento

1. **Inicialização**  
   O usuário executa o script principal (`main.py`), informando os diretórios de entrada e saída, além do idioma desejado.

2. **Leitura e Importação**  
   O sistema importa os arquivos de dados do diretório de entrada, utilizando classes especializadas para cada tipo de planilha.

3. **Validação**  
   Cada arquivo é validado conforme seu modelo de dados:
   - Verificação de colunas obrigatórias e opcionais.
   - Checagem de nomes, cenários, legendas, proporções, etc.
   - Mensagens de erro e advertência são geradas em português ou inglês, conforme configuração.

4. **Processamento**  
   Após a validação, os dados podem ser processados para análises, transformações ou cálculos adicionais, dependendo do modelo.

5. **Geração de Relatórios**  
   Um relatório detalhado é gerado, indicando erros, advertências e o status de cada arquivo processado.

6. **Saída**  
   Os resultados (relatórios, logs e arquivos processados) são salvos no diretório de saída especificado pelo usuário.

## Como Executar

```bash
python3 -m data_validate.main --locale pt_BR --input_folder data/input --output_folder data/output --debug
```

## Personalização

- **Modelos de Dados**: Para adicionar novos tipos de validação, basta criar uma nova classe em `data_model/` seguindo o padrão das existentes.
- **Mensagens**: As mensagens de erro e interface podem ser personalizadas nos arquivos de localização em `static/locales/`.
- **Relatórios**: O template do relatório pode ser ajustado em `static/report/report_template.html`.

## Testes

Execute todos os testes com:
```bash
pytest .
```

## Documentação

Gere a documentação automática com:
```bash
pdoc ./data_validate/ -o ./docs
```

---

**Dúvidas ou sugestões? Consulte o README.md ou abra uma issue no repositório.**