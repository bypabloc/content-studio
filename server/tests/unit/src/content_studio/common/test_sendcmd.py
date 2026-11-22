from content_studio.common import sendcmd


def test_script_writes_one_order_per_line_with_six_decimals_and_a_semicolon():
    """Cada orden es `<segundos> <destino> <orden> <valor>;` en su línea, con seis decimales en el tiempo."""
    text = sendcmd.script([(0.0, 'volume@duck volume 0.5'), (0.02, 'volume@duck volume 0.4')])

    assert text == '0.000000 volume@duck volume 0.5;\n0.020000 volume@duck volume 0.4;\n'


def test_filter_path_escapes_the_drive_colon_for_a_quoted_option_value():
    """Dentro de `f='…'` el `:` de la unidad se escapa una vez, y las barras van hacia adelante."""
    assert sendcmd.filter_path('C:\\work\\follow.txt') == 'C\\:/work/follow.txt'
