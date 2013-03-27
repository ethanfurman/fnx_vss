"""
Bbx File utilities.
"""

import os, string

def asc(strval):                    ##USED in bbxfile
    if len(strval) == 0:
        return 0
    elif len(strval) == 1:
        try:
            return ord(strval)
        except:
            return long(ord(strval))
    else:
        return 256L*(asc(strval[:-1]))+ord(strval[-1])


def applyfieldmap(record, fieldmap):
    if fieldmap == None:
        return record
    elif type(fieldmap) != type({}):
        raise FieldMapTypeError, "FieldMap must be a dictionary of fieldindex[.startpos.endpos]:fieldname"
    retval = {}
    fieldmapkeys = fieldmap.keys()
    fieldmapkeys.sort()
    for item in fieldmapkeys:
        fieldparams = string.split(item,".")
        field = int(fieldparams[0])
        startpos = endpos = ''
        if len(fieldparams) > 1:
            startpos = fieldparams[1]
        if len(fieldparams) == 3:
            endpos = fieldparams[2]
        fieldeval = `record[field]` + '['+startpos+":"+endpos+']'
        retval[fieldmap[item]] = eval(fieldeval)
    return retval


class BBxRec:
    # define datamap as per the iolist in the subclasses
    datamap = "iolist here".split(",")
    def __init__(self, rec, datamap):
        self.rec = rec
        self.datamap = [ xx.strip() for xx in datamap ]
    def __getitem__(self, ref):
        if ref in self.datamap:
            var, sub = ref, ''
        else:
            var, sub = (ref+"(").split("(")[:2]
        varidx = self.datamap.index(var)
        if varidx < len(self.rec):
            val = self.rec[varidx]
        else:
            val = None
        if sub:
            sub = sub[:-1]
            first,last = [ int(x) for x in sub.split(",") ]
            #print val,first,last
            val = val[first-1:first+last-1]
        return val
    def __setitem__(self, ref, newval):
        var, sub = (ref+"(").split("(")[:2]
        varidx = self.datamap.index(var)
        if varidx < len(self.rec):
            val = self.rec[varidx]
        else:
            val = None
        if sub:
            sub = sub[:-1]
            first,last = [ int(x) for x in sub.split(",") ]
            #print val,first,last
            val = val[first-1:first+last-1]
            self.rec[varidx][first-1:first+last-1] = newval
        else:
            self.rec[varidx] = newval


def getSubset(itemslist, pattern):
    # returns a sorted itemslist where keys match pattern
    import sre
    if pattern:
        itemslist = [ (xky,xrec) for (xky,xrec) in itemslist if sre.search(pattern, xky) ]
    itemslist.sort()
    return itemslist


class BBxFile:
    def __init__(self, srcefile, datamap, simple=None, subset=None, section=None):
        records = {}
        datamap = [xx.strip() for xx in datamap]
        leader = trailer = None
        if simple:
            first_ps = simple.find('%s')
            last_ps = simple.rfind('%s')
            if first_ps != -1:
                leader = simple[:first_ps]
            if last_ps != -1:
                trailer = simple[last_ps+2:]     # skip the %s ;)
        if (section is not None
        and not section.startswith(leader)
        and not leader.startswith(section)):
            raise ValueError('no common records between section %r and leader %r' % (section, leader))
        for ky, rec in getfile(srcefile).items():
            if section is None or ky.startswith(section):
                if trailer is None or ky.endswith(trailer):
                    records[ky] = BBxRec(rec, datamap)
        self.records = records
        self.datamap = datamap
        self.simple  = simple
        self.subset  = subset
        self.section = section
    def get_item_or_single(self,ky):
        if self.records.has_key(ky):
            return self.records[ky]
        elif self.simple:
            if self.records.has_key(self.simple % ky):
                return self.records[self.simple % ky]
    def __getitem__(self, ky):
        rv = self.get_item_or_single(ky)
        if rv:
            return rv
        elif self.subset:
            match = self.subset % ky
            rv = [ (xky,xrec) for (xky,xrec) in self.records.items() if xky.startswith(match) ]
            rv.sort()
            return rv
    def __contains__(self, ky):
        #import pdb; pdb.set_trace()
        return self.get_item_or_single(ky)
    def __len__(self):
        return len(self.records)
    def keys(self):
        return self.records.keys()
    def items(self):
        return self.records.items()
    def has_key(self,ky):
        #print 'testing for %s ' % ky
        return not not self[ky]
    def iterpattern(self, pattern=None):
        xx = getSubset(self.items(), pattern)
        return iter(xx)


def getfile(filename = None, fieldmap = None):
    """
Read BBx Mkeyed, Direct or Indexed file and return it as a dictionary.

Format: target = getfile([src_dir]filename [,fieldmap = {0:'field 0 name',3:'field 3 name'})
Notes:  The entire file is read into memory.
        Returns None on error opening file.
    """
    default_file = r'C:\Zope\v2.4\Extensions\WSGSourceData\ICCXF0'

    default_srce_loc, default_filename = os.path.split(default_file)
    if filename:
        srce_loc, filename = os.path.split(filename)
        if srce_loc == '': srce_loc = default_srce_loc
    else:
        srce_loc, filename = os.path.split(default_file)

    try:
        data = open(filename,'rb').read()
    except:
        try:
            data = open(srce_loc + os.sep + filename,'rb').read()
        except:
            print "(srce_loc, filename)", (srce_loc, filename)
            raise "File not found or read/permission error.", (srce_loc, filename)

    #hexdump(data)
    #raise "Breaking..."

    blocksize = 512
    reclen = int(asc(data[13:15]))
    reccount = int(asc(data[9:13]))
    keylen = ord(data[8])
    filetype = ord(data[7])
    keychainkeycount = 0
    keychainkeys = {}
    if filetype == 6:           # MKEYED
        blockingfactor = ord(data[116])
        for fblock in range(0,len(data),blocksize):         # sniff out a key block...
            if data[fblock] != '\0' \
              and data[fblock+1] == '\0' \
              and data[fblock+5] != '\0':
                keysinthiskeyblock = ord(data[fblock])      # ... then parse and follow the links to the records
                keychainkeycount = keychainkeycount + keysinthiskeyblock
                for thiskey in range(fblock+5,fblock+5+keysinthiskeyblock*(keylen+8),keylen+8):
                    keychainkey =  string.split(data[thiskey:thiskey+keylen],'\0',1)[0]
                    keychainrecblkptr = int(asc(data[thiskey+keylen:thiskey+keylen+3]) / 2)
                    keychainrecbyteptr = int(256*(asc(data[thiskey+keylen:thiskey+keylen+3]) % 2) + ord(data[thiskey+keylen+3]))
                    keychainrec = string.split(data[keychainrecblkptr*512+keychainrecbyteptr:keychainrecblkptr*512+keychainrecbyteptr+reclen],'\n')[:-1]
                    # Note:  The trailing [:-1] on the preceeding line is to chop off trailing nulls.  This could lose data in a packed record
                    if keychainrec:
                        if keychainrec[0] == '': keychainrec[0] = keychainkey
                        keychainrec = applyfieldmap(keychainrec, fieldmap)
                        keychainkeys[keychainkey] = keychainrec
    elif filetype == 2:         # DIRECT
        keysperblock = ord(data[62])
        #x#keyareaoffset = ord(data[50])+1
        keyareaoffset = int(asc(data[49:51]))+1
        keyptrsize = ord(data[56])
        nextkeyptr = int(asc(data[24:27]))
        netkeylen = keylen
        keylen = netkeylen + 3*keyptrsize
        dataareaoffset = keyareaoffset + reccount / keysperblock + 1
        while nextkeyptr > 0:
            lastkeyinblock = not(nextkeyptr % keysperblock)
            thiskeyptr = (keyareaoffset + (nextkeyptr/keysperblock) - lastkeyinblock)*blocksize + (((nextkeyptr % keysperblock)+(lastkeyinblock*keysperblock))-1)*keylen
            keychainkey = string.split(data[thiskeyptr:thiskeyptr+netkeylen],'\0',1)[0]
            thisdataptr = dataareaoffset*blocksize + (nextkeyptr-1)*reclen
            keychainrec = string.split(data[thisdataptr:thisdataptr+reclen],'\n')[:-1]
            # Note:  The trailing [:-1] on the preceeding line is to chop off trailing nulls.  This could lose data in a packed record
            if keychainrec:
                if keychainrec[0] == '': keychainrec[0] = keychainkey
                keychainrec = applyfieldmap(keychainrec, fieldmap)
                keychainkeys[keychainkey] = keychainrec
            nextkeyptr = int(asc(data[thiskeyptr+netkeylen:thiskeyptr+netkeylen+keyptrsize]))
            keychainkeycount = keychainkeycount + 1
    elif filetype == 0:         # INDEXED
        for i in range(15, reccount*reclen, reclen):
            keychainrec = string.split(data[i:i+reclen],'\n')[:-1]
            keychainrec = applyfieldmap(keychainrec, fieldmap)
            keychainkeys[keychainkeycount] = keychainrec
            keychainkeycount = keychainkeycount + 1
    else:
        #hexdump(data)
        raise "UnknownFileTypeError", (filetype)
    return keychainkeys

if __name__ == '__main__':
    import time
    #print "Starting..."
    #for fn in ("ICIMF0","GMCMF0","GMAFF0","GMCFF0"):   # "ICCXF0",
    #    start = time.time()
    #    print fn, len(getfile(fn)), time.time()-start
    #start = time.time()
    #print "ICCXXF", len(open(r'C:\Zope\v2.4\Extensions\WSGSourceData\ICCXXF', 'rb').read()), time.time()-start
    
