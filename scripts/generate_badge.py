import subprocess
import json
import requests

def generate_coverage_report():
    # Gera .coverage e relatório de cobertura: coverage run -m pytest  -v -s
    subprocess.run(['coverage', 'run', '-m', 'pytest'])
    subprocess.run(['coverage', 'report'])
    # Gera o relatório de cobertura em formato JSON
    subprocess.run(['coverage', 'json', '-o', 'coverage.json'])

def extract_coverage_percentage():
    # Extrai a porcentagem de cobertura do relatório JSON
    with open('coverage.json') as f:
        coverage_data = json.load(f)
        total_coverage = coverage_data['totals']['percent_covered']
        # Duas casas decimais
        total_coverage = round(total_coverage, 2)
    return total_coverage

def generate_badge(coverage_percentage):
    # Gera a URL do badge usando Shields.io
    badge_url = f"https://img.shields.io/badge/coverage-{coverage_percentage}%25-brightgreen"
    print(f'Baixando badge de cobertura da URL: {badge_url}')
    return badge_url

def download_badge(badge_url, output_file='assets/images/coverage_badge.svg'):
    # Baixa o badge gerado
    response = requests.get(badge_url)
    with open(output_file, 'wb') as f:
        f.write(response.content)
    print(f"Badge de cobertura salvo como {output_file}")

def main():
    # generate_coverage_report()
    coverage_percentage = extract_coverage_percentage()
    badge_url = generate_badge(coverage_percentage)
    download_badge(badge_url)

if __name__ == "__main__":
    main()
