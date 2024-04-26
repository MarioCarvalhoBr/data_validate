import colorama
import matplotlib
import networkx
import openpyxl
import pandas
import pyarrow
import pytest
import pipreqs
import coverage
import pre_commit
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
    print("Coverage version:", coverage.__version__)
    print("Pre-commit version:", pre_commit)
    return True


# Cre uma classe para arvore binária
class Node:
    def __init__(self, data):
        self.left = None
        self.right = None
        self.data = data

    def insert(self, data):
        if self.data:
            if data < self.data:
                if self.left is None:
                    self.left = Node(data)
                else:
                    self.left.insert(data)
            elif data > self.data:
                if self.right is None:
                    self.right = Node(data)
                else:
                    self.right.insert(data)
        else:
            self.data = data

    def print_tree(self):
        if self.left:
            self.left.print_tree()
        print(self.data)
        if self.right:
            self.right.print_tree()
