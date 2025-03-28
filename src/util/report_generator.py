import os
import sys
from jinja2 import Environment, FileSystemLoader
import pdfkit
import src.myparser.info as info
from src.util.utilities import format_number_brazilian
import platform

class ReportGenerator:
    def __init__(self, folder, template_name="default.html", no_time=False, no_version=False, sector=None, protocol=None, user=None, file=None):
        self.no_time = no_time
        self.no_version = no_version
        # Optional argument
        self.sector = sector
        self.protocol = protocol
        self.user = user
        self.file = file

        # Others vars 
        self.num_errors = 0
        self.num_warnings = 0
        self.number_tests = 0

        self.folder = folder
        self.output_folder = None
        self.template_name = template_name
        self.env = Environment(loader=FileSystemLoader(folder))
        self.create_html_template()

    def create_html_template(self):
        """ Cria ou verifica a existência de um template HTML para os relatórios. """
        file_path = os.path.join(self.folder, self.template_name)

        if os.path.exists(file_path):
            os.remove(file_path)

        text_html = """
                        <!DOCTYPE html>
                        <html lang="pt-br">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                            <title>Canoa Report</title>
                            <style>
                                /* Estilo CSS minimalista baseado no design do Bootstrap: By Mário Carvalho */

                                /* COLORS */
                                /* ---------------------------------------------------------- */
                                :root {
                                    /* TEXT COLORS */
                                    --color-primary: #0000FF; /* Cor azul */
                                    --color-secondary: #007bff; /* Cor cinza */
                                    --color-danger: #FF0000; /* Cor vermelha */
                                    --color-warning: #FFA500; /* Cor laranja */
                                    --color-green: #008000; /* Cor verde */
                                    --color-info: #17a2b8; /* Cor azul clara */
                                    --color-white: #ffffff; /* Cor branca */
                                    --color-black: #000000; /* Cor preta */
                                    --color-gray: #343a40; /* Cor cinza */

                                    /* BACKGROUND COLORS */
                                    --bg-primary: #0000FF; /* Cor azul */
                                    --bg-secondary: #007bff; /* Cor cinza */
                                    --bg-danger: #FF0000; /* Cor vermelha */
                                    --bg-warning: #FFA500; /* Cor laranja */
                                    --bg-success: #008000; /* Cor verde */
                                    --bg-info: #17a2b8; /* Cor azul clara */
                                    --bg-light: #f8f9fa; /* Cor cinza claro */
                                    --bg-white: #ffffff; /* Cor branca */
                                    --bg-black: #000000; /* Cor preta */
                                    --bg-gray: #343a40; /* Cor cinza */

                                    /* CARD COLORS */
                                    --color-card-border: #dee2e6; /* Cor da borda do card */
                                    --color-card-body: #f8f9fa; /* Cor de fundo do corpo do card */
                                    --color-card-gray-light: #0000001A; /* Cor cinza suave */

                                    /* OTHER COLORS */
                                    --color-sepia-light: #EEEDEA; /* Cor sepia suave */
                                }
                                /* END COLORS */
                                /* ---------------------------------------------------------- */

                                /* START MY CUSTOM STYLES */
                                /* ---------------------------------------------------------- */

                                /* BODY */
                                body {
                                    background-color: var(--color-sepia-light); /* Cor de fundo do corpo */
                                    color: var(--color-black); /* Cor padrão do texto */
                                }

                                /* DIVS */
                                .container {
                                    max-width: 100%;
                                    margin-left: 0.10in;
                                    margin-right: 0.10in;
                                }

                                /* CARDS */
                                .card {
                                    border: 1px solid var(--color-card-border);
                                    border-radius: 0.25rem;
                                    box-shadow: 0 4px 6px var(--color-card-gray-light);

                                    overflow: hidden;
                                    margin: 5px auto;
                                }
                                .card-header {
                                    padding: 0.75rem 1rem;
                                    background-color: var(--bg-secondary); /* Cor padrão da faixa */
                                    color: white; /* Cor padrão do texto na faixa */
                                }
                                .card-body {
                                    padding: 1rem;
                                    background-color: var(--color-card-body); /* Cor de fundo do corpo */
                                    font-family: Arial, sans-serif;
                                    font-weight: bold;
                                }
                                .card-title {
                                    margin: 0;
                                    font-size: 1.25rem;
                                    font-weight: bold;
                                }
                                .card-text {
                                    margin-top: 0px;
                                    font-size: 1rem;
                                    color: var(--color-black);
                                }

                                /* HEADER CENTER */
                                .info-header-center {
                                    text-align: center; /* Centraliza os itens horizontalmente */
                                    padding: 0.25rem 0; /* Padding extremamente baixo (top e bottom) */
                                }
                                .info-header-center h1 {
                                    margin: 0; /* Remove margem padrão do h1 */
                                    font-size: 2rem; /* Tamanho da fonte */
                                }
                                .info-header-center h2 {
                                    margin: 0; /* Remove margem padrão do h2 */
                                    font-size: 1.5rem; /* Tamanho da fonte */
                                    color: var(--color-gray); /* Cor do texto */
                                }
                                .info-header-center strong {
                                    font-weight: bold; /* Deixa o texto em negrito */
                                }

                                /* HEADER LEFT */
                                .info-header-left {
                                    text-align: left; /* Centraliza os itens a esquerda */
                                    padding: 0.25rem 0; /* Padding extremamente baixo (top e bottom) */
                                }
                                .info-header-left strong {
                                    font-weight: bold; /* Deixa o texto em negrito */
                                    margin: 0; /* Remove margem padrão do strong */
                                    padding: 0; /* Remove padding padrão do strong */
                                }
                                .info-header-left li {
                                    font-weight: bold; /* Deixa o texto em negrito */
                                    margin: 0; /* Remove margem padrão do strong */
                                    padding: 0; /* Remove padding padrão do strong */
                                }

                                /* TEXT COLORS */
                                .text-primary {
                                    color: var(--color-primary);
                                    font-weight: bold;
                                }
                                .text-secondary {
                                    color: var(--color-secondary);
                                }
                                .text-danger {
                                    color: var(--color-danger);
                                }
                                .text-danger-errors {
                                    color: var(--color-danger);
                                    font-weight: normal;
                                }
                                .text-warning {
                                    color: var(--color-warning);
                                }
                                .text-orange-warning {
                                    color: var(--color-warning);
                                    font-weight: normal;
                                }
                                .text-green {
                                    color: var(--color-green);
                                }
                                .text-info {
                                    color: var(--color-info);
                                }
                                .text-white {
                                    color: var(--color-white);
                                }
                                .text-black {
                                    color: var(--color-black);
                                }
                                .text-gray {
                                    color: var(--color-gray);
                                }

                                /* BACKGROUND COLORS */
                                .bg-primary {
                                    background-color: var(--bg-primary);
                                }
                                .bg-secondary {
                                    background-color: var(--bg-secondary);
                                }
                                .bg-danger {
                                    background-color: var(--bg-danger);
                                }
                                .bg-warning {
                                    background-color: var(--bg-warning);
                                }
                                .bg-success {
                                    background-color: var(--bg-success);
                                }
                                .bg-info {
                                    background-color: var(--bg-info);
                                }
                                .bg-light {
                                    background-color: var(--bg-light);
                                }
                                .bg-white {
                                    background-color: var(--bg-white);
                                }
                                .bg-black {
                                    background-color: var(--bg-black);
                                }
                                .bg-gray {
                                    background-color: var(--bg-gray);
                                }
                                /* END MY CUSTOM STYLES */
                                /* ---------------------------------------------------------- */

                            </style>

                        </head>
                        <body>
                            <!-- DIV PRINCIPAL -->
                            <div class="container">

                                <!-- DIV HEADER -->
                                <div class="info-header-center">
                                    <h1><strong>{{ name }}</strong></h1>
                                    <h2 class="text-subtitle">Relat&oacute;rio de Valida&ccedil;&atilde;o de Dados</h2>
                                </div>

                                <!-- CARD DE INFORMAÇÕES -->
                                <div class="card">
                                    <div class="card-header bg-secondary">
                                        <h5 class="card-title text-white">Informa&ccedil;&otilde;es</h5>
                                    </div>
                                    <div class="card-body">
                                        {{ text_display_user }}
                                        {{ text_display_sector }}
                                        {{ text_display_protocol }}
                                        {{ text_display_date }}
                                        {{ text_display_version }}
                                        {{ text_display_file }}
                                    </div>
                                </div>

                                <!-- CARD DE RESUMO -->
                                <div class="card">
                                    <div class="card-header bg-primary">
                                        <h5 class="card-title text-white">Resumo da valida&ccedil;&atilde;o</h5>
                                    </div>
                                    <div class="card-body">
                                        <strong class="text-danger">N&uacute;mero de Erros: {{ num_errors }}</strong><br>
                                        <strong class="text-warning">N&uacute;mero de Avisos: {{ num_warnings }}</strong><br>
                                        <strong class="text-green">N&uacute;mero de testes executados: {{ number_tests }}</strong><br>
                                        <div class="info-header-left" id="tests_not_executed" style="display: {{ display_tests_not_executed }}">
                                            <strong >Testes n&atilde;o executados: </strong>
                                            {{ tests_not_executed }}
                                        </div>

                                    </div>
                                </div>

                                <!-- CARD DE ERROS -->
                                <div class="card">
                                    <!-- Faixa do título -->
                                    <div class="card-header bg-danger">
                                        <h5 class="card-title text-white">Erros</h5>
                                    </div>
                                    <div class="card-body">
                                        {{ errors }}
                                    </div>
                                </div>

                                <!-- CARD DE AVISOS -->
                                <div class="card">
                                    <!-- Faixa do título -->
                                    <div class="card-header bg-warning">
                                        <h5 class="card-title text-white">Avisos</h5>
                                    </div>
                                    <div class="card-body">
                                        {{ warnings }}
                                    </div>
                                </div>

                            </div>
                        </body>
                        </html>
            """
 
        with open(file_path, 'w') as f:
            f.write(text_html)

    def save_html_pdf_report(self, name_file, output_folder, file_output_html, results_tests, results_tests_not_executed, num_errors, num_warnings, number_tests):
        # Setup vars 
        self.num_errors = num_errors
        self.num_warnings = num_warnings
        self.number_tests = number_tests

        try: 
            

            self.output_folder = output_folder
            """ Preenche o template HTML com dados e salva o resultado. """
            template = self.env.get_template(self.template_name)
            
            # Criando a string de erros
            errors = "".join(
                f"\n<br><span class='text-primary'>{name}</span>\n" +
                "\n".join(f"<br><span class='text-danger-errors'>{error}</span>" for error in errors)
                for name, _, errors, _ in results_tests
            )
            # Remover a quebra de linha e a tag <br> no início da string
            if errors.startswith("\n<br>"):
                errors = errors[5:]
            
            # Criando a string de avisos
            warnings = "".join(
                f"\n<br><span class='text-primary'>{name}</span>\n" +
                "\n".join(f"<br><span class='text-orange-warning'>{warning}</span>" for warning in warnings)
                for name, _, _, warnings in results_tests if warnings
            )
            # Remover a quebra de linha e a tag <br> no início da string
            if warnings.startswith("\n<br>"):
                warnings = warnings[5:]
                
            display_tests_not_executed = "block" if results_tests_not_executed else "none"

            results_tests_not_executed = "\n".join([f"<li>{test_name}</li>" for test_name in results_tests_not_executed])
            results_tests_not_executed = f"<ul>{results_tests_not_executed}</ul>"


            date_now = ""
            if not self.no_version:
                date_now = f"<strong>Data e hora do processo: <strong class='text-gray'>{ info.__date_now__ }</strong></strong><br>"

            app_version = ""
            if not self.no_time:
                info_os_name = platform.system()
                app_version = f"<strong>Vers&atilde;o do validador: <strong class='text-gray'>{ info.__version__ } &ndash; {info_os_name}</strong></strong><br>"
                
            if not self.no_version and not self.no_time:
                app_version = app_version

            # Optional arguments
            text_display_user = ""
            text_display_sector = ""
            text_display_protocol = ""
            text_display_file = ""
            
            if self.sector is not None:
                text_display_sector = f"<strong>Setor estrat&eacute;gico: <strong class='text-gray'>{self.sector}</strong></strong><br>"
            
            if self.protocol is not None:
                text_display_protocol = f"<strong>Protocolo: <strong class='text-gray'>{self.protocol}</strong></strong><br>"

            if self.user is not None:
                text_display_user = f"<strong>Usu&aacute;rio: <strong class='text-gray'>{self.user}</strong></strong><br>"

            if self.file is not None:
                text_display_file = f"<strong>Arquivo submetido: <strong class='text-gray'>{self.file}</strong></strong><br>"

            template_vars = {
                "name": info.__name__,

                "errors": errors,
                "warnings": warnings,
                "num_errors": format_number_brazilian(self.num_errors),
                "num_warnings": format_number_brazilian(self.num_warnings),
                "number_tests": self.number_tests,

                "text_display_version": app_version,
                "text_display_date": date_now,
                "text_display_sector": text_display_sector,
                "text_display_protocol": text_display_protocol,
                "text_display_user": text_display_user,
                "text_display_file": text_display_file,

                "tests_not_executed": results_tests_not_executed,
                "display_tests_not_executed": display_tests_not_executed

            }

            html_out = template.render(template_vars)
            output_path_file_html = os.path.join(self.output_folder, name_file + file_output_html)
            with open(output_path_file_html, 'w', encoding="utf-8") as f:
                f.write(html_out)
            
            print(f'\nFoi criado um arquivo de relatório em HTML no caminho: {output_path_file_html}')
            self.save_pdf_report(output_path_file_html)

        except Exception as e:
            print(f'\nErro ao criar o arquivo de relatório em HTML: {e}', file=sys.stderr)

        # Imprimir a saída em JSON
        info_minimized_results_json = {
                "data_validate": {
                    "version": info.__version__,
                    "report": {
                        "errors": int(self.num_errors),
                        "warnings": int(self.num_warnings),
                        "tests": int(self.number_tests)
                    }
                }   
            }

        string_final = f'<{info_minimized_results_json}>'  # Saída final para o usuário
        string_final = string_final.replace("'", '"')
        print(f'\n{string_final}\n')
    
    def save_pdf_report(self, output_path_file_html):
        try:             
            output_path_file_pdf = output_path_file_html.replace(".html", ".pdf")

            options = {
                'page-size': 'Letter',
                'margin-top': '0.0in',
                'margin-right': '0.0in',
                'margin-bottom': '0.0in',
                'margin-left': '0.0in',
                'encoding': "UTF-8",
                'custom-header': [
                    ('Accept-Encoding', 'gzip')
                ],
                'cookie': [],
                'no-outline': None
            }

            pdfkit.from_file(output_path_file_html, output_path_file_pdf, options=options)
            print(f'\nFoi criado um arquivo de relatório em PDF no caminho: {output_path_file_pdf}\n')
            

        except Exception as e:
            print(f'\nErro ao criar o arquivo de relatório em PDF: {e}', file=sys.stderr)
            pass
