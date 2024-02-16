import colorama
import matplotlib
import networkx
import openpyxl
import pandas
import pyarrow
import pytest
import pipreqs
    
def print_versions():
    print("\nPackages versions:")
    print("Colorama version:", colorama.__version__)
    print("Matplotlib version:", matplotlib.__version__)
    print("Networkx version:", networkx.__version__)
    print("Openpyxl version:", openpyxl.__version__)
    print("Pandas version:", pandas.__version__)
    print("Pyarrow version:", pyarrow.__version__)
    print("Pytest version:", pytest.__version__)
    print("Pipreqs version:", pipreqs.__version__)
    return True
