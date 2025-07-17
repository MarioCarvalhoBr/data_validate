
#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

# File: data_importer/strategies/__init__.py
"""
Pacote de estratégias de cabeçalho.
"""

from .header import HeaderStrategy, SingleHeaderStrategy, DoubleHeaderStrategy

__all__ = ["HeaderStrategy", "SingleHeaderStrategy", "DoubleHeaderStrategy"]

