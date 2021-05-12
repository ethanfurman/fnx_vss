#!/usr/local/bin/python
from __future__ import print_function
import os, logging
import bbxfile
from bbxfile import BBxFile, getfilename, TableError
from antipathy import Path
import sys
_logger = logging.getLogger(__name__)

# set later via execfile
CID = NUMERICAL_FIELDS_AS_TEXT = PROBLEM_TABLES = SELF_TEST = None
DATA = SCHEMA = Path()

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
    duplicates = set()
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
            parts = line[9:].rsplit(" (", 1)
            desc = parts[0].strip()
            last_letter = chr(ord('A') - 1)
            if parts[1].startswith('at '):
                if name in TABLES:
                    if SELF_TEST:
                        print('skipping duplicate table in schema: %s' % (name, ))
                    # skip duplicate tables
                    skip_table = True
                    continue
                fields = TABLES.setdefault(name, {'name':name, 'desc':desc, 'filename':name_overrides.get(name[:4],name[:4]), 'filenum':None, 'fields':[], 'iolist':[], 'key':None})['fields']
                iolist = TABLES[name]['iolist']
                table_id = name
                filenum = ''
            else:
                filenum = int(parts[1].split()[0])
                fields = TABLES.setdefault(filenum, {'name':name, 'desc':desc, 'filename':name_overrides.get(name[:4],name[:4]), 'filenum':filenum, 'fields':[], 'iolist':[], 'key':None})['fields']

                if name in TABLES:
                    del TABLES[name]    # only allow names if there aren't any duplicates
                    duplicates.add(name)
                    if SELF_TEST:
                        print('adding table %s as %d only' % (name, filenum))
                elif name in duplicates:
                    pass
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

def fisData (table, keymatch=None, subset=None, rematch=None, filter=None, data_path=None, raw=False, nulls_only=False):
    if data_path is None:
        use_cache = True
        data_path = DATA
    else:
        use_cache = False
        data_path = Path(data_path)
    table_id = filenum = tables[table]['filenum']
    if table_id is None:
        filenum = None
        table_id = tables[table]['name']
    tablename = tables[table_id]['name']
    filename = tables[table_id]['filename']
    key = table_id, keymatch, rematch, subset, filter, raw
    diskname = file_overrides.get(CID+filename, CID+filename)
    try:
        datafile = getfilename(data_path/diskname)
    except TableError, exc:
        exc.filename = diskname
        raise
    mtime = os.stat(datafile).st_mtime
    if use_cache and key in DATACACHE:
        table, old_mtime = DATACACHE[key]
        if old_mtime == mtime:
            return table
    description = tables[table_id]['desc']
    datamap = tables[table_id]['iolist']
    fieldlist = tables[table_id]['fields']
    rectype = tables[table_id]['key']
    table = BBxFile(
            datafile, datamap,
            keymatch=keymatch, subset=subset, rematch=rematch,
            filter=filter, rectype=rectype,
            fieldlist=fieldlist, name=tablename, file_number=filenum,
            desc=description, _cache_key=key,
            raw=raw, nulls_only=nulls_only,
            )
    if use_cache:
        DATACACHE[key] = table, mtime
    return table

def setup(config):
    # SCHEMA = Path("/opt/FIS/WholeHerb_FIS_SCHEMA")
    # DATA = Path("/opt/FIS/whc_data")
    # PROBLEM_TABLES = ('FCCORE')
    # NUMERICAL_FIELDS_AS_TEXT = set([])
    # CID = 'S'
    # name_overrides = {'RDER': 'RDERM', 'CSMS':'CSMSM'}
    global tables, SCHEMA, DATA, PROBLEM_TABLES, NUMERICAL_FIELDS_AS_TEXT, CID, name_overrides, file_overrides
    ns = {'Path': Path}
    execfile(config, ns)
    SCHEMA = ns['SCHEMA']
    DATA = ns['DATA']
    PROBLEM_TABLES = ns['PROBLEM_TABLES']
    NUMERICAL_FIELDS_AS_TEXT = ns['NUMERICAL_FIELDS_AS_TEXT']
    CID = ns['CID']
    name_overrides = ns['name_overrides']
    file_overrides = ns['file_overrides']
    try:
        tables = parse_FIS_Schema(SCHEMA)
    except IOError:
        _logger.error("unable to parse FIS Schema")
        _logger.error("uid: %r, gid: %r, euid: %r, egid: %r" %
                (os.getuid(), os.getgid(), os.geteuid(), os.getegid()))
        _logger.error("args: %r" % (sys.argv, ))
        _logger.exception('unable to parse FIS Schema, unable to access FIS data')
        raise

        class tables(object):
            def __repr__(self):
                return 'FIS schema unavailable; no access to FIS data'
            def __getitem__(self, name):
                raise Exception('FIS data has not been installed')
        tables = tables()
    bbxfile.tables = tables

setup('%s/config/fnx.fis.conf' % os.environ['VIRTUAL_ENV'])

#tables['NVTY1']['fields'][77]

#NVTY = fisData(135,keymatch="%s101000    101**")

#vendors = fisData(65,keymatch='10%s')
#vendors['000099']['Gn$']


if __name__ == '__main__':
    """
    Display record counts for all tables in specified file
    missing/corrupted records.
    """
    SELF_TEST = True
    from antipathy import Path
    from scription import *
    report = echo
    virtual_env = os.environ.get('VIRTUAL_ENV')
    config = '%s/config/fnx.fis.conf' % os.environ['VIRTUAL_ENV']
    ns = {'Path': Path}
    execfile(config, ns)
    DATA = ns['DATA']
    CID = ns['CID']
    print('schema: %s' % (SCHEMA, ))
    print('data:   %s' % (DATA, ))
    print('CID:    %s' % (CID, ))
    missing_tables = {}

    updated_data = {}
    lost_data = {}

    @Command(
            file=Spec('show all tables in FILE(s)', MULTI, type=unicode.upper),
            table=Spec('only show TABLE(s)', MULTI, type=unicode.upper),
            raw=Spec('include all TABLE records in FILE', FLAG),
            nulls_only=Spec('only include null records', FLAG),
            )
    @Alias('fisdata.py')
    def self_test(file, table, raw, nulls_only):
        "display info about selected files"
        print('file: %r\ntable: %r\nraw: %r\nnulls-only: %r' % (file, table, raw, nulls_only))
        global tables
        int_keys = []
        str_keys = []
        target_tables = table
        for k in sorted(tables.keys()):
            if isinstance(k, basestring):
                str_keys.append(k)
            elif isinstance(k, (int, long)):
                int_keys.append(k)
            else:
                raise ValueError('invalid key type: %r is %r' % (k, type(k)))
        if file:
            extra_tables = tuple(t for t in str_keys if t.startswith(file))
            if not extra_tables:
                error('no tables matching %s' % ', '.join(file))
                if not target_tables:
                    abort()
            target_tables += extra_tables
        print('target tables: %r' % (target_tables, ))
        last_file = None
        last_total = 0
        for n in str_keys:
            if target_tables and n not in target_tables:
                continue
            if last_file != n[:4]:
                if last_file is not None:
                    echo('  ', '-' * 30)
                    echo('   total: %d records' % last_total)
                last_total = 0
                last_file = n[:4]
                echo(last_file, border='flag')
            table = tables.get(n)
            if not table:
                print('%s is empty' % (table, ))
                continue
            bundle = tables[n]
            name = bundle['name']
            filename = bundle['filename']
            matches = Path.glob('%s/%s%s' % (DATA, CID, filename))
            matches = [p.split('/')[-1] for p in matches]
            if not matches:
                missing_tables.setdefault(filename, []).append(name)
                continue
            test_table = fisData(n, raw=raw, nulls_only=nulls_only)
            last_total += len(test_table)
            echo('   %s: %d records' % (n, len(test_table)))
        echo('  ', '-' * 30)
        echo('   total: %d records' % last_total)
        if missing_tables:
            print('=======\nMISSING\n=======\nfile : tables\n-------------')
            for filename, tables in sorted(missing_tables.items()):
                print('%-5s: %s' % (filename, ', '.join(tables)))

    Main()
