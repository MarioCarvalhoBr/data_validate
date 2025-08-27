#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import os
import sys
import time
from pathlib import Path
import re
from jinja2 import Environment, FileSystemLoader
import pdfkit
import platform

from common.base.metadata_info import METADATA
from common.utils.formatting.number_formatting import format_number_brazilian
from controller.context.general_context import GeneralContext
from controller.report.model_report import ModelReportList

info = METADATA


class ReportGeneratorPDF:
    def __init__(self, context: GeneralContext=None):

        self.context = context

        # DataAction args
        self.no_time = self.context.data_args.data_action.no_time
        self.no_version = self.context.data_args.data_action.no_version
        # DataReport args
        self.sector = self.context.data_args.data_report.sector
        self.protocol = self.context.data_args.data_report.protocol
        self.user = self.context.data_args.data_report.user
        self.file = self.context.data_args.data_report.file

        # Others vars
        self.num_errors = 0
        self.num_warnings = 0
        self.number_tests = 0

        self.input_folder = self.context.data_args.data_file.input_folder
        self.output_folder = self.context.data_args.data_file.output_folder
        self.template_name = self.context.config.OUTPUT_DEFAULT_HTML
        self.template = ""
        self.required_variables = []

        self.env = Environment(loader=FileSystemLoader(self.output_folder))

        self.validate_html_template()

    def validate_html_template(self):
        template_default_with_errors = """
                            <!DOCTYPE html>
                            <html lang="pt-br">
                            <head>
                                <meta charset="UTF-8">
                                <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                                <title>Canoa Report</title>
                            </head>
                            <body>
                                <h1 style="color:#FF0000;">Relat&oacute;rio gerando com o template padr&atilde;o de erro</h1>
                                <p>Esse relat&oacute;rio foi gerado com o template padr&atilde;o de erro, pois o template personalizado n&atilde;o foi encontrado ou est&aacute; faltando vari&aacute;veis obrigat&oacute;rias.</p>
                                <p>Entre em contato com o administrador do sistema para corrigir o problema.</p>
                                <p>RELAT&Oacute;RIO</p>
                                {{ name }}
                                Relat&oacute;rio de Valida&ccedil;&atilde;o de Dados
                                Informa&ccedil;&otilde;es: 
                                {{ text_display_user }}
                                {{ text_display_sector }}
                                {{ text_display_protocol }}
                                {{ text_display_date }}
                                {{ text_display_version }}
                                {{ text_display_file }}
                                Resumo da validação
                                N&uacute;mero de Erros: {{ num_errors }}
                                N&uacute;mero de Avisos: {{ num_warnings }}
                                N&uacute;mero de testes executados: {{ number_tests }}
                                Testes n&atilde;o executados: {{ tests_not_executed }}
                                Mostrar erros n&atilde;o executados: {{ display_tests_not_executed }}
                                Erros
                                {{ errors }}
                                Avisos
                                {{ warnings }}
                            </body>
                            </html>
                            """

        # Expressão regular para encontrar o padrão completo, incluindo as chaves
        regex = r"\{\{\s*.*?\s*\}\}"

        # Usando re.findall para extrair todas as correspondências completas
        self.required_variables = re.findall(regex, template_default_with_errors)

        # 1. Validate existence of the template file
        template_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'../../static/report/report_template.html'))
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                self.template = f.read()

        # 2. Validate required variables in the template
        missing_variables = []
        for variable in self.required_variables:
            if variable not in self.template:
                missing_variables.append(variable)
        if missing_variables:
            self.template = template_default_with_errors

    def save_html_pdf_report(self, report_list: ModelReportList, results_tests_not_executed):

        name_file = self.context.fs_utils.get_last_directory_name(path=self.input_folder)
        file_output_html = self.context.config.OUTPUT_REPORT_HTML

        # Setup vars
        self.num_errors = sum(len(report.errors) for report in report_list)
        self.num_warnings = sum(len(report.warnings) for report in report_list)
        self.number_tests = len(report_list)

        try:
            """ Preenche o template HTML com dados e salva o resultado. """
            template = self.env.from_string(self.template)
            # Criando a string de erros a partir do report_list
            errors = ""
            warnings = ""
            for report in report_list:
                errors += f"<br><span class='text-primary'>{report.name_test}</span>\n"
                if report.errors:
                    for error in report.errors:
                        errors += f"<br><span class='text-danger-errors'>{error}</span>\n"

                warnings += f"<br><span class='text-primary'>{report.name_test}</span>\n"
                if report.warnings:
                    for warning in report.warnings:
                        warnings += f"<br><span class='text-orange-warning'>{warning}</span>\n"

            # Remover a primeira tag <br> se existir
            if errors.startswith("<br>"):
                errors = errors[4:]

            # Remover a primeira tag <br> se existir
            if warnings.startswith("<br>"):
                warnings = warnings[4:]

            display_tests_not_executed = "block" if results_tests_not_executed else "none"

            results_tests_not_executed = "\n".join(
                [f"<li>{test_name}</li>" for test_name in results_tests_not_executed])
            results_tests_not_executed = f"<ul>{results_tests_not_executed}</ul>"

            date_now = ""
            if not self.no_time:
                date_now = f"<strong>Data e hora do processo: <strong class='text-gray'>{info.__date_now__}</strong></strong><br>"

            app_version = ""
            if not self.no_version:
                info_os_name = platform.system()
                app_version = f"<strong>Vers&atilde;o do validador: <strong class='text-gray'>{info.__version__} &ndash; {info_os_name}</strong></strong><br>"

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
