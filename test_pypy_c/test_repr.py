import re
import support
import pytest


@pytest.mark.parametrize("obj_input,obj_output", [
    ("10 ** 20",
        r"100000000000000000000" + ("L" if support.version == 2 else "")),
    ("[5, 6, 7]", r"\[5, 6, 7\]"),
    ("{1: 2, 3: 4, 5: 6}", r"\{1: 2, 3: 4, 5: 6\}"),
    ("A()", "<__main__.A instance at 0x[0-9a-f]+>"),
])
def test_repr_objects(obj_input, obj_output, tmpdir):
    tmpdir.join('test1.py').write(
        'class A: pass\n'
        'x = %s\n'
        'del x\n' % (obj_input,))
    rdb = support.Rdb(tmpdir, ['test1.py'])
    rdb.setup('> del x')
    rdb.command('p x')
    assert re.compile(obj_output).search(rdb.before)
