"""Publish a completed file on its own filesystem without replacing another writer's file."""

import errno
import os
import sys


def publish_new(source, destination):
    if os.name == "nt":
        os.rename(source, destination)
        return
    try:
        os.link(source, destination)
        return
    except OSError as error:
        if error.errno not in (errno.EPERM, errno.EOPNOTSUPP, errno.ENOSYS):
            raise
        # FAT and some network volumes have no hard links. Use the native
        # exclusive rename where the operating system provides it.
        import ctypes
        libc = ctypes.CDLL(None, use_errno=True)
        if sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
            at_fdcwd = -100
            result = libc.renameat2(at_fdcwd, os.fsencode(source), at_fdcwd,
                                    os.fsencode(destination), 1)  # RENAME_NOREPLACE
        elif sys.platform == "darwin" and hasattr(libc, "renamex_np"):
            result = libc.renamex_np(os.fsencode(source), os.fsencode(destination), 4)  # RENAME_EXCL
        else:
            raise
        if result:
            code = ctypes.get_errno()
            raise OSError(code, os.strerror(code), destination)
