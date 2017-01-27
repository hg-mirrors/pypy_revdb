===========================
RevDB, the Reverse Debugger
===========================


Introduction
============

A "reverse debugger" is a debugger where you can go forward and backward
in time.  RevDB is a reverse debugger for Python based on PyPy.  It can
be used to track down hard-to-reproduce bugs in your Python programs
(whether you usually run them on PyPy or on CPython).

It is similar to `undodb-gdb`_ and `rr`_, which are reverse debuggers
for C code.  RevDB does not allow you to step in or inspect things at
the level of C: it works purely on Python.

For more information about what reverse debugging is, have a look at
https://en.wikipedia.org/wiki/Debugger#Reverse_debugging and
http://programmers.stackexchange.com/questions/181527/why-is-reverse-debugging-rarely-used.

.. _`undodb-gdb`: http://undo.io/
.. _`rr`: http://rr-project.org/

RevDB is tested on Linux and to some extent on OS/X.  It is known *not*
to work on Windows so far.  Only Python 2.7 is implemented for now.

This is the original blog post, which describes the basics:
https://morepypy.blogspot.ch/2016/07/reverse-debugging-for-python.html
(note that many of the limitations described in that blog post have
been removed now: threads and cpyext are implemented; various crashes
have been fixed; ``next``-style commands behave more reasonably now;
``import`` in ``!`` commands is special-cased).


Installation
============

You need to download and build a special version of PyPy.  Sorry, there
are not prebuilt binaries at this point in time.  This is mainly because
distributing Linux binaries is a mess.  Note that the building process
takes 20 to 30 minutes (which is long, but less than a normal PyPy).

* If you don't have a PyPy repository already downloaded, you can
  download directly the correct revision from
  https://bitbucket.org/pypy/pypy/downloads?tab=tags --- you need the
  latest ``RevDB-pypy2.7-vXXX`` tag, corresponding to the latest release
  of revdb.  Alternatively, if you already have a PyPy repository, make
  a local clone of it and do ``hg update RevDB-pypy2.7-vXXX``; or go to
  the development head with ``hg update reverse-debugger``.

* Make sure you have the dependencies installed:
  http://pypy.readthedocs.org/en/latest/build.html#install-build-time-dependencies
  (note that for RevDB you need the Boehm garbage collector ``libgc``,
  even if you don't plan to run PyPy's tests).

* Build the revdb version of PyPy::

    cd pypy/goal
    ../../rpython/bin/rpython -O2 --revdb

* Finally, you need to install the regular, almost-pure Python package
  https://bitbucket.org/pypy/revdb (which is where the present README
  file originally lives).  It has got a small CFFI module, so you should
  run either ``python setup.py install`` (usually in a virtualenv) or
  directly ``python setup.py build_ext --inplace``.  Use a regular
  CPython 2.7.x here, or PyPy but not the RevDB version of PyPy.


Usage
=====

* Here is the executable you use instead of ``pypy`` or ``python``::
    
    /path-to-reverse-debugging-pypy-repo/pypy/goal/pypy-c
    
  It works like a (slow but) regular Python interpreter, so you can make
  virtualenvs with it, or do any necessary preparation.  You can even
  install CPython C extension modules, which will work with PyPy's
  cpyext support---which is, in itself, only a 99% solution: a few
  CPython C extension modules may not fully work in PyPy.  But if they
  work in a regular PyPy they should work with the RevDB PyPy too.

* **Recording:** When you are ready to run the program that you want to
  debug, use the ``REVDB`` environment variable to ask the above
  ``pypy-c`` to write a log file::

    REVDB=log.rdb  /.../pypy/goal/pypy-c  yourprogr.py  arguments...

  You can repeat the step above until you succeed in logging an
  execution that exhibits the bug that you are tracking.  Once you do,
  you get a ``log.rdb`` that we will use next.  The same ``log.rdb`` can
  be used any number of times for replaying.  In case of doubt, if it
  was hard to obtain, make a safe copy.

* **Replaying:** start the debugger's user interface::

    /path/to/revdb/revdb.py  log.rdb

  If you want to enable syntax coloring, add ``-c dark`` or ``-c light``
  depending on whether you use a dark- or light-background terminal (you
  need to install ``pygments``, then).

  Do not run this in the virtualenv you created in the previous step!
  This must run with a regular Python (CPython 2.7.x, or non-RevDB PyPy).

  Replaying works by having ``revdb.py`` find the ``pypy-c`` of RevDB
  and internally executing it in a special mode.  It looks at the path
  recorded in the log file (but see also the ``-x`` argument).  It must
  find the *very same* version of ``pypy-c``.  With that restriction,
  you could in theory move that ``log.rdb`` file on another machine and
  debug there, if the ``pypy-c`` executable and associated
  ``libpypy-c.so`` work when copied unchanged on that machine too.

Note that the log file typically grows at a rate of 1-2 MB per second.
Assuming size is not a problem, the limiting factor are:

1. Replaying time.  If your recorded execution took more than a few
   minutes, replaying will be painfully slow.  It sometimes needs to go
   over the whole log several times in a single session.  If the bug
   occurs randomly but rarely, you should run recording for a few
   minutes, then kill the process and try again, repeatedly until you
   get the crash.

2. RAM usage for replaying.  The RAM requirements are 10 or 15 times
   larger for replaying than for recording.  If that is too much, you
   can try with a lower value for ``MAX_SUBPROCESSES`` in
   ``_revdb/process.py``, but it will always be several times larger.


Debugger User Interface
=======================

The debugger user interface is a mix between gdb and pdb.  Type "help"
to get a summary of all commands.

(Write more here...)

You can get a feel for the commands by following the blog post
https://morepypy.blogspot.ch/2016/07/reverse-debugging-for-python.html.

Below we give some description for the least obvious but most useful
commands.

``(123456)$``

  This is the prompt, which displays the current timestamp.  The
  timestamp fully identifies the position in the log.  Use ``go`` to
  jump directly to some timestamp number.  Use ``step``/``bstep`` to do
  single-timestamp steps.  Other commands step by more, like ``next``
  and ``finish`` and their ``b`` variants.

``continue``

  This is usually the first command you give, to go to the last
  timestamp before stepping back.  A breakpoint-like "stoppoint" is set
  automatically and is always present: it activates at the time when
  execution just finished running the main module.  There are more
  recorded timestamps afterwards, particularly if PyPy is then going to
  print a traceback, but you are generally not interested in that.  So
  after you start ``revdb.py`` you typically say ``continue``, hit the
  stoppoint, and then say ``bstep`` a few times to reach the last
  interesting point (e.g. where the exception was raised, assuming there
  was one).
  
  Note another trick, useful if running tests: it's hard to go to the
  correct place if the testing framework does a lot of extra things
  after the failure occurs.  Then you can put ``os._exit(1)`` in your
  test instead of, say, the failing assert; and then when replaying,
  ``continue`` will go to that place.

``print``

  The ``print`` command can run any Python code, including (single-line)
  statements.  It only prints the result if it was an expression and
  that expression returns a result different from ``None``.  In other
  words, it works like typing at Python's interactive mode does; it does
  not work like Python's own ``print`` statement.  It is sometimes
  clearer to use ``!``, which is another abbreviation for ``print`` or
  ``p``.

``$5 =``

  Whenever a dynamic (i.e. non-prebuilt) object is printed, it is
  printed with a numeric prefix, e.g. ``$5 =``.  Afterwards, you can use
  the expression ``$5`` in all Python expressions; it stands for the
  same object.  The parser recognizes it as a standard subexpression, so
  you can say ``$5.foo`` or ``len($5)`` etc.  It continues to work after
  you move at a different time in the past or the future.  If you move
  before the time of creation for this object, using ``$5`` will raise
  an exception.  Note that the existence of ``$5`` keeps the object
  alive forever (it can be recalled even if you go far in the future),
  but this doesn't change the recorded program's own results: the
  ``__del__`` method is called, and weakrefs to ``$5`` go away, as per
  the recording.

``break``

  ``break`` puts a breakpoint, either by line number or by function
  name.  If you say ``break foo`` or ``break foo()`` with empty
  parentheses, the breakpoint activates whenever a function with the
  name ``foo`` is called.  To set a breakpoint by line number, use
  either ``break NUM`` or ``break FILE:NUM``.  The ``FILE`` defaults to
  the ``co_filename`` of the current code object.  If given explicitly,
  ``FILE`` matches any code object with a ``co_filename`` of the form
  ``/any/path/FILE``.  For example, if you set a breakpoint at
  ``foo.py:42`` it will break at the line 42 in any file called
  ``/any/path/foo.py``.  (Breakpoints cannot be conditional for now.)

``nthread, bthread``

  Multithreaded programs are handled correctly.  As usual with the GIL,
  in the recording session only one thread can run Python bytecodes at a
  time; so during replaying (i.e. now) you see bytecodes executed
  sequentially.  ``revdb.py`` displays a marker line whenever the next
  place it displays is actually from a different thread than the last.
  Typically, thread switches occur rarely.  You can use the ``nthread``
  and ``bthread`` commands to go forward or backward until a thread
  switch occurs (either going to any different thread, or going
  precisely to the thread with the given number).

``watch``

  ``watch`` puts a watchpoint.  This command is essential to RevDB's
  debugging approach!  Watchpoints are expressions that are evaluated
  outside any context, so they must not depend on any local or global
  variable.  They can depend on builtins, and they can use ``$NUM`` to
  reference any previously-printed object.  Usually we watch ``$2.foo``
  to find where the attribute ``foo`` on this precise object ``$2``
  changed; or ``len($3)`` to find where the length of the list ``$3``
  changed.  Similarly, you can find out who changes the value of the
  global ``mod.GLOB``: first do ``print mod`` to get ``$4 =
  <module...>`` and then set a watchpoint on ``$4.GLOB``.  It may
  occasionally be useful to set a watchpoint on just ``$5``: it means
  that you're watching for changes in the repr of this exact object.

  If you are a bit creative you can call a Python function from your
  program: first print the function itself, and then set a watchpoint
  on, say, ``$6() > 100``.  However, watchpoint expressions must be
  fully side-effect-free, otherwise replaying will get out of sync and
  crash.  (``revdb.py`` can usually recover from such crashes and let
  you continue.)

More notes:

* When ``revdb.py`` is busy moving in time, it prints the progress, for
  example as ``(1500000...)``.  If you messed up, or simply are not
  interested in it continuing searching after a while, you can safely
  press Ctrl-C to have it stop and jump back to the timestamp it was
  previously at.  This is particularly important with watchpoints,
  because they make running a lot slower.  (You should anyway delete
  watchpoints when their role has been fulfilled, but in the future we
  might cache the watchpoint results so that they are only evaluated the
  first time we go over each timestamp.)

* Setting a watchpoint or printing a ``$NUM`` in the past requires
  a rescan of the log file from the time of creation of that object
  (once).  If ``$NUM`` is an object created very early in the process,
  you will have to wait (or use Ctrl-C).

* When tracking a complex bug, it is recommended to write down the
  timeline on a piece of paper (or separate file).  Make sure you write
  the timestamp for every event you record, and keep the log ordered by
  timestamp.  Write down which ``$NUM`` corresponds to the relevant
  objects.  All the timestamps that you write down are still valid if
  you leave and restart ``revdb.py``.  The ``$NUM`` are not, though.
  (This might be changed in the future.  For now it should be easy to
  rebuild them manually by using ``go TIMESTAMP`` and repeating the
  ``print`` commands.)


Contact information
===================

IRC: #pypy on irc.freenode.net

Mailing list: pypy-dev@python.org

You can report issues in the `issue tracker`__ of RevDB.

.. __: https://bitbucket.org/pypy/revdb/issues?status=new&status=open

RevDB is made by Armin Rigo, but thanks go to the rest of the PyPy team
as well.
