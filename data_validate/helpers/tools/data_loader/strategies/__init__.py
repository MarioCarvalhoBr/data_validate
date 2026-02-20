#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/strategies/__init__.py
"""
Pacote de estratégias de cabeçalho.
"""

from .header import HeaderStrategy, SingleHeaderStrategy, DoubleHeaderStrategy

__all__ = ["HeaderStrategy", "SingleHeaderStrategy", "DoubleHeaderStrategy"]
