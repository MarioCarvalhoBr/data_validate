import colorama
import matplotlib
import networkx
import openpyxl
import pandas
import pyarrow
import pytest
import pipreqs
import coverage
from pre_commit import constants as pre_commit
import datetime
import setuptools
import genbadge
import chardet
import pdfkit

def print_versions():
    print("\nPACKAGES VERSIONS: ")
    print("Colorama version:", colorama.__version__)
    print("Matplotlib version:", matplotlib.__version__)
    print("Networkx version:", networkx.__version__)
    print("Openpyxl version:", openpyxl.__version__)
    print("Pandas version:", pandas.__version__)
    print("Pyarrow version:", pyarrow.__version__)
    print("Pytest version:", pytest.__version__)
    print("Pipreqs version:", pipreqs.__version__)
    print("Coverage version:", coverage.__version__)
    print("Pre-commit version:", pre_commit.VERSION)
    print("Setuptools version:", setuptools.__version__)
    print("Genbadge version:", genbadge.__version__)
    print("CharDet Version: ", chardet.__version__)
    print("PDFKit Version: ", pdfkit.__version__)
    
    return True

# Informações da ferramenta

__name__ = "Canoa"
__version__ = "0.5.03"

__author__ = "Mário de Araújo Carvalho"
__email__ = "mariodearaujocarvalho@gmail.com"

__description__ = "A simple parser for Canoa project"
__url__ = "https://github.com/AdaptaBrasil/data_validate"
__license__ = "MIT"

__status__ = "Development"

__python_version__ = "3.12"
__packages__ = ["colorama", "matplotlib", "networkx", "openpyxl", "pandas", "pyarrow", "pytest", "pipreqs", "coverage", "pre_commit"]

# UTILS
__date_now__ = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
