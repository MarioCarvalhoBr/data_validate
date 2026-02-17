#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import os
from pathlib import Path

from data_validate.config.metadata_info import METADATA

print(f"{METADATA.__welcome__}\n")

# --- CONFIGURAÇÃO ---
REPO_VERSION = METADATA.__version__

# Exemplos: "MarioCarvalhoBr/data_validate" ou "AdaptaBrasil/data_validate"
USER_REPO = "AdaptaBrasil/data_validate"
if METADATA.__status__ == METADATA.__status_dev__:
    USER_REPO = "MarioCarvalhoBr/data_validate"

# --------------------
TEMPLATE_FILE: Path = Path(__file__).resolve().parents[3] / "static" / "templates" / "README.TEMPLATE.md"
# If the file doesn't exist, raise an error
if not TEMPLATE_FILE.exists():
    raise FileNotFoundError(f"Template file not found: {TEMPLATE_FILE}")

print(f'Build README for "{USER_REPO}" - Status: {METADATA.__status__} | Version: {REPO_VERSION}')
# OUTPUT_FILE = "README.md"
OUTPUT_FILE = Path(__file__).resolve().parents[4] / "README.md"


def generate_readme():
    """
    Reads the template file, replaces the {{USER_REPO}} placeholder
    and generates the final README.TEMPLATE.md file.
    """
    try:
        # Ensures the script finds the template in the same directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, TEMPLATE_FILE)
        output_path = os.path.join(script_dir, OUTPUT_FILE)

        # Read the content of the template file
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace the placeholder with the variable value
        new_content = content.replace("{{USER_REPO}}", USER_REPO).replace("{{REPO_VERSION}}", REPO_VERSION)

        # Write the new content to the output file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"✅ Arquivo '{OUTPUT_FILE}' gerado com sucesso para o repositório '{USER_REPO}'!")

    except FileNotFoundError:
        print(f"❌ Erro: O arquivo de template '{TEMPLATE_FILE}' não foi encontrado.")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")


if __name__ == "__main__":
    generate_readme()
