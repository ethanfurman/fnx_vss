#!/usr/local/bin/python
import sys, getpass, shlex, subprocess, re, os
from bbxfile import BBxFile

FIS_SCHEMAS = "/FIS/Falcon_FIS_SCHEMA"
FIS_DATA = "/FIS/data"

# enable for text file output to compare against original output
textfiles = False

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
    if textfiles:
        file_fields = open('fields.txt.latest', 'w')
        file_iolist = open('iolist.txt.latest', 'w')
        file_tables = open('tables.txt.latest', 'w')
    iolist = None    
    contents = open(source).readlines()
    FIS_TABLES = {}
    for line in contents:
        line = line.rstrip()
        if not line:
            continue
        if line.startswith("FC"):
            if textfiles and iolist is not None:
               file_iolist.write(str(iolist) + '\n')            
            name = line[2:9].strip()
            parts = line[9:].split(" ( ")
            desc = parts[0].strip()
            filenum = int(parts[1].split()[0])
            fields = FIS_TABLES.setdefault(filenum, {'name':name, 'desc':desc, 'filenum':filenum, 'fields':[], 'iolist':[], 'key':None})['fields']
            if name in FIS_TABLES:
                del FIS_TABLES[name]    # only allow names if there aren't any duplicates
            else:
                FIS_TABLES[name] = FIS_TABLES[filenum]
            iolist = FIS_TABLES[filenum]['iolist']
        else:   # should start with a field number...
            fieldnum, fielddesc, fieldsize, rest = slicendice(line, 10, 50, 56)
            rest = rest.split()
            if not rest:
                fieldmask, fieldvar = '', 'None'
                if fielddesc.strip('()').lower() != 'open':
                    fieldvar = 'Fld%02d' % int(fieldnum)
            else:
                if '#' in rest[-1]:
                    fieldmask = rest.pop()
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
            if "(" in fieldvar and not fieldvar.endswith(")"):
                fieldvar+=")"                    
            fieldsize = int(fieldsize) if fieldsize else 0
            fields.append(["f%s_%s" % (filenum,fieldnum), fielddesc, fieldsize, fieldvar, sizefrom(fieldmask)])
            desc = fielddesc.replace(' ','').replace('-','=').lower()
            if desc.startswith(('key','keygroup','keytyp')) and desc.count('=') == 1:
                token = fielddesc.replace('-','=').split('=')[1].strip().strip('\'"')
                start, length = fieldvar.split('(')[1].strip(')').split(',')
                start, length = int(start) - 1, int(length)
                if len(token) < length:
                    length = len(token)
                stop = start + length
                FIS_TABLES[filenum]['key'] = token, start, stop
            if textfiles:
                file_fields.write(str(fields[-1]) + '\n')            
            if "$" in fieldvar:
                basevar = fieldvar.split("(")[0]
            else:
                basevar = fieldvar
            if not basevar in iolist:
                iolist.append(basevar)
    if textfiles:
        file_iolist.write(str(iolist) + '\n')
        for key, value in sorted(FIS_TABLES.items(), key=lambda kv: kv[1]['filenum']):
            file_tables.write("%-10s %5s - %-10s  %s\n" % (key, value['filenum'], value['name'], value['desc']))            
    return FIS_TABLES


DATACACHE = {}

def fisData (table, simple=None, section=None):
    key = table, simple, section
    if key in DATACACHE:
        return DATACACHE[key]
    datamap = tables[table]['iolist']
    tablename = tables[table]['name']
    key_group = tables[table]['key']
    datafile = os.sep.join([FIS_DATA,"O"+tablename[:4]])
    table = DATACACHE[key] = BBxFile(datafile, datamap, simple=simple, section=section, keygroup=keygroup)
    return table

tables = parse_FIS_Schema(FIS_SCHEMAS)

#tables['NVTY1']['fields'][77]

#NVTY = fisData(135,simple="%s101000    101**")

#vendors = fisData(65,simple='10%s')
#vendors['000099']['Gn$']
