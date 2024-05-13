import os
from src.util.report_generator import ReportGenerator

class TestReportGenerator:
    def setup_method(self):
        self.folder = "/tmp"
        self.template_name = "test_template.html"
        self.report_generator = ReportGenerator(self.folder, self.template_name)

    def test_init(self):
        assert self.report_generator.folder == self.folder
        assert self.report_generator.template_name == self.template_name

    def test_create_html_template(self):
        self.report_generator.create_html_template()
        assert os.path.exists(os.path.join(self.folder, self.template_name))

    def test_save_html_pdf_report(self):
        results_tests = [("Test", True, [], [])]
        self.report_generator.save_html_pdf_report("test_report", self.folder, ".html", results_tests)
        assert os.path.exists(os.path.join(self.folder, "test_report.html"))

    def test_save_pdf_report(self):
        self.report_generator.save_pdf_report(os.path.join(self.folder, "test_report.html"))
        assert os.path.exists(os.path.join(self.folder, "test_report.pdf"))

    def teardown_method(self):
        os.remove(os.path.join(self.folder, self.template_name))
        os.remove(os.path.join(self.folder, "test_report.html"))
        os.remove(os.path.join(self.folder, "test_report.pdf"))
