from ._ancillary_cffi import ffi, lib

def send_fds(pipe_num, fd_list):
    if lib.ancil_send_fds(pipe_num, fd_list, len(fd_list)) < 0:
        raise OSError(ffi.errno, "ancil_send_fds() failed")
