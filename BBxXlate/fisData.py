#!/usr/local/bin/python
import os, logging
import bbxfile
from bbxfile import BBxFile, getfilename, TableError
from antipathy import Path
_logger = logging.getLogger(__name__)

# set later via execfile
CID = NUMERICAL_FIELDS_AS_TEXT = PROBLEM_TABLES = None
DATA = SCHEMA = Path()

execfile('/etc/openerp/fnx.fis.conf')

def sizefrom(mask):
    if not(mask): return ""
    fieldlen = len(mask)
    postdec = 0
    if "." in mask: postdec = len(mask.split(".")[-1])
    return "(%s,%s)" % (fieldlen,postdec)

def slicendice(line, *nums):
    results = []
    start = None
    nums += (None, )
    for num in nums:
        results.append(line[start:num].strip())
        start = num
    return tuple(results)

def parse_FIS_Schema(source):
    iolist = None
    contents = open(source).readlines()
    TABLES = {}
    skip_table = False
    for line in contents:
        line = line.rstrip()
        if not line:
            continue
        if skip_table and line[:1] == ' ':
            continue
        elif line[:1] == 'F' and line[1:2] != 'C':
            skip_table = True
            continue
        elif line[:15].strip() == '':
            continue    # skip commenting lines
        elif line.startswith(PROBLEM_TABLES):
            skip_table = True
        elif line.startswith('FC'):
            skip_table = False
            name = line[2:9].strip()
            # possible adjust name
            name = name_overrides.get(name, name)
            parts = line[9:].rsplit(" (", 1)
            desc = parts[0].strip()
            last_letter = chr(ord('A') - 1)
            if parts[1].startswith('at '):
                if name in TABLES:
                    # skip duplicate tables
                    skip_table = True
                    continue
                fields = TABLES.setdefault(name, {'name':name, 'desc':desc, 'filenum':None, 'fields':[], 'iolist':[], 'key':None})['fields']
                iolist = TABLES[name]['iolist']
                table_id = name
                filenum = ''
            else:
                filenum = int(parts[1].split()[0])
                fields = TABLES.setdefault(filenum, {'name':name, 'desc':desc, 'filenum':filenum, 'fields':[], 'iolist':[], 'key':None})['fields']

                if name in TABLES:
                    del TABLES[name]    # only allow names if there aren't any duplicates
                else:
                    TABLES[name] = TABLES[filenum]
                iolist = TABLES[filenum]['iolist']
                table_id = filenum
        else:   # should start with a field number...
            fieldnum, fielddesc, fieldsize, rest = slicendice(line, 10, 50, 56)
            rest = rest.split()
            if not rest:
                last_letter = chr(ord(last_letter) + 1)
                fieldmask, fieldvar = '', last_letter + 'n$'
                if fielddesc.strip('()').lower() == 'open':
                    # ignore line -- this fixes offset issues in 74, not sure about 5, 44, nor 147
                    continue
            else:
                if '#' in rest[-1]:
                    fieldmask = rest.pop()
                    if rest and (table_id, rest[0].lower()) in NUMERICAL_FIELDS_AS_TEXT:
                        fieldmask = ''
                    if not rest:
                        rest.append('Fld%02d' % int(fieldnum))
                else:
                    fieldmask = ''
                if len(rest) == 2:
                    fieldvar, maybe = rest
                    if '(' in maybe:
                        fieldvar = maybe
                else:
                    fieldvar = rest[0]
                fieldvar = fieldvar.title()
                last_letter = fieldvar[0]
            if "(" in fieldvar and not fieldvar.endswith(")"):
                fieldvar+=")"
            fieldvar = fieldvar.title()
            if "$" in fieldvar:
                basevar = fieldvar.split("(")[0]
            else:
                basevar = fieldvar
            basevar = basevar
            if not basevar in iolist:
                iolist.append(basevar)
            fieldsize = int(fieldsize) if fieldsize else 0
            fields.append(["f%s_%s" % (filenum,fieldnum), fielddesc, fieldsize, fieldvar, sizefrom(fieldmask)])
            desc = fielddesc.replace(' ','').replace('-','=').lower()
            if (fieldvar.startswith(iolist[0])
            and desc.startswith(('key','keygroup','keytyp','rectype','recordtype','type'))
            and desc.count('=') == 1):
                if desc.startswith('type') and '"' not in desc and "'" not in desc:
                    continue
                    # can try the below when we have records in 152
                    #
                    # start, length = fieldvar.split('(')[1].strip(')').split(',')
                    # start, length = int(start) - 1, int(length)
                    # if 'blank' in desc:
                    #     token = ' ' * length
                    # else:
                    #     token = fielddesc.replace('-','=').split('=')[1].strip('\'" ')
                    #     if ' OR ' in token:
                    #         token = tuple([t.strip('\' "') for t in token.split(' OR ')])
                else:
                    token = fielddesc.replace('-','=').split('=')[1].strip().strip('\'"')
                    start, length = fieldvar.split('(')[1].strip(')').split(',')
                    start, length = int(start) - 1, int(length)
                    if len(token) < length:
                        length = len(token)
                    stop = start + length
                if not isinstance(token, tuple):
                    token = (token, )
                TABLES[table_id]['key'] = token, start, stop
    return TABLES


DATACACHE = {}

def fisData (table, keymatch=None, subset=None, filter=None):
    table_id = tables[table]['filenum']
    if table_id is None:
        table_id = tables[table]['name']
    tablename = tables[table_id]['name']
    if tablename.startswith('CNVZ'):
        tablename = tablename[:4]
    key = table_id, keymatch, subset, filter
    try:
        datafile = getfilename(DATA/CID+tablename)
    except TableError, exc:
        exc.filename = CID+tablename
        raise
    mtime = os.stat(datafile).st_mtime
    if key in DATACACHE:
        table, old_mtime = DATACACHE[key]
        if old_mtime == mtime:
            return table
    description = tables[table_id]['desc']
    datamap = tables[table_id]['iolist']
    fieldlist = tables[table_id]['fields']
    rectype = tables[table_id]['key']
    table = BBxFile(
            datafile, datamap,
            keymatch=keymatch, subset=subset,
            filter=filter, rectype=rectype,
            fieldlist=fieldlist, name=tablename,
            desc=description, _cache_key=key,
            )
    DATACACHE[key] = table, mtime
    return table

name_overrides = {
    'ORDER': 'ORDERM',
    }

try:
    tables = parse_FIS_Schema(SCHEMA)
except IOError:
    _logger.error('unable to parse FIS Schema, unable to access FIS data')

    class tables(object):
        def __repr__(self):
            return 'FIS schema unavailable; no access to FIS data'
        def __getitem__(self, name):
            raise Exception('FIS data has not been installed')
    tables = tables()

bbxfile.tables = tables

#tables['NVTY1']['fields'][77]

#NVTY = fisData(135,keymatch="%s101000    101**")

#vendors = fisData(65,keymatch='10%s')
#vendors['000099']['Gn$']
