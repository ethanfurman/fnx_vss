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
Compression implementations for a Transport.
"""

import zlib


class ZlibCompressor (object):
    def __init__(self):
        self.z = zlib.compressobj(9)

    def __call__(self, data):
        return self.z.compress(data) + self.z.flush(zlib.Z_FULL_FLUSH)


class ZlibDecompressor (object):
    def __init__(self):
        self.z = zlib.decompressobj()

    def __call__(self, data):
        return self.z.decompress(data)
