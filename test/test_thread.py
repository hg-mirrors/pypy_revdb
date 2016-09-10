import support    # set up sys.path
from test_basic import BaseRecordingTests
from test_basic import InteractiveTests
from rpython.rtyper.lltypesystem import rffi
from rpython.rlib import rthread
from rpython.rlib import revdb

from _revdb.message import *


_sleep = rffi.llexternal('sleep', [rffi.UINT], rffi.UINT)


class TestThreadRecording(BaseRecordingTests):

    def in_parallel(self, rdb, th1, th2, geninsns1, geninsns2, final_thread):
        assert final_thread in (1, 2)

        def _switch(th2):
            got = rdb.switch_thread(expected=th2[0] if th2 else None)
            if th2:
                assert th2[0] == got
            else:
                th2.append(got)

        while geninsns1 or geninsns2:
            if rdb.is_special_packet():
                # thread switch
                _switch(th2)
                th1, th2, geninsns1, geninsns2 = th2, th1, geninsns2, geninsns1
                final_thread = 3 - final_thread
            else:
                try:
                    geninsns1.next()
                except StopIteration:
                    geninsns1 = None
        if final_thread == 2:
            _switch(th2)

    def start_thread_B(self, rdb, th_A):
        th_B_container = []

        def from_th_A():
            rdb.gil_release()
            yield
            rdb.same_stack()                   # start_new_thread returns
            x = rdb.next()                     # result is the 'th_B' id
            if th_B_container:
                assert [x] == th_B_container
            else:
                tb_B_container.append(x)

        def from_th_B():
            b = rdb.next('!h'); assert 300 <= b < 310 #"callback": start thread
            yield
            rdb.gil_acquire()
            yield
            rdb.gil_release()

        self.in_parallel(rdb, [th_A], th_B_container, from_th_A(), from_th_B(),
                         final_thread=1)
        [th_B] = th_B_container
        return th_B

    def test_thread_simple(self):
        def bootstrap():
            rthread.gc_thread_start()
            _sleep(1)
            print "BB"
            _sleep(2)
            print "BBB"
            rthread.gc_thread_die()

        def main(argv):
            print "A"
            rthread.start_new_thread(bootstrap, ())
            for i in range(2):
                _sleep(2)
                print "AAAA"
            return 9

        self.compile(main, backendopt=False, thread=True)
        out = self.run('Xx')
        # should have printed A, BB, AAAA, BBB, AAAA
        rdb = self.fetch_rdb([self.exename, 'Xx'])
        th_A = rdb.main_thread_id
        rdb.write_call("A\n")
        rdb.same_stack()      # RPyGilAllocate()

        th_B = self.start_thread_B(rdb, th_A)

        rdb.gil_acquire()
        rdb.gil_release()

        rdb.switch_thread(th_B)
        rdb.same_stack()      # sleep() (finishes here)
        rdb.next('i')         # sleep()
        rdb.gil_acquire()
        rdb.write_call("BB\n")
        rdb.gil_release()

        rdb.switch_thread(th_A)
        rdb.same_stack()      # sleep()
        rdb.next('i')         # sleep()
        rdb.gil_acquire()
        rdb.write_call("AAAA\n")
        rdb.gil_release()

        rdb.switch_thread(th_B)
        rdb.same_stack()      # sleep()
        rdb.next('i')         # sleep()
        rdb.gil_acquire()
        rdb.write_call("BBB\n")
        rdb.gil_release()

        rdb.switch_thread(th_A)
        rdb.same_stack()      # sleep()
        rdb.next('i')         # sleep()
        rdb.gil_acquire()
        rdb.write_call("AAAA\n")
        rdb.done()

    def test_threadlocal(self):
        class EC(object):
            def __init__(self, value):
                self.value = value
        raw_thread_local = rthread.ThreadLocalReference(EC)

        def bootstrap():
            rthread.gc_thread_start()
            _sleep(1)
            ec = EC(4567)
            raw_thread_local.set(ec)
            print raw_thread_local.get().value
            assert raw_thread_local.get() is ec
            rthread.gc_thread_die()

        def main(argv):
            ec = EC(12)
            raw_thread_local.set(ec)
            rthread.start_new_thread(bootstrap, ())
            _sleep(2)
            print raw_thread_local.get().value
            assert raw_thread_local.get() is ec
            return 9

        self.compile(main, backendopt=False, thread=True)
        out = self.run('Xx')
        # should have printed 4567 and 12
        rdb = self.fetch_rdb([self.exename, 'Xx'])
        th_A = rdb.main_thread_id
        rdb.same_stack()      # RPyGilAllocate()

        th_B = self.start_thread_B(rdb, th_A)

        rdb.gil_acquire()
        rdb.gil_release()

        rdb.switch_thread(th_B)
        rdb.same_stack()      # sleep() (finishes here)
        rdb.next('i')         # sleep()
        rdb.gil_acquire()
        rdb.write_call("4567\n")
        rdb.gil_release()

        rdb.switch_thread(th_A)
        rdb.same_stack()      # sleep()
        rdb.next('i')         # sleep()
        rdb.gil_acquire()
        rdb.write_call("12\n")
        rdb.done()


class TestThreadInteractive(InteractiveTests):
    expected_stop_points = 5

    def setup_class(cls):
        from test_basic import compile, run
        def bootstrap():
            rthread.gc_thread_start()
            _sleep(1)
            revdb.stop_point()
            _sleep(2)
            revdb.stop_point()
            rthread.gc_thread_die()

        def main(argv):
            revdb.stop_point()
            rthread.start_new_thread(bootstrap, ())
            for i in range(2):
                _sleep(2)
                revdb.stop_point()
            print "ok"
            return 9

        compile(cls, main, backendopt=False, thread=True)
        assert run(cls, '') == 'ok\n'

    def test_go(self):
        child = self.replay()
        for i in range(2, 6):
            child.send(Message(CMD_FORWARD, 1))
            child.expect(ANSWER_READY, i, Ellipsis,
                         (i & 1) ^ 1)    # thread number: either 0 or 1 here
        child.send(Message(CMD_FORWARD, 1))
        child.expect(ANSWER_AT_END)


class TestThreadLocal(InteractiveTests):
    expected_stop_points = 2

    def setup_class(cls):
        from test_basic import compile, run
        class EC(object):
            def __init__(self, value):
                self.value = value
        raw_thread_local = rthread.ThreadLocalReference(EC)

        def bootstrap():
            rthread.gc_thread_start()
            _sleep(1)
            ec = EC(4567)
            raw_thread_local.set(ec)
            revdb.stop_point()
            print raw_thread_local.get().value
            assert raw_thread_local.get() is ec
            rthread.gc_thread_die()

        def main(argv):
            revdb.stop_point()
            ec = EC(12)
            raw_thread_local.set(ec)
            rthread.start_new_thread(bootstrap, ())
            _sleep(2)
            print raw_thread_local.get().value
            assert raw_thread_local.get() is ec
            return 9

        compile(cls, main, backendopt=False, thread=True)
        assert run(cls, '') == '4567\n12\n'

    def test_go_threadlocal(self):
        child = self.replay()
        child.send(Message(CMD_FORWARD, 1))
        child.expect(ANSWER_READY, 2, Ellipsis, 1)
        child.send(Message(CMD_FORWARD, 1))
        child.expect(ANSWER_AT_END)
