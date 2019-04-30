"""
Bbx File utilities.
"""
from __future__ import print_function

from antipathy import Path
from collections import OrderedDict
from stat import ST_MTIME
from VSS.utils import LazyAttr as lazy
import logging
import os
import re
import string

_logger = logging.getLogger('BBx')

class TableError(Exception):
    'generic problem'

class UnknownTableError(TableError):
    'unknown table format'

class MissingTableError(TableError):
    'unable to find table file'


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

# injected from fisData
tables = None

def applyfieldmap(record, fieldmap):
    if fieldmap == None:
        return record
    elif type(fieldmap) != type({}):
        raise TableError("fieldmap must be a dictionary of fieldindex[.startpos.endpos]:fieldname")
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


def unicode_strip(text=u''):
    return unicode(text).strip()

def Int(text=''):
    if not text.strip():
        return 0
    return int(float(text))

def Float(text=''):
    if not text.strip():
        return 0.0
    return float(text)

def IntFloat(text=''):
    if not text.strip():
        return 0
    try:
        return int(text)
    except ValueError:
        return float(text)


class BBxRec(object):
    # define datamap as per the iolist in the subclasses
    datamap = "iolist here".split(",")

    def __init__(self, rec, datamap, fieldlist, filename):
        self.filename = filename
        self.rec = rec
        self.datamap = [ xx.strip() for xx in datamap ]
        if fieldlist is None:
            fieldlist = []
            for fieldvar in datamap:
                fieldlist.append(None, '', None, fieldvar, None)
        self.fieldlist = fieldlist

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.rec == other.rec
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self.rec != other.rec
        return NotImplemented

    def __getitem__(self, ref):
        if isinstance(ref, (int, long)):
            ref, mask = self.fieldlist[ref][3:5]
            ref = [ref]
            masks = [mask]
            single = True
        elif isinstance(ref, slice):
            ref = [r[3] for r in self.fieldlist[ref]]
            masks = [r[4] for r in self.fieldlist[ref]]
            single = False
        else:
            ref = ref.title()
            for fld in self.fieldlist:
                if fld[3] == ref:
                    mask = fld[4]
                    break
            else:
                raise ValueError('%s is not a valid field' % ref)
            ref = [ref]
            masks = [mask]
            single = True
        result = []
        for r, m in zip(ref, masks):
            if m and ',0' in m:
                cls = Int
            elif m:
                cls = Float
            elif '$' not in r:
                cls = IntFloat
            else:
                cls = unicode_strip
            if r in self.datamap:
                var, sub = r, ''
            else:
                var, sub = (r+"(").split("(")[:2]
            try:
                varidx = self.datamap.index(var)
            except ValueError:
                raise ValueError('%s is not a valid field' % var)
            # intention: ignore missing trailing fields
            try:
                val = self.rec[varidx]
            except IndexError:
                result.append(cls())
                continue
            if sub:
                sub = sub[:-1]
                first,last = [ int(x) for x in sub.split(",") ]
                val = val[first-1:first+last-1]
            try:
                result.append(cls(val))
            except Exception:
                # _logger.error(repr(self))
                _logger.error('<%s::%s> unable to convert %r to %s, data lost' % (self.filename, r+m, val, cls.__name__))
                result.append(cls())
        if single:
            return result[0]
        return result

    def __repr__(self):
        return repr(self.rec)

    def __str__(self):
        lines = []
        field_num = 0
        last_field = None
        for i, row in enumerate(self.fieldlist):
            name, spec = row[1:4:2]
            current_field = spec.split('(')[0]
            if current_field != last_field or not current_field.endswith('$'):
                field_num += 1
                last_field = current_field
                display_field_num = '%2d' % field_num
            if '$' in spec:
                lines.append('%3d | %s | %-12s | %-*s | %s' % (i, display_field_num, spec, self._width, self[spec], name))
            else:
                lines.append('%3d | %s | %-12s | %*s | %s' % (i, display_field_num, spec, self._width, self[spec] or '-', name))
            display_field_num = '  '
        return '\n'.join(lines)

    def _calc_widths(self):
        # calculate (max) widths for printing
        widths = []
        max_width = 20
        for field_row in self.fieldlist:
            field_def = field_row[3]
            if ',' in field_def:
                # get width from spec
                width = int(field_def.split(',')[1].strip(')'))
            else:
                # get width by measurement
                width = len(unicode(self[field_def]))
            widths.append(width)
            max_width = max(max_width, width)
        self._width = max_width
        self._widths = widths

    @lazy
    def _width(self):
        self._calc_widths()
        return self._width

    @lazy
    def _widths(self):
        self._calc_widths()
        return self._widths


def getSubset(itemslist, pattern):
    # returns a sorted itemslist where keys match pattern
    import sre
    if pattern:
        itemslist = [ (xky,xrec) for (xky,xrec) in itemslist if sre.search(pattern, xky) ]
    itemslist.sort()
    return itemslist

def BBVarLength(datamap, fieldlist):
    dm_iter = iter(datamap)
    current_var = next(dm_iter)
    length = 0
    result = []
    for field in fieldlist:
        if not field[3].startswith(current_var):
            result.append(length)
            try:
                current_var = next(dm_iter)
            except StopIteration:
                return result
            length = 0
        length += field[2]
    result.append(length)
    return result

class BBxFile(object):

    def __init__(self, srcefile, datamap, fieldlist, keymatch=None, subset=None, filter=None, rectype=None, name=None, desc=None, _cache_key=None, raw=False, nulls_only=False):
        try:
            record_filename = srcefile.split('/')[-1]
            records = OrderedDict()
            datamap = [xx.strip() for xx in datamap]
            leader = trailer = None
            if rectype:
                tokens, start, stop = rectype
            if keymatch:
                first_ps = keymatch.find('%s')
                last_ps = keymatch.rfind('%s')
                if first_ps != -1:
                    leader = keymatch[:first_ps]
                if last_ps != -1:
                    trailer = keymatch[last_ps+2:]     # skip the %s ;)
            fieldlengths = BBVarLength(datamap, fieldlist)
            fixedLengthFields = set([fld[1] for fld in fieldlist if '$' in fld[3] and fld[3][-1] != '$'])
            corrupted = 0
            for ky, rec in getfile(srcefile, nulls_only=nulls_only).items():
                if ky.startswith('10YER'):
                    # this shows only four records coming from getfile()
                    pass
                if not raw:
                    if nulls_only:
                        if rectype and ky[start:stop] not in tokens:
                            continue
                    else:
                        try:
                            if (
                                len(ky) != fieldlengths[0] or
                                not ((len(datamap) - 2) <= len(rec) <= (len(datamap) + 2)) or
                                any(len(field) != length for field, length, name in
                                    zip(rec, fieldlengths, datamap) if name in fixedLengthFields
                                    ) or
                                rectype and ky[start:stop] not in tokens
                                ):
                                    continue    # record is not a match for this table
                        except:
                            raise UnknownTableError()
                rec = BBxRec(rec, datamap, fieldlist, record_filename)
                if nulls_only:
                    records[ky] = rec
                    continue
                # verify ky is present in record
                if ky != rec.rec[0]:
                    corrupted += 1
                    continue
                if filter:
                    if filter(rec):
                        records[ky] = rec
                elif leader is trailer is None and keymatch is not None:
                    if keymatch == ky:
                        records[ky] = rec
                elif leader is None or ky.startswith(leader):
                    if trailer is None or ky.endswith(trailer):
                        records[ky] = rec
            self.records = records
            self.datamap = datamap
            self.fieldlist = fieldlist
            self.keymatch  = keymatch
            self.subset  = subset
            self.rectype = rectype
            self.name = name
            self.desc= desc
            self.filename = srcefile
            self._cache_key = _cache_key
            self.corrupted = corrupted
        except TableError, exc:
            exc.filename = srcefile
            raise

    @lazy
    def field_widths(self):
        widths = [1] * len(self.fieldlist)
        for rec in self:
            for i, (w1, w2) in enumerate(zip(widths, rec._widths)):
                widths[i] = max(w1, w2)
        return widths

    def __contains__(self, ky):
        return self[ky] is not None

    def __getitem__(self, ky):
        ky = self._normalize_key(ky)
        return self.records[ky]

    def __iter__(self):
        """
        iterates through the records (all records kept during __init__, ignores subsequent keymatch settings, etc.)
        """
        return iter(self.records.values())

    def __len__(self):
        return len(self.records)

    def __repr__(self):
        pieces = []
        for attr in ('name desc keymatch subset rectype'.split()):
            value = getattr(self, attr)
            if value is not None:
                if attr is 'rectype':
                    value = value[0]
                pieces.append("%s=%r" % (attr, value))
        return "BBxFile(%s)" % (', '.join(pieces) + "[%d records]" % len(self.records))

    def _normalize_key(self, ky):
        if self.records.has_key(ky):
            return ky
        elif self.keymatch:
            if '%' in self.keymatch:
                return self.keymatch % ky
        return ky

    def get(self, ky, sentinel=None):
        ky = self._normalize_key(ky)
        try:
            return self[ky]
        except KeyError:
            return sentinel

    def get_subset(self, ky):
        if not self.subset:
            raise ValueError('subset not defined')
        if '%' in self.subset and ky:
            match = self.subset % ky
        elif '%' not in self.subset and not ky:
            match = self.subset
        else:
            raise ValueError('ky is required when using %-interpolation, and absent otherwise')
        rv = []
        for key, rec in self.records.items():
            if not key.replace('\xff', ''):
                # skipping weird record
                continue
            if key.startswith(match) or re.match(match, key):
                rv.append((key, rec))
        return rv

    def keys(self):
        return self.records.keys()

    def items(self):
        return self.records.items()

    def has_key(self, ky):
        ky = self._normalize_key(ky)
        return self.records.has_key(ky)

    def values(self):
        return self.records.values()

    def iterpattern(self, pattern=None):
        xx = getSubset(self.items(), pattern)
        return iter(xx)

    def release(self):
        'remove physical file'
        if self._cache_key in tables:
            del tables[self._cache_key]
        os.unlink(self.filename)


def getfilename(target):
    template = target.dirname / target.base
    files = Path.glob(template)
    if not files:
        template = target.dirname / target.base + '*'
        files = Path.glob(template)
        if not files:
            raise MissingTableError('unable to find any files matching %s' % template)
    possibles = []
    for file in files:
        if len(file.base) in (5, 6):
            if file.ext.lower() in ('', '.txt'):
                possibles.append(file)
    possibles.sort(key=lambda fn: fn.stat()[ST_MTIME])
    target = possibles.pop()
    return target


def getfile(filename, fieldmap=None, nulls_only=False):
    """
    Read BBx Mkeyed, Direct or Indexed file and return it as a dictionary.

    Format: target = getfile([src_dir]filename [,fieldmap = {0:'field 0 name',3:'field 3 name'})
    Notes:  The entire file is read into memory.
        Returns None on error opening file.
    """

    try:
        fh = open(filename,'rb')
        data = fh.read()
        fh.close()
    except:
        raise Exception("File not found or read/permission error: %s" % (filename, ))

    #hexdump(data)
    #raise "Breaking..."

    # handle case where filename has been converted to a simple tab-delimited text file
    if filename[-4:].lower() == '.txt':
        key_map = {}
        data = data.split('\n')
        if not data[-1]:
            data = data[:-1]
        for line in data:
            fields = line.split('\t')
            key_map[fields[0]] = fields
        return key_map

    # handle normal case of Business Basic file
    blocksize = 512
    reclen = int(asc(data[13:15]))
    reccount = int(asc(data[9:13]))
    keylen = ord(data[8])
    filetype = ord(data[7])
    report('filetype: %r' % (filetype, ))
    empty_records = 0
    keychainkeycount = 0
    keychainkeys = {}
    if filetype == 6:           # MKEYED
        ord(data[116])
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
                    keychainrec = string.split(data[keychainrecblkptr*512+keychainrecbyteptr:keychainrecblkptr*512+keychainrecbyteptr+reclen],'\n')
                    tail = keychainrec[-1]
                    if tail != '\x00' * len(tail):
                        lost_data[filename] = tail
                    if nulls_only:
                        if len(keychainrec) == 1:
                            keychainkeys[keychainkey] = keychainrec
                    # Note:  this is designed to chop off trailing nulls, but could lose data in a packed record
                    keychainrec.pop()
                    if not keychainrec:
                        empty_records += 1
                    else:
                        if keychainrec[0] != keychainkey:
                            updated_data[filename] = keychainrec[0], keychainkey
                            keychainrec[0] = keychainkey
                        keychainrec = applyfieldmap(keychainrec, fieldmap)
                        keychainkeys[keychainkey] = keychainrec
    elif filetype == 2:         # DIRECT
        seen_keys = set()
        keysperblock = ord(data[62])
        report('keys per block: %r' % keysperblock)
        #x#keyareaoffset = ord(data[50])+1
        keyareaoffset = int(asc(data[49:51]))+1
        report('key area offset: %r' % keyareaoffset)
        keyptrsize = ord(data[56])
        report('key ptr size: %r' % keyptrsize)
        nextkeyptr = int(asc(data[24:27]))
        report('next key ptr: %r' % nextkeyptr)
        netkeylen = keylen
        report('net key len: %r' % netkeylen)
        keylen = netkeylen + 3*keyptrsize
        report('key len: %r' % keylen)
        dataareaoffset = keyareaoffset + reccount / keysperblock + 1
        report('data area offset: %r' % dataareaoffset)
        while nextkeyptr > 0:
            if nextkeyptr in seen_keys:
                report('CYCLE DETECTED')
                break
            else:
                seen_keys.add(nextkeyptr)
            lastkeyinblock = not(nextkeyptr % keysperblock)
            thiskeyptr = (keyareaoffset + (nextkeyptr/keysperblock) - lastkeyinblock)*blocksize + (((nextkeyptr % keysperblock)+(lastkeyinblock*keysperblock))-1)*keylen
            keychainkey = string.split(data[thiskeyptr:thiskeyptr+netkeylen],'\0',1)[0]
            thisdataptr = dataareaoffset*blocksize + (nextkeyptr-1)*reclen
            keychainrec = string.split(data[thisdataptr:thisdataptr+reclen],'\n')
            tail = keychainrec[-1]
            if tail != '\x00' * len(tail):
                lost_data[filename] = tail
            if nulls_only:
                if len(keychainrec) == 1:
                    keychainkeys[keychainkey] = keychainrec
            # Note:  this is designed to chop off trailing nulls, but could lose data in a packed record
            keychainrec.pop()
            if not keychainrec:
                empty_records += 1
            elif not nulls_only:
                if keychainrec[0] != keychainkey:
                    updated_data[filename] = keychainrec[0], keychainkey
                    keychainrec[0] = keychainkey
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
        raise UnknownFileTypeError(filetype)
    report('%d records expected' % reccount)
    report('%d useful records found' % len(keychainkeys))
    report('%d empty records found' % empty_records)
    report('------------------------\n%d total records\n------------------------' % (len(keychainkeys)+empty_records))
    if updated_data:
        report('%d records with updated keys  (e.g. %r)' % (len(updated_data), updated_data.values()[0]))
    if lost_data:
        report('%d records with lost data  (e.g. %r)' % (len(lost_data), lost_data.values()[0]))

    return keychainkeys

class UnknownFileTypeError(Exception):
    pass

updated_data = {}
lost_data = {}

if __name__ != '__main__':
    def report(*args, **kwds):
        return
else:
    from scription import *
    report = echo

    config = '%s/config/fnx.fis.conf' % os.environ['VIRTUAL_ENV']
    ns = {'Path': Path}
    execfile(config, ns)
    DATA = ns['DATA']
    CID = ns['CID']

    @Command(
            file=Spec('file file(s) to examine', MULTI, type=unicode.upper),
            type=Spec('storage type to process', OPTION, type=int),
            )
    @Alias('bbxfile.py')
    def self_test(file, type):
        "display info about selected files"
        if file:
            data = [DATA/CID+f for f in file]
        else:
            data = DATA.glob(CID+'*')

        for file in sorted(data):
            if type:
                with open(file,'rb') as fh:
                    data = fh.read(8)
                if asc(data[7]) != type:
                    continue
            echo(file, border='flag')
            updated_data.clear()
            lost_data.clear()
            try:
                getfile(file)
            except UnknownFileTypeError:
                echo('UNKNOWN TYPE')
            echo()

    Main()
