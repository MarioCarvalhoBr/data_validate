#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

from typing import List
from dataclasses import dataclass


@dataclass
class SpellCheckResult:
    """Resultado da verificação ortográfica"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]