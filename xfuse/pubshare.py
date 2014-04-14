#!/usr/bin/env python

from errno import EACCES, ENOENT
from os.path import realpath
from sys import argv, exit
from threading import Lock
from collections import defaultdict
from stat import S_IFDIR, S_IFLNK, S_IFREG
from time import time

import os

from fenx.xfuse import FUSE, FuseOSError, Operations, LoggingMixIn

class fnxFs(LoggingMixIn, Operations): 


class Loopback(LoggingMixIn, Operations):    
    def __init__(self, root):
        self.root = realpath(root)
        self.rwlock = Lock()
   
    def __call__(self, op, path, *args):
        return super(Loopback, self).__call__(op, self.root + path, *args)
   
    def access(self, path, mode):
        if not os.access(path, mode):
            raise FuseOSError(EACCES)
   
    chmod = os.chmod
    chown = os.chown
   
    def create(self, path, mode):
        return os.open(path, os.O_WRONLY | os.O_CREAT, mode)
   
    def flush(self, path, fh):
        return os.fsync(fh)
   
    def fsync(self, path, datasync, fh):
        return os.fsync(fh)
   
    def getattr(self, path, fh=None):
        st = os.lstat(path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
            'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
   
    getxattr = None
   
    def link(self, target, source):
        return os.link(source, target)
   
    listxattr = None
    mkdir = os.mkdir
    mknod = os.mknod
    open = os.open
   
    def read(self, path, size, offset, fh):
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.read(fh, size)
   
    def readdir(self, path, fh):
        pathdir = os.listdir(path)
        userdir = []
        for pathd in pathdir:
            try:
                name = os.path.basename(os.readlink(pathd))
            except:
                name = pathd
            userdir.append(name)
        return ['.', '..'] + userdir

    xreadlink = os.readlink
    def readlink(self, path):
        #import pdb; pdb.set_trace()
        #print "in readlink with path=%s and basename=%s" % (path, os.path.basename(os.readlink(path)))
        #return os.path.basename(os.readlink(path))
        return ""
   
    def release(self, path, fh):
        return os.close(fh)
       
    def rename(self, old, new):
        return os.rename(old, self.root + new)
   
    rmdir = os.rmdir
   
    def statfs(self, path):
        stv = os.statvfs(path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))
   
    def symlink(self, target, source):
        return os.symlink(source, target)
   
    def truncate(self, path, length, fh=None):
        with open(path, 'r+') as f:
            f.truncate(length)
   
    unlink = os.unlink
    utimens = os.utime
   
    def write(self, path, data, offset, fh):
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.write(fh, data)


class Memory(LoggingMixIn, Operations):
    """Example memory filesystem. Supports only one level of files."""
   
    def __init__(self):
        self.files = {}
        self.data = defaultdict(str)
        self.fd = 0
        now = time()
        for ii in ["","11-39","11-31","11-100","11-82"]:
            self.files['/%s' % ii] = dict(st_mode=(S_IFDIR | 0755), st_ctime=now, st_mtime=now, st_atime=now)
       
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
    if len(argv) == 3:
        fuse = FUSE(Loopback(argv[1]), argv[2], foreground=True)
    elif len(argv) == 2:
        fuse = FUSE(Memory(), argv[1], foreground=True)
    print 'loopback usage: %s <root> <mountpoint>\n         memory usage: %s <mountpoint>' % (argv[0],argv[0])
    exit(1)
