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

.. _`undodb-gdb`: http://undo.io/
.. _`rr`: http://rr-project.org/

RevDB is tested on Linux and to some extent on OS/X.  It is known *not*
to work on Windows so far.  Only Python 2.7 is implemented for now.

This is the original blog post, which describes the basics:
https://morepypy.blogspot.ch/2016/07/reverse-debugging-for-python.html


Installation
============

You need to download and build a special version of PyPy.  Sorry, there
are not prebuilt binaries at this point in time.  This is mainly because
distributing Linux binaries is a mess.  Note that the building process
takes about half an hour (which is long, but less than a normal PyPy).

* If you don't have a PyPy repository already downloaded, you can
  download directly the correct revision from
  https://bitbucket.org/pypy/pypy/downloads?tab=tags --- you need the
  latest ``RevDB-pypy2.7-vXXX`` tag, corresponding to the latest release
  of revdb.  Alternatively, if you already have a PyPy repository, make
  a local clone of it and do ``hg update RevDB-pypy2.7-vXXX``; or go to
  the development head with ``hg update reverse-debugger``.

* Make sure you have the dependencies installed:
  http://pypy.readthedocs.org/en/latest/build.html#install-build-time-dependencies

* Build the revdb version of PyPy::

    cd pypy/goal
    ../../rpython/bin/rpython -O2 --revdb

* Finally, you need to install the regular, almost-pure Python package
  https://bitbucket.org/pypy/revdb (which is where the present README
  file originally lives).  It has got a small CFFI module, so you should
  run either ``python setup.py install`` (usually in a virtualenv) or
  directly ``python setup.py build_ext --inplace``.


Usage
=====

* Here is the executable you use instead of ``pypy`` or ``python``::
    
    /path-to-reverse-debugging-pypy-repo/pypy/goal/pypy-c
    
  It works like a (slow but) regular Python interpreter, so you can
  make virtualenvs with it, or do any necessary preparation.

* **Recording:** When you are ready to run the program that you want to
  debug, use the ``REVDB`` environment variable to ask the above
  ``pypy-c`` to write a log file::

    REVDB=log.rdb  /.../pypy/goal/pypy-c  yourprogr.py  arguments...

* You can repeat the step above until you succeed in logging an
  execution that exhibits the bug that you are tracking.  Once you do,
  you get a ``log.rdb`` that we will use next.  The same ``log.rdb`` can
  be used any number of times for replaying.

* **Replaying:** Run ``/path/to/revdb/revdb.py log.rdb`` to start the
  debugger's user interface.  If you want to enable syntax coloring, add
  ``-c dark`` or ``-c light`` depending on whether you use a dark- or
  light-background terminal.

* Replaying only works if it can find the *very same* version of
  ``pypy-c``.  With that restriction, you could in theory move that
  ``log.rdb`` file on another machine and debug there, if the ``pypy-c``
  executable and associated ``libpypy-c.so`` work when copied unchanged
  on that machine too.


Debugger User Interface
=======================

The debugger user interface is a mix between gdb and pdb.  Type "help"
to get a summary of all commands.

(Write more here...)

You can get a feel for the commands by following the blog post
https://morepypy.blogspot.ch/2016/07/reverse-debugging-for-python.html
(note that many of the limitations described in that blog post have
been removed now).

Below we give some description for the least obvious but most useful
commands.

``print``

  ``print`` can run any Python code, including (single-line) statements.
  It only prints the result if it was an expression and that expression
  returns a result different from ``None``, like the interactive mode of
  Python.

``$5 =``

  Whenever a dynamic (i.e. non-prebuilt) object is printed, there is
  a numeric prefix like ``$5 =``.  You can use the expression ``$5``
  in all future Python expressions; it stands for the same object.  It
  works even if you move at a different time, as long as you don't move
  before the time where that object was created.

``break``

  ``break`` puts a breakpoint, either by line number or by function
  name.  If you say ``break foo`` or ``break foo()`` with empty
  parentheses, the breakpoint activates whenever a function with the
  name ``foo`` is called.  To set a breakpoint by line number, use
  either ``break NUM`` or ``break FILE:NUM``.  The ``FILE`` defaults to
  the ``co_filename`` of the current code object.  If given explicitly,
  it will match any code object with a ``co_filename`` of the form
  ``/any/path/FILE``.  For example, if you set a breakpoint at
  ``foo.py:42`` it will break at the line 42 in any file called
  ``/any/path/foo.py``.

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

  ``watch`` puts a watchpoint.  This command is essential to that
  debugging approach!  Watchpoints are expressions that are evaluated
  outside any context, so they must not depend on any local or global
  variable.  They can depend on builtins, and they can use ``$NUM`` to
  reference any previously-printed object.  Usually we watch ``$2.foo``
  to find where the attribute ``foo`` on this precise object ``$2``
  changed; or ``len($3)`` to find where the length of the list ``$3``
  changed.  Similarly, you can find out who changes the value of the
  global ``mod.GLOB``: first do ``print mod`` to get ``$4 =
  <module...>``; then set a watchpoint on ``$4.GLOB``.

  If you are a bit creative you can call a Python function from your
  program: first print the function itself, and then set a watchpoint
  on, say, ``$5() > 100``.  However, watchpoint expressions must be
  fully side-effect-free, otherwise replaying will get out of sync and
  crash.  (``revdb.py`` can usually recover from such crashes and let
  you continue.)

``(1500000...)``

  When ``revdb.py`` is busy moving in time, it prints the progress, for
  example as ``(1500000...)``.  If you messed up, or simply are not
  interested in it continuing searching after a while, you can safely
  press Ctrl-C to have it stop and jump back to the timestamp it was
  previously at.  This is particularly important with watchpoints,
  because they make running a lot slower.  (You should anyway delete
  watchpoints when their role has been fulfilled, but in the future we
  might cache the watchpoint results so that they are only evaluated the
  first time we go over each timestamp.)

* When tracking a complex bug, it is recommended to write down the
  timeline on a piece of paper (or separate file).  Keep it ordered by
  the timestamps of the relevant events as you find them, and write down
  which ``$NUM`` corresponds to which relevant objects.  (These ``$NUM``
  are lost if you leave and restart ``revdb.py``, though.  This might be
  changed in the future.  For now it should be easy to rebuild them
  manually by using ``go TIMESTAMP`` and repeating the ``print``
  commands.)
