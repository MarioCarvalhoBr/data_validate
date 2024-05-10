import os
from jinja2 import Environment, FileSystemLoader
from pyhtml2pdf import converter

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
        if not os.path.exists(file_path):
            text_html = """
            <!DOCTYPE html>
            <html>
            <head lang="en">
                <meta charset="UTF-8">
                <title>Data Validate</title>
            </head>
            <body>
                <h2>Report Errors</h2>
                <p>{{ errors }}</p>
                <h2>Report Warnings</h2>
                <p>{{ warnings }}</p>
                <h2>Report Info</h2>
                <p>Number of errors: {{ num_errors }}</p>
                <p>Number of warnings: {{ num_warnings }}</p>
            </body>
            </html>
            """
            with open(file_path, 'w') as f:
                f.write(text_html)
            # print('\nCreated a file report in HTML template: ', file_path)

    def save_html_pdf_report(self, output_folder, file_output_html, results_tests):
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
                "errors": errors,
                "warnings": warnings,
                "num_errors": num_errors,
                "num_warnings": num_warnings
            }

            html_out = template.render(template_vars)
            output_path = os.path.join(self.output_folder, file_output_html)
            with open(output_path, 'w', encoding="utf-8") as f:
                f.write(html_out)
            print(f'\nCriado um arquivo de relatório em HTML: {output_path}')
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
            
            print(f'\nCriado um arquivo de relatório em PDF: {os.path.join(self.output_folder, os.path.basename(ABS_PATH_PDF))}\n')

        except Exception as e:
            print(f'\nErro ao criar o arquivo de relatório em PDF: {e}')
            pass
