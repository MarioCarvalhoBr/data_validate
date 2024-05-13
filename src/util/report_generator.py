import os
from jinja2 import Environment, FileSystemLoader
from pyhtml2pdf import converter
import src.myparser.info as info

class ReportGenerator:
    def __init__(self, folder, template_name="default.html"):
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

                                <div class="text-center mb-4">
                                    <h1><strong>{{ name }}</strong></h1>
                                    <h2>Relatório de Validação de Dados</h2>
                                </div>

                                <div class="card mb-4">
                                    <div class="card-header bg-primary text-white">
                                        <strong>Informações</strong>
                                    </div>
                                    <div class="card-body">
                                        <strong>Data e hora do processo: </strong>{{ date_now }}<br>
                                        <strong>Versão do validador:</strong>  {{ version }}
                                    </div>
                                </div>

                                <div class="card">
                                    <div class="card-header bg-primary text-white">
                                        <strong>Resumo da validação</strong>
                                    </div>
                                    <div class="card-body">
                                       <p class="card-text"><strong class="text-danger">Número de Erros: {{ num_errors }}</strong></p>
                                        <p class="card-text"><strong class="text-warning">Número de Avisos: {{ num_warnings }}</strong></p>
                                    </div>
                                </div>
                                <br>

                                <div class="card mb-4">
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
                            <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js" integrity="sha384-I7E8VVD/ismYTF4hNIPjVp/Zjvgyol6VFvRkX/vR+Vc4jQkC+hVqc2pM8ODewa9r" crossorigin="anonymous"></script>
                            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.min.js" integrity="sha384-0pUGZvbkm6XF6gxjEnlmuGrJXVbNuzT9qBBavbLwCsOGabYfZo0T0to5eqruptLy" crossorigin="anonymous"></>
                        </body>
                        </html>

            """
        with open(file_path, 'w') as f:
            f.write(text_html)
        # print('\nCreated a file report in HTML template: ', file_path)

    def save_html_pdf_report(self, name_file, output_folder, file_output_html, results_tests):
        try: 
            self.output_folder = output_folder
            """ Preenche o template HTML com dados e salva o resultado. """
            template = self.env.get_template(self.template_name)
            
            num_errors = sum(len(data_test[2]) for data_test in results_tests if not data_test[1])
            num_warnings = sum(len(data_test[3]) for data_test in results_tests)
            
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

            template_vars = {
                "name": info.__name__,
                "date_now": info.__date_now__,
                "version": info.__version__,
                "errors": errors,
                "warnings": warnings,
                "num_errors": num_errors,
                "num_warnings": num_warnings
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

            converter.convert(FULL_FILE_PATH_HTML, ABS_PATH_PDF)
            
            print(f'\nFoi criado um arquivo de relatório em PDF no caminho: {os.path.join(self.output_folder, os.path.basename(ABS_PATH_PDF))}\n')

        except Exception as e:
            print(f'\nErro ao criar o arquivo de relatório em PDF: {e}')
            pass
