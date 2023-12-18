import language_tool_python

def verificar_ortografia(texto):
    print('Inicializando o LanguageTool para português')
    tool = language_tool_python.LanguageTool('pt-BR')

    matches = tool.check(texto)
    erros = len(matches)

    print('Erros encontrados:', erros)
    for i, erro in enumerate(matches):
        # Imprimir a mensagem de erro
        print(f"Erro {i+1}: {erro.message}")

        # Imprimir as duas últimas linhas do erro
        erro_lines = str(erro).split('\n')
        if len(erro_lines) >= 3:
            print(erro_lines[-2])  # Linha do texto com erro
            print(erro_lines[-1])  # Indicação do erro


texto = "Exempro de texto com erros de ortografia."
verificar_ortografia(texto)