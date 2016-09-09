import sys, os

def setup_sys_path():
    """Set up sys.path so that we can import rpython from the
    reverse-debugger branch.  We expect to find a checkout of
    the complete rpython in the "../reverse-debugger" subdirectory,
    which could also be a symlink if you prefer.
    """
    par_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lnk = os.path.join(par_dir, 'reverse-debugger')
    if not os.path.isdir(lnk):    # possibly a symlink
        raise AssertionError(
            "these tests require ../reverse-debugger to point to "
            "a checkout of rpython in the reverse-debugger branch.")
    sys.path.insert(0, '.')
    sys.path.insert(1, par_dir)
    sys.path.insert(2, lnk)
    return par_dir

parent_dir = setup_sys_path()
