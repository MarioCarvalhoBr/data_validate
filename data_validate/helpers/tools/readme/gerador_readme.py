#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import os
from pathlib import Path

from data_validate import METADATA

# --- CONFIGURAÇÃO ---
REPO_VERSION = METADATA.__version__

# Exemplos: "MarioCarvalhoBr/data_validate" ou "AdaptaBrasil/data_validate"
USER_REPO = "AdaptaBrasil/data_validate"
if METADATA.__status__ == METADATA.__text_dev__:
    USER_REPO = "MarioCarvalhoBr/data_validate"

# --------------------
TEMPLATE_FILE: Path = (
    Path(__file__).resolve().parents[3] / "static" / "templates" / "README.TEMPLATE.md"
)
# Se o arquivo não existir, lança um erro
if not TEMPLATE_FILE.exists():
    raise FileNotFoundError(f"Template file not found: {TEMPLATE_FILE}")

print(f'Build README for "{USER_REPO}" - Status: {METADATA.__status__} | Version: {REPO_VERSION}')
# OUTPUT_FILE = "README.md"
OUTPUT_FILE = Path(__file__).resolve().parents[4] / "README.md"

def generate_readme():
    """
    Lê o arquivo de template, substitui o placeholder {{USER_REPO}}
    e gera o arquivo README.TEMPLATE.md final.
    """
    try:
        # Garante que o script encontre o template no mesmo diretório
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, TEMPLATE_FILE)
        output_path = os.path.join(script_dir, OUTPUT_FILE)

        # Lê o conteúdo do arquivo de template
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Substitui o placeholder pelo valor da variável
        new_content = content.replace("{{USER_REPO}}", USER_REPO).replace("{{REPO_VERSION}}", REPO_VERSION)

        # Escreve o novo conteúdo no arquivo de saída
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(
            f"✅ Arquivo '{OUTPUT_FILE}' gerado com sucesso para o repositório '{USER_REPO}'!"
        )

    except FileNotFoundError:
        print(f"❌ Erro: O arquivo de template '{TEMPLATE_FILE}' não foi encontrado.")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    generate_readme()
