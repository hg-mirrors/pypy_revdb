import os
import cffi
ffibuilder = cffi.FFI()

ffibuilder.cdef("""
    int ancil_send_fds(int, const int *, unsigned);
""")

local_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(local_dir, 'fd_send.c')) as f:
    csource = f.read()

ffibuilder.set_source("_revdb._ancillary_cffi", csource,
                      include_dirs=[local_dir])

if __name__ == '__main__':
    ffibuilder.compile(verbose=True)
