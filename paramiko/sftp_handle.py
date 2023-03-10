# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distrubuted in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

from __future__ import absolute_import

"""
Abstraction of an SFTP file handle (for server mode).
"""

import os

from .common import *
from .sftp import *


class SFTPHandle (object):
    """
    Abstract object representing a handle to an open file (or folder) in an
    SFTP server implementation.  Each handle has a string representation used
    by the client to refer to the underlying file.
    
    Server implementations can (and should) subclass SFTPHandle to implement
    features of a file handle, like L{stat} or L{chattr}.
    """
    def __init__(self, flags=0):
        """
        Create a new file handle representing a local file being served over
        SFTP.  If C{flags} is passed in, it's used to determine if the file
        is open in append mode.
        
        @param flags: optional flags as passed to L{SFTPServerInterface.open}
        @type flags: int
        """
        self.__flags = flags
        self.__name = None
        # only for handles to folders:
        self.__files = { }
        self.__tell = None

    def close(self):
        """
        When a client closes a file, this method is called on the handle.
        Normally you would use this method to close the underlying OS level
        file object(s).
        
        The default implementation checks for attributes on C{self} named
        C{readfile} and/or C{writefile}, and if either or both are present,
        their C{close()} methods are called.  This means that if you are
        using the default implementations of L{read} and L{write}, this
        method's default implementation should be fine also.
        """
        readfile = getattr(self, 'readfile', None)
        if readfile is not None:
            readfile.close()
        writefile = getattr(self, 'writefile', None)
        if writefile is not None:
            writefile.close()

    def read(self, offset, length):
        """
        Read up to C{length} bytes from this file, starting at position
        C{offset}.  The offset may be a python long, since SFTP allows it
        to be 64 bits.

        If the end of the file has been reached, this method may return an
        empty string to signify EOF, or it may also return L{SFTP_EOF}.

        The default implementation checks for an attribute on C{self} named
        C{readfile}, and if present, performs the read operation on the python
        file-like object found there.  (This is meant as a time saver for the
        common case where you are wrapping a python file object.)

        @param offset: position in the file to start reading from.
        @type offset: int or long
        @param length: number of bytes to attempt to read.
        @type length: int
        @return: data read from the file, or an SFTP error code.
        @rtype: str
        """
        readfile = getattr(self, 'readfile', None)
        if readfile is None:
            return SFTP_OP_UNSUPPORTED
        try:
            if self.__tell is None:
                self.__tell = readfile.tell()
            if offset != self.__tell:
                readfile.seek(offset)
                self.__tell = offset
            data = readfile.read(length)
        except IOError, e:
            self.__tell = None
            return SFTPServer.convert_errno(e.errno)
        self.__tell += len(data)
        return data

    def write(self, offset, data):
        """
        Write C{data} into this file at position C{offset}.  Extending the
        file past its original end is expected.  Unlike python's normal
        C{write()} methods, this method cannot do a partial write: it must
        write all of C{data} or else return an error.

        The default implementation checks for an attribute on C{self} named
        C{writefile}, and if present, performs the write operation on the
        python file-like object found there.  The attribute is named
        differently from C{readfile} to make it easy to implement read-only
        (or write-only) files, but if both attributes are present, they should
        refer to the same file.
        
        @param offset: position in the file to start reading from.
        @type offset: int or long
        @param data: data to write into the file.
        @type data: str
        @return: an SFTP error code like L{SFTP_OK}.
        """
        writefile = getattr(self, 'writefile', None)
        if writefile is None:
            return SFTP_OP_UNSUPPORTED
        try:
            # in append mode, don't care about seeking
            if (self.__flags & os.O_APPEND) == 0:
                if self.__tell is None:
                    self.__tell = writefile.tell()
                if offset != self.__tell:
                    writefile.seek(offset)
                    self.__tell = offset
            writefile.write(data)
            writefile.flush()
        except IOError, e:
            self.__tell = None
            return SFTPServer.convert_errno(e.errno)
        if self.__tell is not None:
            self.__tell += len(data)
        return SFTP_OK

    def stat(self):
        """
        Return an L{SFTPAttributes} object referring to this open file, or an
        error code.  This is equivalent to L{SFTPServerInterface.stat}, except
        it's called on an open file instead of a path.

        @return: an attributes object for the given file, or an SFTP error
            code (like L{SFTP_PERMISSION_DENIED}).
        @rtype: L{SFTPAttributes} I{or error code}
        """
        return SFTP_OP_UNSUPPORTED

    def chattr(self, attr):
        """
        Change the attributes of this file.  The C{attr} object will contain
        only those fields provided by the client in its request, so you should
        check for the presence of fields before using them.

        @param attr: the attributes to change on this file.
        @type attr: L{SFTPAttributes}
        @return: an error code like L{SFTP_OK}.
        @rtype: int
        """
        return SFTP_OP_UNSUPPORTED


    ###  internals...

    
    def _set_files(self, files):
        """
        Used by the SFTP server code to cache a directory listing.  (In
        the SFTP protocol, listing a directory is a multi-stage process
        requiring a temporary handle.)
        """
        self.__files = files

    def _get_next_files(self):
        """
        Used by the SFTP server code to retreive a cached directory
        listing.
        """
        fnlist = self.__files[:16]
        self.__files = self.__files[16:]
        return fnlist

    def _get_name(self):
        return self.__name

    def _set_name(self, name):
        self.__name = name


from .sftp_server import SFTPServer
