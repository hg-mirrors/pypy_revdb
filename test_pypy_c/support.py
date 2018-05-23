from __future__ import print_function
import sys, os
import time
import subprocess
import pexpect


def find_executable():
    """Set up 'executable' to be the full path of a pypy executable, which
    must be translated with --revdb.  We expect to find a checkout of
    the complete rpython in the "../reverse-debugger" subdirectory,
    which could also be a symlink if you prefer.
    """
    par_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lnk = os.path.join(par_dir, 'reverse-debugger')
    if not os.path.isdir(lnk):    # possibly a symlink
        raise AssertionError(
            "these tests require ../reverse-debugger to point to "
            "a checkout of rpython in the reverse-debugger branch.")
    for version, search in [(2, os.path.join(lnk, 'pypy', 'goal', 'pypy-c')),
                            (3, os.path.join(lnk, 'pypy', 'goal', 'pypy3-c'))]:
        if os.path.isfile(search):
            return version, search
    raise AssertionError("not found: ../reverse-debugger/pypy/goal/pypy*-c")

# 'version' is the version of Python supported by pypy*-c: either 2 or 3
version, executable = find_executable()

# 'rootdir' is the full path of the '..' directory
rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def record(curdir, argv, expect_crash=False):
    env = os.environ.copy()
    logfile = 'log-%s.rdb' % (time.time(),)
    env['REVDB'] = logfile
    allargv = [executable] + argv
    exitcode = subprocess.call(allargv, cwd=str(curdir), env=env)
    if expect_crash:
        assert exitcode != 0
    else:
        assert exitcode == 0, "%s in cwd=%s returned exit code %s" % (
            allargv, str(curdir), exitcode)
    return os.path.join(str(curdir), logfile)

def spawn(curdir, argv, expect_crash=False):
    logfile = record(curdir, argv, expect_crash=expect_crash)
    cmdline = "'%s' '%s' '%s'" % (os.path.abspath(sys.executable),
                                  os.path.join(rootdir, 'revdb.py'),
                                  logfile)
    old_cwd = os.getcwd()
    try:
        os.chdir(str(curdir))
        return pexpect.spawn(cmdline, timeout=3)
    finally:
        os.chdir(old_cwd)


class Rdb:
    def __init__(self, curdir, argv, expect_crash=False):
        self.child = spawn(curdir, argv, expect_crash=expect_crash)
        self.child.expect(r'RevDB: ')
        self.child.expect(r'File ')
        self.child.expect(r'\(1\)\$ ')
        self.points = {1: 1}

    def command(self, command, go_to_point):
        self.child.sendline(command)
        self.child.expect(r'\((\d+)\)\$ ')
        self.before = self.child.before.replace('\r\n', '\n')
        new_real_pt = int(self.child.match.group(1))
        print(repr(command), '->', new_real_pt)
        if go_to_point in self.points:
            assert new_real_pt == self.points[go_to_point]
        else:
            for pt, real_pt in self.points.items():
                if pt < go_to_point:
                    assert real_pt < new_real_pt
                else:
                    assert real_pt > new_real_pt
            self.points[go_to_point] = new_real_pt
