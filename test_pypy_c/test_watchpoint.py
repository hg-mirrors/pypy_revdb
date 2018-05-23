import support


def test_watchpoint(tmpdir):
    tmpdir.join('test1.py').write(
        'lst = []\n'
        'lst.append(50)\n'
        'lst[-1] = 60\n'
        'lst.append(70)\n'
        'del lst'
    )
    rdb = support.Rdb(tmpdir, ['test1.py'])
    p_x70 = rdb.setup('> lst.append(70)\n')
    rdb.command('p lst', p_x70)
    assert '$0 = [60]\n' in rdb.before
    rdb.command('p len($0)', p_x70)
    assert '1\n' in rdb.before
    rdb.command('watch len($0)')

    p_x50 = rdb.command('bc')
    assert 'updating watchpoint value: len($0) => 0\n' in rdb.before
    assert 'Reverse-hit watchpoint 1: len($0)\n' in rdb.before
    assert '> lst.append(50)\n' in rdb.before

    p_lstdef = rdb.command('bc')
    assert ("updating watchpoint value: len($0) => RuntimeError: '$0' refers "
            "to an object created later in time\n") in rdb.before
    assert 'Reverse-hit watchpoint 1: len($0)\n' in rdb.before
    assert '> lst = []\n' in rdb.before

    rdb.command('c', p_x50)
    assert 'updating watchpoint value: len($0) => 0\n' in rdb.before
    assert 'Hit watchpoint 1: len($0)\n' in rdb.before
    assert '> lst.append(50)\n' in rdb.before

    p_x60 = rdb.command('c')
    assert 'updating watchpoint value: len($0) => 1\n' in rdb.before
    assert 'Hit watchpoint 1: len($0)\n' in rdb.before
    assert '> lst[-1] = 60\n' in rdb.before

    p_dellst = rdb.command('c')
    assert 'updating watchpoint value: len($0) => 2\n' in rdb.before
    assert 'Hit watchpoint 1: len($0)\n' in rdb.before
    assert '> del lst\n' in rdb.before

    assert 1 < p_lstdef < p_x50 < p_x60 < p_x70 < p_dellst
