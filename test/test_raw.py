import os, subprocess

import support    # set up sys.path
from rpython.rlib import revdb
from rpython.rtyper.lltypesystem import lltype
from test_basic import InteractiveTests

from _revdb.message import *


class TestReplayingRaw(InteractiveTests):
    expected_stop_points = 1

    def setup_class(cls):
        from test_basic import compile, run
        from test_basic import fetch_rdb

        FOO = lltype.Struct('FOO')
        foo = lltype.malloc(FOO, flavor='raw', immortal=True)

        BAR = lltype.Struct('BAR', ('p', lltype.Ptr(FOO)))
        bar = lltype.malloc(BAR, flavor='raw', immortal=True)
        bar.p = foo

        BAZ = lltype.Struct('BAZ', ('p', lltype.Ptr(FOO)), ('q', lltype.Signed),
                            hints={'union': True})
        baz = lltype.malloc(BAZ, flavor='raw', immortal=True)
        baz.p = foo

        VBAR = lltype.Array(lltype.Ptr(FOO))
        vbar = lltype.malloc(VBAR, 3, flavor='raw', immortal=True)
        vbar[0] = vbar[1] = vbar[2] = foo

        RECBAR = lltype.Struct('RECBAR', ('super', BAR), ('q', lltype.Ptr(FOO)))
        recbar = lltype.malloc(RECBAR, flavor='raw', immortal=True)
        recbar.q = foo
        recbar.super.p = foo

        IBAR = lltype.Struct('IBAR', ('p', lltype.Ptr(FOO)),
                             hints={'static_immutable': True})
        ibar = lltype.malloc(IBAR, flavor='raw', immortal=True)
        ibar.p = foo

        BARI = lltype.Struct('BARI', ('b', lltype.Ptr(IBAR)))
        bari = lltype.malloc(BARI, flavor='raw', immortal=True)
        bari.b = ibar

        class X:
            pass
        x = X()
        x.foo = foo
        x.ibar = ibar
        x.bari = bari

        def main(argv):
            assert bar.p == foo
            assert baz.p == foo
            for i in range(3):
                assert vbar[i] == foo
            assert recbar.q == foo
            assert recbar.super.p == foo
            assert ibar.p == foo
            assert bari.b == ibar
            assert x.foo == foo
            assert x.ibar == ibar
            assert x.bari == bari
            revdb.stop_point()
            return 9

        compile(cls, main, backendopt=False, shared=True)
        run(cls, '')
        rdb = fetch_rdb(cls, [cls.exename])
        #assert len(rdb.rdb_struct) >= 4

    def test_replaying_raw(self):
        # This tiny test seems to always have foo at the same address
        # in multiple runs.  Here we recompile with different options
        # just to change that address.
        #
        # NOTE: not supported right now!  The executable must be
        # exactly the same one with the same raw addresses.  This
        # might be fixed in the future.
        #subprocess.check_call(["make", "clean"],
        #                      cwd=os.path.dirname(str(self.exename)))
        #subprocess.check_call(["make", "lldebug"],
        #                      cwd=os.path.dirname(str(self.exename)))
        #
        child = self.replay()
        child.send(Message(CMD_FORWARD, 2))
        child.expect(ANSWER_AT_END)
