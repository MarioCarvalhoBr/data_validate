"""
# Adapta Parser

Esta é a descrição principal do projeto Adapta Parser.
Aqui você pode adicionar informações como:

- Uma visão geral do projeto.
- Como instalar e usar.
- Exemplos de uso.
- Informações de licença.

Você pode até usar formatação Markdown básica aqui,
embora o suporte possa variar dependendo da versão do pdoc.
"""

from data_validate.helpers.base.metadata_info import METADATA

# Package metadata
__name__ = METADATA.__name__
__project_name__ = METADATA.__project_name__
__version__ = METADATA.__version__
__url__ = METADATA.__url__
__description__ = METADATA.__description__
__author__ = METADATA.__author__
__author_email__ = METADATA.__author_email__
__maintainer_email__ = METADATA.__maintainer_email__
__license__ = METADATA.__license__
__python__ = METADATA.__python__
__python_version__ = METADATA.__python_version__
__status__ = METADATA.__status__

print(f"The {__project_name__} {__name__} version {__version__} initialized.\n")
