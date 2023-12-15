from myparser import verify_sp_description_parser
from myparser import verify_structure_folder_files

# Pasta raiz
path_input = "input/espec/"
# Planilhas que serão testadas: SUCESSO
planilha_04_descricao = path_input + "4_descricao/descricao.xlsx"


def test_verify_sp_description_parser():
    message_sp_desc = verify_sp_description_parser(planilha_04_descricao)
    assert message_sp_desc == True

def test_verify_structure_folder_files():
    result = verify_structure_folder_files(path_input)
    assert result == True