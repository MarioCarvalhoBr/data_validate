@echo off
REM Importa o arquivo de constantes usando o caminho do diretório do script
set SCRIPT_DIR=%~dp0
call "%SCRIPT_DIR%constants.bat"

echo Executando verificações...

for %%F in (%DATA_NAMES%) do (
    if exist "%INPUT_DATA%\%%F" (
        echo.
        echo Processando a pasta "%INPUT_DATA%\%%F"...
        
        python main.py --input_folder="%INPUT_DATA%\%%F" --output_folder="%OUTPUT_DATA%\%%F" --debug --no-time --no-version --sector="Setor A" --protocol="Protocolo B" --user="Usuário C"
        
        if "%%F"=="data_errors_01" (
            echo Processando a pasta "%%F" com a flag --no-warning-titles-length...
            python main.py --input_folder="%INPUT_DATA%\%%F" --output_folder="%OUTPUT_DATA%\%%F" --debug --no-warning-titles-length --no-time --no-version --sector="Setor A" --protocol="Protocolo B" --user="Usuário C"
        )
    ) else (
        echo A pasta "%INPUT_DATA%\%%F" não existe.
    )
)

echo Verificações concluídas
