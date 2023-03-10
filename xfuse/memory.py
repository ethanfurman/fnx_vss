#!/usr/bin/env python

from collections import defaultdict
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from sys import argv, exit
from time import time

from xfuse import FUSE, Operations, LoggingMixIn


class Example(LoggingMixIn, Operations):
    """Example memory filesystem. Supports only one level of files."""
   
    def __init__(self):
        self.files = {}
        self.data = defaultdict(str)
        self.fd = 0
        now = time()
        self.files['/'] = dict(st_mode=(S_IFDIR | 0755), st_ctime=now, st_mtime=now, st_atime=now)
       
    def chmod(self, path, mode):
        self.files[path]['st_mode'] &= 0770000
        self.files[path]['st_mode'] |= mode
        return 0

    def chown(self, path, uid, gid):
        self.files[path]['st_uid'] = uid
        self.files[path]['st_gid'] = gid
        return 0
   
    def create(self, path, mode):
        self.files[path] = dict(st_mode=(S_IFREG | mode), st_nlink=1,
                st_size=0, st_ctime=time(), st_mtime=time(), st_atime=time())
        self.fd += 1
        return self.fd
       
    def getattr(self, path, fh=None):
        if path not in self.files:
            raise OSError(ENOENT)
        st = self.files[path]
        if path == '/':
            # Add 2 for `.` and `..` , subtruct 1 for `/`
            st['st_nlink'] = len(self.files) + 1
        return st
       
    def mkdir(self, path, mode):
        self.files[path] = dict(st_mode=(S_IFDIR | mode), st_nlink=2,
                st_size=0, st_ctime=time(), st_mtime=time(), st_atime=time())
        return 0
   
    def open(self, path, flags):
        self.fd += 1
        return self.fd
   
    def read(self, path, size, offset, fh):
        return self.data[path][offset:offset + size]
   
    def readdir(self, path, fh):
        return ['.', '..'] + [x[1:] for x in self.files if x != '/']
   
    def readlink(self, path):
        return self.data[path]
   
    def rename(self, old, new):
        self.files[new] = self.files.pop(old)
        return 0
   
    def rmdir(self, path):
        self.files.pop(path)
        return 0
   
    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)
   
    def symlink(self, target, source):
        self.files[target] = dict(st_mode=(S_IFLNK | 0777), st_nlink=1, st_size=len(source))
        self.data[target] = source
        return 0
   
    def truncate(self, path, length, fh=None):
        self.data[path] = self.data[path][:length]
        self.files[path]['st_size'] = length
        return 0
   
    def unlink(self, path):
        self.files.pop(path)
        return 0
   
    def utimens(self, path, times=None):
        now = time()
        atime, mtime = times if times else (now, now)
        self.files[path]['st_atime'] = atime
        self.files[path]['st_mtime'] = mtime
        return 0
   
    def write(self, path, data, offset, fh):
        self.data[path] = self.data[path][:offset] + data
        self.files[path]['st_size'] = len(self.data[path])
        return len(data)


if __name__ == "__main__":
    if len(argv) != 2:
        print 'usage: %s <mountpoint>' % argv[0]
        exit(1)
    fuse = FUSE(Example(), argv[1], foreground=True)

