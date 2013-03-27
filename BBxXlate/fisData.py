#!/usr/local/bin/python
import sys, getpass, shlex, subprocess, re, os
from fenx.BBxXlate.bbxfile import BBxFile

FIS_SCHEMAS = "/FIS/Falcon_FIS_SCHEMA"
FIS_DATA = "/FIS/data"

def sizefrom(mask):
    if not(mask): return ""
    fieldlen = len(mask)
    postdec = 0
    if "." in mask: postdec = len(mask.split(".")[-1])
    return "(%s,%s)" % (fieldlen,postdec)


def parse_FIS_Schema(source):
    contents = open(source).readlines()
    FIS_TABLES = {}
    for line in [ii for ii in contents if ii.strip()]:
        if line.startswith("FC"):
            name = line[2:9].strip()
            parts = line[9:].split(" ( ")
            desc = parts[0].strip()
            filenum = int(parts[1].split()[0])
            fields = FIS_TABLES.setdefault(name,{'name':name,'desc':desc,'filenum':filenum,'fields':[],'iolist':[]})['fields']
            iolist = FIS_TABLES[name]['iolist']
            FIS_TABLES[filenum] = FIS_TABLES[name]
            #print name,filenum,'  ==>'
        elif line.startswith("          "):
            continue
        else:   # should start with a field number...
            #print line
            if len(line)>56:
                fieldvar,fieldmask = line[56:].split()[0].strip(),line[56:].split()[-1]
                if fieldvar == fieldmask: fieldmask = ""
                fieldnum,fielddesc,fieldsize = line[:10].strip(),line[10:50].strip(),line[50:56].strip()
            else:
                fieldnum,fielddesc,fieldsize,fieldvar = line[:10].strip(),line[10:50].strip(),line[50:56].strip(),"None"
            if "(" in fieldvar and not fieldvar.endswith(")"):
                fieldvar+=")"
            #print " --> ",fieldnum,fielddesc,fieldsize,fieldvar,fieldmask
            if not(fieldsize): fieldsize = "0"
            fields.append(["f%s_%s" % (filenum,fieldnum),fielddesc,int(fieldsize),fieldvar,sizefrom(fieldmask)])
            if "$" in fieldvar: basevar = fieldvar.split("(")[0]
            else: basevar = fieldvar
            if not basevar in iolist: iolist.append(basevar)
    return FIS_TABLES


DATACACHE = {}

def fisData (table,simple=None,section=None):
    if table in DATACACHE:
        return DATACACHE[table]
    datamap = tables[table]['iolist']
    tablename = tables[table]['name']
    datafile = os.sep.join([FIS_DATA,"O"+tablename[:4]])
    DATACACHE[table] = BBxFile(datafile,datamap,simple=simple,section=section)
    return DATACACHE[table]


tables = parse_FIS_Schema(FIS_SCHEMAS)

#tables['NVTY1']['fields'][77]

#NVTY = fisData(135,simple="%s101000    101**")

#vendors = fisData(65,simple='10%s')
#vendors['000099']['Gn$']
