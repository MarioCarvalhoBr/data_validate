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


# Lazy loading - só importa quando necessário
def get_metadata():
    """Get package metadata lazily."""
    from data_validate.config.metadata_info import METADATA

    return METADATA


# Package metadata - usando lazy loading
def __getattr__(name: str):
    """Lazy attribute access for metadata."""
    """Get package metadata lazily."""
    metadata = get_metadata()

    attr_map = {
        "__name__": "__name__",
        "__project_name__": "__project_name__",
        "__version__": "__version__",
        "__url__": "__url__",
        "__description__": "__description__",
        "__author__": "__author__",
        "__author_email__": "__author_email__",
        "__maintainer_email__": "__maintainer_email__",
        "__license__": "__license__",
        "__python_version__": "__python_version__",
        "__status__": "__status__",
        "__welcome__": "__welcome__",
    }

    if name in attr_map:
        return getattr(metadata, attr_map[name])

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
