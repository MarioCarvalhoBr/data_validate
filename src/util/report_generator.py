import os
from jinja2 import Environment, FileSystemLoader
from pyhtml2pdf import converter
import src.myparser.info as info

class ReportGenerator:
    def __init__(self, folder, template_name="default.html", no_time=False):
        self.no_time = no_time
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
                            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
                            <title>Canoa Report</title>
                            <style>
                                .container {
                                    max-width: 98%;
                                }
                            </style>
                        </head>
                        <body>
                            <div class="container my-5">

                                <div class="text-center mb-12">
                                    <h1><strong>{{ name }}</strong></h1>
                                    <h2>Relat&oacute;rio de Valida&ccedil;&atilde;o de Dados</h2>
                                </div>

                                <div class="card mb-12">
                                    <div class="card-header bg-primary text-white">
                                        <strong>Informa&ccedil;&otilde;es</strong>
                                    </div>
                                    <div class="card-body">
                                        <strong>Vers&atilde;o do validador:</strong>  {{ version }}<br>
                                        <strong style="display: {{ display_date }}">Data e hora do processo: </strong>{{ date_now }}
                                    </div>
                                </div>

                                <div class="card">
                                    <div class="card-header bg-primary text-white">
                                        <strong>Resumo da valida&ccedil;&atilde;o</strong>
                                    </div>
                                    <div class="card-body">
                                        <p class="card-text"><strong class="text-danger">N&uacute;mero de Erros: {{ num_errors }}</strong></p>
                                        <p class="card-text"><strong class="text-warning">N&uacute;mero de Avisos: {{ num_warnings }}</strong></p>
                                        <p class="card-text" style="color: green;"><strong>N&uacute;mero de testes executados: {{ number_tests }}</strong></p>

                                        <p id="tests_not_executed" class="card-text" style="display: {{ display_tests_not_executed }}"><strong>Testes n&atilde;o executados:</strong> {{ tests_not_executed }} </p>
                                        
                                        
                                    </div>
                                </div>
                                <br>

                                <div class="card mb-12">
                                    <div class="card-header bg-danger text-white">
                                        <strong>Erros</strong>
                                    </div>
                                    <div class="card-body">
                                        <p class="card-text">{{ errors }}</p>
                                    </div>
                                </div>
                                <div class="card mb-4">
                                    <div class="card-header text-dark bg-warning">
                                        <strong>Avisos</strong>
                                    </div>
                                    <div class="card-body">
                                        <p class="card-text">{{ warnings }}</p>
                                    </div>
                                </div>

                            </div>
                        </body>
                        </html>
            """
 
        with open(file_path, 'w') as f:
            f.write(text_html)
        # print('\nCreated a file report in HTML template: ', file_path)

    def save_html_pdf_report(self, name_file, output_folder, file_output_html, results_tests, results_tests_not_executed, num_errors, num_warnings, number_tests):
        try: 
            self.output_folder = output_folder
            """ Preenche o template HTML com dados e salva o resultado. """
            template = self.env.get_template(self.template_name)
            
            errors = "\n<br>".join(
                f"\n<br><span style='color: blue;'>{name}</span>:\n<br>" +
                "\n<br>".join(f"<span style='color: red;'>{error}</span>" for error in errors)
                for name, _, errors, _ in results_tests
            )

            warnings = "\n<br>".join(
                f"\n<br><span style='color: blue;'>{name}</span>:\n<br>" +
                "\n<br>".join(f"<span style='color: orange;'>{warning}</span>" for warning in warnings)
                for name, _, _, warnings in results_tests if warnings
            )
            display_tests_not_executed = "block" if results_tests_not_executed else "none"
            display_date = "block" if not self.no_time else "none"

            results_tests_not_executed = "\n".join([f"<li>{test_name}</li>" for test_name in results_tests_not_executed])
            results_tests_not_executed = f"<ul>{results_tests_not_executed}</ul>"

            date_now = info.__date_now__
            if self.no_time:
                date_now = ""

            template_vars = {
                "name": info.__name__,

                "version": info.__version__,
                "errors": errors,
                "warnings": warnings,
                "num_errors": num_errors,
                "num_warnings": num_warnings,
                "number_tests": number_tests,

                "date_now": date_now,
                "display_date": display_date,

                "tests_not_executed": results_tests_not_executed,
                "display_tests_not_executed": display_tests_not_executed

            }

            html_out = template.render(template_vars)
            output_path = os.path.join(self.output_folder, name_file + file_output_html)
            with open(output_path, 'w', encoding="utf-8") as f:
                f.write(html_out)
            
            print(f'\nFoi criado um arquivo de relatório em HTML no caminho: {output_path}')
            self.save_pdf_report(output_path)

        except Exception as e:
            print(f'\nErro ao criar o arquivo de relatório em HTML: {e}')
            pass
    
    def save_pdf_report(self, output_path):
        try: 
            ABSOLUTE_PATH_FILE = os.path.abspath(output_path)
            
            FULL_FILE_PATH_HTML = f'file:///{ABSOLUTE_PATH_FILE}'
            ABS_PATH_PDF = ABSOLUTE_PATH_FILE.replace(".html", ".pdf")

            converter.convert(FULL_FILE_PATH_HTML, ABS_PATH_PDF, install_driver= False)
            print(f'\nFoi criado um arquivo de relatório em PDF no caminho: {os.path.join(self.output_folder, os.path.basename(ABS_PATH_PDF))}\n')

        except Exception as e:
            print(f'\nErro ao criar o arquivo de relatório em PDF: {e}')
            pass
