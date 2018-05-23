import os
import subprocess
import support


def test_starts():
    output = subprocess.check_output([support.executable, '-c', 'print(6*7)'])
    assert output == "42\n"

    output = subprocess.check_output([support.executable, '-c', 'print(6*7)'],
                                     stderr=subprocess.STDOUT)
    assert 'starting, log file disabled' in output
    assert output.endswith("\n42\n")


def test_record(tmpdir):
    logfile = support.record(tmpdir, ['-c', 'print(6*7)'])
    assert os.path.exists(logfile)
    assert os.path.getsize(logfile) < 3*1024*1024     # currently around 624KB


def test_start_debugger(tmpdir):
    tmpdir.join('test1.py').write('x = 5 * 10\nx = 6 * 10\nx = 7 * 10\n')
    child = support.spawn(tmpdir, ['test1.py'])
    child.expect(r'RevDB: ')
    child.expect(r'File ')
    child.expect(r'\(1\)\$ ')
    #
    # go to the end
    child.sendline('c')
    child.expect(r'\((\d+)\)\$ ')
    p_end = int(child.match.group(1))
    assert 1 < p_end
    #
    # go back a few steps until the x = 7 line
    for retry in range(6):
        child.sendline('bstep')
        child.expect([r'\((\d+)\)\$ ', r'x = 7 \* 10'])
        if child.match.group() == 'x = 7 * 10':
            break
    else:
        raise AssertionError("not reaching the line 'x = 7 * 10'")
    child.expect(r'\((\d+)\)\$ ')
    p_x70 = int(child.match.group(1))
    assert 1 < p_x70 < p_end
    #
    # print the value of 'x'
    child.sendline('p x')
    child.expect(r'60')


def test_start_debugger_2(tmpdir):
    tmpdir.join('test1.py').write('x = 5 * 10\nx = 6 * 10\nx = 7 * 10\n')
    rdb = support.Rdb(tmpdir, ['test1.py'])
    p_x70 = rdb.setup('> x = 7 * 10\n')
    rdb.command('p x', p_x70)
    assert '60\n' in rdb.before
