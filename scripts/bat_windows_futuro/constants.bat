@echo off

REM PASTAS DE ENTRADA E SAÍDA
set INPUT_DATA=input_data
set OUTPUT_DATA=output_data
set LOG_FOLDER=log

REM Pastas com os dados de entrada
set DATA_NAMES=

for /D %%D in ("%INPUT_DATA%\*") do (
    for %%B in (%%~nxD) do (
        set DATA_NAMES=!DATA_NAMES!%%B 
    )
)
