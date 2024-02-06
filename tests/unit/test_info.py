import src.myparser.info as lv

def test_verstion():
    ret = lv.print_versions()
    assert ret is True