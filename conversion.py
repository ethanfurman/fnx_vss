"""Takes the tables from an Access database and converts them into corresponding
OpenERP csv files (for data import), py files (for OE database), and xml files
(for OE views).

It reestablishes relations between tables, and if a numeric field exists which
is the target of a relation, it is removed from the OE version of the table.

There are two special fields: id, and name

'id' is populated with a special value that allows OE to link the tables, and
looks something like modulename_database_table_#, i.e. whmsds_blends_categories_1,
or whmsds_blends_blends_5.  This field will be automatically added to any table
that is the target of a relation.

'name' is special in that OE will automatically index and search on this field
without any extra work on our part.  If a table has only one field that is the
target of a relation, and that field is not numeric, it will be named 'name' in
the OE database, but the presented name in the view will be the same as it was
in the Access table.

The conversion process takes place in four steps:

    1)  get the tables and relations from the Access databases, and convert
        them into dbf files with matching py files that describe the relation
        between Access name and python names, and the linkage between the
        tables.

    2)  make any adjustments to the tables and py files (field renaming, data
        normalization, etc.)

    3)  create the final copies of the csv, py, and xml files for each database,
        per table

    4)  make any final manual adjustments (such as adding one2many links)

This script does the initial converting, linking, and minor renaming, then
creates the scripts that will create the py, xml, and final csv files -- this
allows for human interaction before that final step to change names of fields,
etc., if necessary."""

import os, sys, shlex, shutil, stat, subprocess, re, dbf, csv
from collections import defaultdict
from datetime import date, datetime, time
from path import Path
from string import uppercase, lowercase, digits
from VSS import Table
from VSS.openerp import OpenERPcsv, EmbeddedNewlineError
from VSS.time_machine import BiDict, PropertyDict
from VSS.utils import LazyAttr, Missing, translator
csv_line = OpenERPcsv._convert_line; del OpenERPcsv

import xlrd
from xlrd import open_workbook, xldate_as_tuple
from xlrd import XL_CELL_TEXT, XL_CELL_NUMBER, XL_CELL_DATE, XL_CELL_BOOLEAN, XL_CELL_ERROR, XL_CELL_BLANK

def _get_sheet(self, index_or_name):
    if isinstance(index_or_name, (int, long)):
        return self.sheet_by_index(index_or_name)
    return self.sheet_by_name(index_or_name)

def _get_cell(self, row_col):
    return self.cell(*row_col)

xlrd.book.Book.__getitem__ = _get_sheet
xlrd.sheet.Sheet.__getitem__ = _get_cell

integer = int, long
string = str, unicode
class many2one(object):
    "dummy class used for field types"

strip_invalid_fieldname_chars = translator(keep=uppercase+lowercase+digits+'_')

class ConversionError(Exception):
    "all-purpose exception for conversion problems"

class DataStore(object):
    def __init__(yo, file_name, module):
        yo.module = module
        yo.module_id = module.lower().replace(' ','_')
        file_name = yo.diskname = Path(file_name)     # name of originating jet tables
        basename = yo.basename = file_name.basename.split('.', 1)[0].replace('-','')
        yo.folder = Path('./converting')
        if not os.path.exists(yo.folder):
            os.mkdir(yo.folder)
        #if yo.folder not in sys.path:
        #    sys.path.insert(0, yo.folder)
        yo.tables = PropertyDict(default=PropertyDict)  # tablename -> various bits about the table
        yo.table_names = BiDict()                       # python table name <-> jet table name
        yo.relations = PropertyDict(default=list)       # tablename -> relations involving that table
        if file_name.ext.lower() == '.mdb':
            yo._load_access(file_name)
            yo._to_dbf = yo._jet2dbf
        elif file_name.ext.lower() in ('.xls','.xlsx'):
            yo._load_excel(file_name)
            yo._to_dbf = yo._xl2dbf
        else:
            raise ConversionError('unknown file extension: %s' % file_name.ext)
        for table_name, data in yo.tables.items():
            yo.tables[table_name].dbf_file = "%s_%s_stage1.dbf" % (basename, table_name)

    def __repr__(yo):
        return "DataStore(%r)" % yo.diskname

    def _close(yo):
        "closes all dbf tables -- for testing only"
        for _, obj in yo.tables.items():
            obj.dbf.close()
    
    def _open(yo):
        "opens all dbf tables -- for testing only"
        for _, obj in yo.tables.items():
            obj.dbf.open()
    
    def _create_py(yo):
        lines = []
        table_names = yo.table_names.keys()
        data = [yo.tables[name] for name in table_names]
        lines.append(stage1_header.format(
                basename=yo.basename,
                module=yo.module,
                database=yo.basename,
                table_names='\n        '.join(["%s=%r," % (name, yo.table_names[name]) for name in table_names]),
                ))
        for table_name, datum in zip(table_names, data):
            field_names = datum.field_names.keys()
            field_text = ["(%r, %r)," % (field, datum.field_names[field]) for field in field_names]
            relation_text = []
            relations = yo.relations.get(yo.table_names[table_name], ())
            for relation in relations:
                relation_text.append('%r,' % (relation,))
            if relation_text:
                relation_text.append('')
            field_structure = datum.dbf.structure()
            field_structure = ["'%s',  # %s" % (struct, comment) for struct, comment in zip(field_structure, field_names)]
            field_types = []
            for i, types in sorted(datum.field_types.items()):
                field_types.append(', '.join(['%s' % type for type in types]))
            lines.append(stage1_subclass.format(
                    table_name=table_name,
                    original_name=datum.original_table_name,
                    dbf_file_1=datum.dbf_file,
                    field_names='\n            '.join(field_text),
                    relations='\n            '.join(relation_text),
                    field_struct='\n            '.join(field_structure),
                    field_types = '\n            '.join(['(%s,),    #  %s' % (f, c) for f, c in zip(field_types, field_names)]),
                    ))
        lines.append(stage1_footer)
        return '\n\n'.join(lines)

    def _jet2dbf(yo):
        for table in yo.table_names:
            command = 'mdb-export -D "%Y-%m-%d %H:%M:%S" ' + "%s '%s'" % (yo.diskname, yo.table_names[table])
            csv_contents = get_external_command_output(command)
            if not csv_contents:
                raise ConversionError("unable to get data for %s:%s" % (yo.diskname, yo.table_names[table]))
            csv_contents = csv_contents.strip().split('\n')
            dbf_file = yo.folder/yo.tables[table].dbf_file
            yo.tables[table].dbf_fields = BiDict()
            dbf_fields = []
            field_names = dict()
            for i, (field_name, field_def) in enumerate(yo.tables[table].jet_fields):
                field_name = yo.tables[table].field_names[field_name]
                size = yo.field_size(field_name, field_def)
                dbf_field_name = 'f%d' % i
                field_names[field_name] = dbf_field_name
                dbf_fields.append('%s C(%d)' % (dbf_field_name, size))
                yo.tables[table].dbf_fields[field_name] = dbf_field_name
            dbf_table = yo.tables[table].dbf = Table(
                    dbf_file,
                    dbf_fields,
                    )
            with dbf_table:
                state = None
                for i, line in enumerate(csv_contents):
                    final_line = []
                    try:
                        for i, value in enumerate(csv_line(line, prev_state=state)):
                            final_line.append(value.decode('utf8', 'ignore'))
                    except EmbeddedNewlineError, exc:
                        state = exc.state
                    else:
                        dbf_table.append(tuple(final_line))
                        state = None

    def _load_access(yo, file_name):
        output = get_external_command_output("mdb-schema --no-not-null %s oracle" % file_name).split('\n')
        in_table = False
        for line in output:
            if not in_table:
                if line.startswith('alter table '):     # ubuntu mdb tool (
                    # alter table Sample Memo add constraint Customers_Sample Memo foreign key (CustomerID) references Customers(CustomerID)
                    tn1_start = 12
                    tn1_end = line.index(' add constraint ')
                    fn1_start = line.index(' foreign key (') + 14

                    fn1_end = line.index(') references ')
                    tn2_start = fn1_end + 13
                    tn2_end = line.rindex('(')
                    fn2_start = tn2_end + 1
                    fn2_end = line.rindex(')')
                    tn1 = line[tn1_start:tn1_end]
                    fn1 = line[fn1_start:fn1_end]
                    tn2 = line[tn2_start:tn2_end]
                    fn2 = line[fn2_start:fn2_end]
                    #fn1, fn2 = fix_fieldname(fn1), fix_fieldname(fn2)
                    if tn1 not in yo.table_names or tn2 not in yo.table_names:
                        print "%s: either %s or %s (or both) are not valid tables" % (file_name, tn1, tn2)
                        continue
                    relation = ((tn1, fn1), (tn2, fn2))
                    yo.relations[tn1].append(relation)
                    yo.relations[tn2].append(relation)
                    continue
                elif line.startswith('-- Relationship from '):      # linux mint 14 mdb tool
                    tn1, fn1, tn2, fn2 = re.findall('"([^"]*)"', line)
                    #tn1, tn2 = tn1.replace(' ','_'), tn2.replace(' ','_')
                    #fn1, fn2 = fix_fieldname(fn1), fix_fieldname(fn2)
                    if tn1 not in yo.table_names or tn2 not in yo.table_names:
                        print "%s: either %s or %s (or both) are not valid tables" % (file_name, tn1, tn2)
                        continue
                    relation = ((tn1, fn1), (tn2, fn2))
                    yo.relations[tn1].append(relation)
                    yo.relations[tn2].append(relation)
                    continue
                if not line.startswith('CREATE TABLE '):
                    continue
                jet_table_name = line[13:].strip('"')
                table_name = jet_table_name.replace(' ','_')
                datum = yo.tables[table_name]
                if table_name.startswith(("_", "MSys", "Switchboard", "Errors", "TMPCL", "Paste", "~")):
                    continue
                yo.table_names[table_name] = jet_table_name
                in_table = True
                datum.jet_fields = list()
                datum.field_names = BiDict()
                datum.field_types = defaultdict(set)
                continue
            if line[:2] == ' (':
                continue
            if line[:2] == ');':
                in_table = False
                continue
            line = line.strip('\t, ')
            line = [l for l in line.split('\t') if l]
            jet_field_name, field_def = line
            jet_field_name = jet_field_name.strip('"')
            oe_field_name = fix_fieldname(jet_field_name)
            datum.field_types[len(datum.field_names)].add(fix_fieldtype(field_def)[0])
            datum.field_names[oe_field_name] = jet_field_name
            datum.jet_fields.append((jet_field_name, field_def))
            datum.original_table_name = jet_table_name
        for rels in yo.relations.values():
            rels[:] = list(set(rels))

    def _load_excel(yo, file_name):
        file_name = Path(file_name)
        yo._book = book = open_workbook(file_name)
        for sheet in book:
            if sheet.nrows:     # skip the empty sheets
                xl_sheet = sheet.name
                oe_sheet = xl_sheet.replace(' ','_')
                yo.table_names[oe_sheet] = xl_sheet
                yo.tables[oe_sheet].original_table_name = xl_sheet
                yo.tables[oe_sheet].field_names = BiDict()
                yo.tables[oe_sheet].jet_fields = None
                for j in range(sheet.ncols):
                    cell = sheet[0, j]
                    if cell.ctype == XL_CELL_TEXT:
                        value = cell.value
                    elif cell.ctype in (0, XL_CELL_BLANK):
                        value = 'field_%02d' % j
                    else:
                        raise ConversionError("error or bad cell type in header: %d" % cell.ctype)
                    oe_field_name = fix_fieldname(value)
                    count = 0
                    while oe_field_name in yo.tables[oe_sheet].field_names:
                        count += 1
                        oe_field_name = fix_fieldname(value + ' ' + str(count))
                    if count:
                        value = value + ' ' + str(count)
                    yo.tables[oe_sheet].field_names[oe_field_name] = value

    def _xl2dbf(yo):
        for oe_sheet in yo.table_names:
            xl_sheet = yo.table_names[oe_sheet]
            sheet = yo._book[xl_sheet]
            field_types = yo.tables[oe_sheet].field_types = defaultdict(set)
            dbf_file = yo.folder/"%s_%s_stage1.dbf" % (yo.basename, oe_sheet)
            yo.tables[oe_sheet].dbf_fields = BiDict()
            dbf_fields = []
            field_names = dict()
            with Table(
                    xl_sheet,
                    ["f%d M" % i for i in range(sheet.ncols)],
                    on_disk=False,
                    ) as mdbf:
                for i in range(1, sheet.nrows):
                    row = []
                    for j in range(sheet.ncols):
                        cell = sheet[i, j]
                        if cell.ctype == XL_CELL_TEXT:
                            value = '"%s"' % cell.value.replace('"','""')
                            type = str
                        elif cell.ctype == XL_CELL_NUMBER:
                            value = str(cell.value)
                            print repr(value), repr(cell.value), int(cell.value) == cell.value
                            type = (float, int)[int(cell.value) == cell.value]
                            value = str(type(cell.value))
                        elif cell.ctype == XL_CELL_DATE:
                            dt = xldate_as_tuple(cell.value, yo._book.datemode)
                            if dt == (0, 0, 0, 0, 0, 0):
                                value = None
                                type = None
                            elif dt[3:] == (0, 0, 0):
                                value = "%04d-%02d-%02d" % dt[:3]
                                type = date
                            elif dt[:3] == (0, 0, 0):
                                value = "%02d:%02d:%02d" % dt[3:]
                                type = time
                            else:
                                value = "%04d-%02d-%02d %02d:%02d:%02d" % dt
                                type = datetime
                        elif cell.ctype == XL_CELL_BOOLEAN:
                            value = str(bool(cell.value))
                            type = bool
                        elif cell.ctype in (0, XL_CELL_BLANK):
                            value = None
                            type = None
                        else:
                            raise ConversionError("error or unknown cell type: %d" % cell.ctype)
                        row.append(value)
                        if type is not None:
                            field_types[j].add(type.__name__)
                    mdbf.append(tuple(row))
                xl_field_names = [yo.tables[oe_sheet].field_names[f] for f in yo.tables[oe_sheet].field_names]
                field_lens = [len(f) for f in xl_field_names]
                for row in mdbf:
                    for i, value in enumerate(row):
                        field_lens[i] = max(field_lens[i], len(value))
                fields = []
                for i, length in enumerate(field_lens):
                    fields.append('f%d C(%d)' % (i, length))
                    if field_types.get(i) is None:  # if any column was empty, default to None
                        field_types[i].add('None')
                with Table(dbf_file, fields) as ddbf:
                    yo.tables[oe_sheet].dbf = ddbf
                    ddbf.append(tuple(xl_field_names))
                    for row in mdbf:
                        ddbf.append(row)

    def detail(yo, tablename):
        "'Blend Categories' --> 'Blend_Categories'"
        tablename = tablename.replace(' ','_')
        relations = yo.relations[tablename]
        rel_to = []
        rel_from = []
        for rel in relations:
            if tablename == rel.src_table:
                rel_from.append("%s -> %s:%s"  % (rel.src_field, rel.tgt_table, rel.tgt_field))
            elif tablename == rel.tgt_table:
                rel_to.append("%s <- %s:%s" % (rel.tgt_field, rel.src_table, rel.src_field))
            else:
                raise ConversionError("%r does not seem to belong to table %r" % (rel, tablename))
        fields = []
        jet_field_defs = yo.tables[tablename].jet_fields
        if jet_field_defs is not None:
            for f in jet_field_defs:
                fields.append("%-15s: %s" % (f[1], f[0]))
            result = "%s\n" % tablename
            if rel_to or rel_from:
                result += '    Relations\n'
            if rel_to:
                result += '        ' + '\n        '.join(rel_to) + '\n'
            if rel_from:
                result += '        ' + '\n        '.join(rel_from) + '\n'
            result += '    Fields\n'
            result += '        ' + '\n        '.join(fields) + '\n'
        else:
            result = "%s\n    Fields\n        " % tablename
            field_names = yo.tables[tablename].field_names
            keys = field_names.keys()
            values = [field_names[k] for k in keys]
            result += '\n        '.join(values)
        return result

    def field_size(yo, name, jet_def):
        "VARCHAR (2) --> 2; NUMBER (4) --> 20"
        size = 30
        if jet_def.startswith('VARCHAR2'):
            size = max(size, int(re.search('\(\d+\)', jet_def).group()[1:-1]) + 12)
        if name.endswith('_ID'):
            size = max(size, 50)
        return size

    def stage1(yo, overwrite=False):
        yo._to_dbf()
        filename = yo.folder/'%s_stage1' % yo.basename.replace(' ','_')
        if not os.path.exists(filename) or overwrite:
            with open(filename, 'w') as py:
                py.write(yo._create_py())
            os.chmod(filename, stat.S_IRWXU)
        else:
            print 'Skipping creation of %s' % filename
    
class Stage1(object):
    "stage 1 --> data normalization --> stage 2"
    def __init__(yo):
        yo.stage2_table_name = '%s_%s_stage2.dbf' % (yo.database, yo.table_names[yo.original_name])
        yo.stage3_table_name = '%s_%s_stage3.dbf' % (yo.database, yo.table_names[yo.original_name])
        yo.classes[yo.original_name] = yo
        if os.path.exists(yo.stage1_table_name):
            yo.stage1_table = Table(yo.stage1_table_name)
        if os.path.exists(yo.stage2_table_name):
            yo.stage2_table = Table(yo.stage2_table_name)
        for field_type in yo.stage2_field_types:
            if len(field_type) != 1:
                raise ConversionError("each field type in stage2_field_types should have one type")
        yo.stage2_field_types = [t[0] for t in yo.stage2_field_types]
        for rel in yo.relations:
            check_field = (rel[0][1], rel[1][1]) [rel[1][0] == yo.original_name]
            if yo.stage2_field_names[check_field] not in yo.stage2_field_names:
                raise ConversionError('%r does not seem to be an original field name' % check_field)
        yo.log_file = open('%s_%s_stage1.log' % (yo.database, yo.table_names[yo.original_name]), 'a')

    def _create_py(yo):
        field_names = yo.stage2_field_names.keys()
        field_text = ["(%r, %r)," % (field, yo.stage2_field_names[field]) for field in field_names]
        relation_text = []
        for relation in yo.relations:
            relation_text.append('%r,' % (relation,))
        if relation_text:
            relation_text.append('')
        field_structure = yo.stage2_field_structure
        field_structure = ["'%s',  # %s" % (struct, comment) for struct, comment in zip(field_structure, field_names)]
        field_types = [f if f is not None else str for f in yo.stage2_field_types]
        lines = []
        lines.append(stage2_subclass.format(
                table_name=yo.__class__.__name__,
                original_name=yo.original_name,
                dbf_file_2=yo.stage2_table_name,
                field_names='\n            '.join(field_text),
                relations='\n            '.join(relation_text),
                field_struct='\n            '.join(field_structure),
                field_types = '\n            '.join(['(%s,),    #  %s' %
                        (f.__name__, c) for f, c in zip(field_types, field_names)]),
                ))
        return '\n\n'.join(lines)

    def _dbf_transfer(yo):
        """takes initial exported files and re-exports them, calling `transfer` on each record
        `transfer` can be overridden to drop, split, verify, etc., record data"""
        src = yo.stage1_table
        dst = yo.stage2_table = src.new(yo.stage2_table_name, yo.stage2_field_structure)
        with dbf.Tables(src, dst):
            dst.append(tuple(yo.stage2_field_names.keys()))
            for rec in src[1:]:
                dst.append(yo.transfer(dbf.recno(rec), rec))

    def log(yo, rec_num, field_name, data, message):
        print('%s:   %5d  <%s>:%r -- %s\n' % (yo.__class__.__name__, rec_num, field_name, data, message))
        yo.log_file.write('%s:   %5d  <%s>:%r -- %s\n' % (yo.__class__.__name__, rec_num, field_name, data, message))

    def transfer(yo, recno, rec):
        'default: removes extraneous spaces from text fields, collapses scientific notation to normal numbers'
        fields = list(rec)
        for i, field in enumerate(fields):
            if field and field[0] == field[-1] == '"':
                fields[i] = '"%s"' % (field.strip('" '))
            elif '.' in field and 'e' in field and ('+' in field or '-' in field):
                fields[i] = str(float(field))
        return tuple(fields)

class Stage2(object):
    def __init__(yo):
        yo.stage3_table_name = '%s_%s_stage3.dbf' % (yo.database, yo.table_names[yo.original_name])
        yo.classes[yo.original_name] = yo
        if os.path.exists(yo.stage2_table_name):
            yo.stage2_table = Table(yo.stage2_table_name)
        if os.path.exists(yo.stage3_table_name):
            yo.stage3_table = Table(yo.stage3_table_name)
        for field_type in yo.stage3_field_types:
            if len(field_type) != 1:
                raise ConversionError("each field type in stage2_field_types should have one type")
        yo.stage3_field_types = [t[0] for t in yo.stage3_field_types]
        for rel in yo.relations:
            check_field = (rel[0][1], rel[1][1]) [rel[1][0] == yo.original_name]
            if yo.stage3_field_names[check_field] not in yo.stage3_field_names:
                raise ConversionError('%r does not seem to be an original field name' % check_field)
        yo.log_file = open('%s_%s_stage2.log' % (yo.database, yo.table_names[yo.original_name]), 'a')
        yo.relations = set()
        yo.new_relations = []
        yo.drop_fields = set(yo.__class__.drop_fields)
        yo.drop_field_indices = set()
        for i, field in enumerate(yo.stage3_field_structure):
            if field.startswith(tuple(yo.drop_fields)):
                yo.drop_field_indices.add(i)
        for record in dbf.Process(yo.stage2_table, start=1):
            if dbf.is_deleted(record):
                dbf.undelete(record)

    def _create_py(yo):
        field_names = yo.stage3_field_names.keys()
        field_structs = yo.stage3_field_structure[:]
        field_types = yo.stage3_field_types[:]
        for index in sorted(yo.drop_field_indices, reverse=True):
            field_names.pop(index)
            field_structs.pop(index)
            field_types.pop(index)
        field_names_text = ["(%r, %r)," % (field, yo.stage3_field_names[field]) for field in field_names]
        relation_text = []
        for relation in yo.new_relations:
            relation_text.append('%r,' % (relation,))
        if relation_text:
            relation_text.append('')
        field_defs = []
        for struct, type, name in zip(field_structs, field_types, field_names):
            size = re.search('\((\d+)\)', struct).groups()[0]
            type = {
                    str : 'char',
                    int : 'integer',
                    bool : 'bool',
                    }.get(type, type.__name__)
            if type == 'char':
                field_defs.append('(%r, %s),        # %s' % (type, size, name))
            else:
                field_defs.append('(%r, ),          # %s' % (type, name))
        lines = []
        lines.append(stage3_subclass.format(
                table_name=yo.__class__.__name__,
                original_name=yo.original_name,
                dbf_file=yo.stage3_table_name,
                field_names='\n            '.join(field_names_text),
                relations='\n            '.join(relation_text),
                py_defs='\n            '.join(field_defs),
                ))
        return '\n\n'.join(lines)

    def _dbf_transfer(yo):
        """takes initial exported files and re-exports them, calling `transfer` on each record
        `transfer` can be overridden to drop, split, verify, etc., record data"""
        src = yo.stage2_table
        dst = yo.stage3_table
        class_tables = [cls.stage2_table for cls in yo.classes.values()]
        class_tables.append(dst)
        with dbf.Tables(class_tables):
            template = dst.create_template()
            for rec in dbf.Process(src, 1, None, dbf.is_deleted):
                if dbf.is_deleted(rec):
                    continue
                dst.append(yo._transfer(rec, template))

    def _drop_missing_links(yo):
        "make sure all references are valid; delete records that don't link up"
        class_tables = [cls.stage2_table for cls in yo.classes.values()]
        dropped = 0
        with dbf.Tables(class_tables):
            for rel in yo.relations:
                if rel.src_table_name == yo.original_name:
                    for record in dbf.Process(yo.stage2_table, None, None, dbf.is_deleted):
                        try:
                            found = rel[record]
                            if all(dbf.is_deleted(rec) for rec in found):
                                raise dbf.NotFoundError("no active records found")
                        except dbf.NotFoundError:
                            print rel
                            print record
                            dbf.delete(record)
                            dropped += 1
                            yo.log(
                                    dbf.recno(record),
                                    rel.src_field_name,
                                    record[rel.src_field], 
                                    "link not found in %s" % rel.tgt_table_name,
                                    )
        return dropped

    def _modify_stage3_structures_1(yo):
        for rel in yo.__class__.relations:
            "rel = ((src_table_name, src_table_field), (tgt_table_name, tgt_table_field))"
            src_cls = yo.classes[rel[0][0]]
            tgt_cls = yo.classes[rel[1][0]]
            src_table = src_cls.stage2_table
            tgt_table = tgt_cls.stage2_table
            src_field = src_cls.stage2_field_names.keys().index(src_cls.stage2_field_names[rel[0][1]])
            tgt_field = tgt_cls.stage2_field_names.keys().index(tgt_cls.stage2_field_names[rel[1][1]])
            relation = dbf.Relation(
                    (src_table, src_field),
                    (tgt_table, tgt_field),
                    src_names=rel[0],
                    tgt_names=rel[1],
                    )
            if src_table is yo.stage2_table:                                    # adjust field sizes
                yo.relations.add(relation)
                new_tgt_fld = src_cls.stage3_field_names[relation.src_field_name]    # get new name from source table
                new_tgt_fld_index = tgt_cls.stage3_field_names.keys().index(new_tgt_fld)
                relation.source_field, new_fld_struct = tgt_cls.stage3_field_structure[new_tgt_fld_index].split()
                src_fld_index = src_cls.stage3_field_names.keys().index(new_tgt_fld)
                relation.replace_field, old_fld_struct = src_cls.stage3_field_structure[src_fld_index].split()
                src_cls.stage3_field_structure[src_fld_index] = '%s %s' % (relation.replace_field, new_fld_struct)
                src_cls.stage3_field_types[src_fld_index] = tgt_cls.stage3_field_types[new_tgt_fld_index]
                new_rel = (
                    (relation.src_table_name, relation.src_field_name),
                    (relation.tgt_table_name, tgt_cls.stage3_field_names[src_cls.stage3_field_names[relation.src_field_name]])
                    )
                src_cls.new_relations.append(new_rel)
                tgt_cls.new_relations.append(new_rel)
            else: # see if field should be dropped
                src_field_name = src_cls.stage3_field_names.keys()[src_field]
                tgt_field_name = tgt_cls.stage3_field_names.keys()[tgt_field]
                if src_field_name != tgt_field_name:
                    dbf_field = tgt_cls.stage3_field_structure[tgt_field].split()[0]
                    yo.drop_fields.add(dbf_field)
                    yo.drop_field_indices.add(tgt_field)
        yo.normal_fields = set([f.split()[0] for f in yo.stage3_field_structure])
        yo.replace_fields = set([rel.replace_field for rel in yo.relations])
        yo.normal_fields -= yo.replace_fields
        field_structure = yo.stage3_field_structure[:]
        original_fields = yo.stage3_field_names.keys()
        for index in sorted(yo.drop_field_indices, reverse=True):
            field_structure.pop(index)
            original_fields.pop(index)
        yo.stage3_table = yo.stage2_table.new(yo.stage3_table_name, field_structure)
        with yo.stage3_table as table:
            table.append(tuple(original_fields))

    def _modify_stage3_structures_2(yo):
        class_tables = [cls.stage2_table for cls in yo.classes.values()]
        class_tables.append(yo.stage3_table)
        with dbf.Tables(class_tables):
            for rel in yo.relations:    # actual Relation class at this point
                if rel.src_table is yo.stage2_table \
                and rel.one_or_many(rel.src_table) == 'many':
                    index = yo.stage3_field_names.keys().index(yo.stage3_field_names[rel.src_field_name])
                    #yo.stage3_field_names[index] += '_id'
                    yo.stage3_field_types[index] = many2one

    def log(yo, rec_num, field_name, data, message):
        print('%s:   record %-5d  <%s>:%r -- %s\n' % (yo.__class__.__name__, rec_num, field_name, data, message))
        yo.log_file.write('%s:   record %-5d  <%s>:%r -- %s\n' % (yo.__class__.__name__, rec_num, field_name, data, message))

    def _transfer(yo, rec, new_rec):
        'unlink files'
        dbf.reset(new_rec)
        for f in yo.normal_fields - yo.drop_fields:
            new_rec[f] = rec[f]
        for rel in yo.relations:
            target_list = rel[rec]
            new_rec[rel.replace_field] = target_list[0][rel.source_field]
        return new_rec



class Stage3(object):
    "generates final xml/csv/py files"

    def __init__(yo):
        dbf_file = Path(yo.dbf_file)
        yo.csv_file = yo.folder/('%s.%s_%s.csv' % (yo.module_id, yo.database_id, yo.tables[yo.original_name].lower()))
        yo.input_table = Table(dbf_file)
        yo.one2many = []
        yo.relations_in = {}
        yo.relations_out = {}
        for rel in yo.relations:
            if rel[0][0] == yo.original_name:
                yo.relations_out[yo.field_names[rel[0][1]]] = rel[1]
            elif rel[1][0] == yo.original_name:
                yo.relations_in[yo.field_names[rel[1][1]]] = rel[0]
            else:
                raise ConversionError('incorrect relation: %s -- %r' % (yo.__class__.name, rel))
        yo.classes[yo.original_name] = yo

    def create_csv(yo):
        "step 1"
        with open(yo.csv_file, 'w') as csv:
            csv.write(','.join(yo.field_names)+'\n')
            for record in dbf.Process(yo.input_table, start=1):
                fields = []
                for field in record:
                    if field and field[0] == field[-1] == '"':
                        field = '"%s"' % field[1:-1].replace('"','""')
                    fields.append(field.encode('utf8'))
                csv.write(','.join(fields))
                csv.write('\n')

    def create_py(yo):
        "step 2"
        name = "%s.%s_%s" % (yo.module_id, yo.database_id,  yo.tables[yo.original_name].lower())
        desc = "table data for %s" % name
        columns = ['    _columns = {']
        sel_funcs = []
        for i, (oe_field, col_def) in enumerate(zip(yo.field_names, yo.py_field_defs)):
            if col_def[0] == 'many2one':
                subst = PropertyDict()
                subst.oe_field = oe_field       # .rsplit('_', 1)[0]
                subst.display_name = yo.field_names[oe_field]
                subst.module = yo.module_id
                subst.target_table = "%s_%s" % (yo.database_id, yo.tables[yo.relations_out[oe_field][0]].lower())
                subst.func_name = '_select_%s' % oe_field
                columns.append(MANY2ONE.format(**subst))
                #sel_funcs.append(SEL_FUNC.format(field=oe_field, table='%s.%s' % (yo.module_id, subst.target_table)))
            elif col_def[0] == 'char':
                subst = PropertyDict()
                subst.oe_field = oe_field
                subst.display_name = yo.field_names[oe_field]
                subst.size = col_def[1]
                columns.append(CHAR.format(**subst))
            else:
                subst = PropertyDict()
                subst.oe_field = oe_field
                subst.display_name = yo.field_names[oe_field]
                columns.append(globals()[col_def[0].upper()].format(**subst))
        for field, (src_table, src_field) in yo.relations_in.items():
            subst = PropertyDict()
            subst.oe_field = yo.tables[src_table].lower() + '_ids'
            subst.module = yo.module_id
            subst.target_table = "%s_%s" % (yo.database_id, yo.tables[src_table].lower())
            subst.target_field = yo.classes[src_table].field_names[src_field]
            subst.display_name = src_table
            columns.append(ONE2MANY.format(**subst))
            target_fields = [f for f in yo.classes[src_table].field_names if f != subst.target_field]
            yo.one2many.append((subst.oe_field, target_fields))
        result = []
        result.append('class %s(osv.Model):' % yo.tables[yo.original_name])
        result.append('    _name = %r' % name)
        result.append('    _description = %r' % desc)
        if sel_funcs:
            result.append('\n'.join(sel_funcs))
        result.append('\n        '.join(columns))
        result.append('        }')
        result.append('%s()' % yo.tables[yo.original_name])
        return '\n'.join(result)

    def create_xml(yo):
        "step 3"
        final = []
        top_name = yo.module
        top_id = top_name.lower().replace(' ','_')
        side_name = yo.database
        side_id = side_name.lower().replace(' ','_')
        table_id = yo.tables[yo.original_name].lower()
        fields = []
        field_ids = []
        for f in skipper(yo.field_names.keys()):
            fields.append(FIELD_ENTRY.format(name=f))
        for field, target_fields in yo.one2many:
            tbd = field[:-4].title()
            tf = '\n            '.join([FIELD_ENTRY.format(name=f) for f in target_fields])
            field_ids.extend(FIELD_IDS.format(tbd=tbd, name=field, target_fields=tf).split('\n'))
        final.append(FORM_RECORD.format(
                id=table_id,
                side_id=side_id,
                top_id=top_id,
                db_field_lines=('\n'+' '*28).join(fields),
                link_ids=('\n'+' '*24).join(field_ids),
                ))
        final.append(TREE_RECORD.format(
                id=table_id,
                side_id=side_id,
                top_id=top_id,
                db_field_lines=('\n'+' '*20).join(fields),
                ))
        final.append(ACTION_RECORD.format(
                id=table_id,
                side_id=side_id,
                top_id=top_id,
                ))
        final.append(MENU_ENTRY.format(
                entry_name=table_id.title(),
                id=table_id,
                side_id=side_id,
                top_id=top_id,
                ))
        return '\n'.join(final)

def fix_fieldname(fieldname):
    "make fieldname a valid python/OE field name"
    fieldname = fieldname.replace('#','Number').replace('%','Percent').replace(' ','_').replace('/','_').replace('-','_')
    fieldname = fieldname.lower()
    if fieldname.endswith('id') and not fieldname.endswith('_id'):
        fieldname = fieldname[:-2] + '_id'
    fieldname = strip_invalid_fieldname_chars(fieldname).strip('_')
    while '__' in fieldname:
        fieldname = fieldname.replace('__','_')
    return fieldname

def fix_fieldtype(fieldtype):
    "convert fieldtype from oracle to OE"
    convert = {
        # Oracle names -> OE names
        'DATE'          : 'datetime',
        'FLOAT'         : 'float',
        'NUMBER (255)'  : 'bool',
        'NUMBER(1)'     : 'bool',
        'TIMESTAMP'     : 'datetime',
        }
    new_type = convert.get(fieldtype, None)
    size = None
    if new_type is None:
        if fieldtype.startswith('NUMBER(') and ',' in fieldtype[7:-1]:
            new_type = 'float'
        elif fieldtype.startswith('NUMBER'):
            new_type = 'int'
        elif fieldtype.startswith('VARCHAR2'):
            new_type, size = fieldtype.split()
            new_type = {'NUMBER':'int','VARCHAR2':'str'}[new_type]
            size = size.strip('()')
        else:
            raise ConversionError("unknown field type: %s" % fieldtype)
    return new_type, size

def get_external_command_output(command):
    args = shlex.split(command)
    ret = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
    return ret

def skipper(sequence):
    midpoint, odd = divmod(len(sequence), 2)
    midpoint += odd
    for item1, item2 in zip(sequence[:midpoint], sequence[midpoint:]):
        yield item1
        yield item2
    if odd:
        yield sequence[midpoint-1]

stage1_header = '''\
#!/usr/bin/python
"""The purpose of stage 1 is to allow for custom record processing of the data
exported in the initial convert step.  Create a `transfer(self, record)` method
for each table that needs custom processing (which might include data normalization,
data validation, etc.)."""

import dbf, os, re, stat
from datetime import date, datetime, time
from scription import Script, Run, Bool
from VSS import Table
from VSS.conversion import Stage1, stage2_header, stage2_footer
from VSS.path import Path
from VSS.utils import BiDict

MODULE = {module!r}
DATABASE = {database!r}
TABLE_NAMES = BiDict(
        {table_names}
        )
CLASSES = {{}}
FILENAME = {basename!r}

'''

stage1_subclass = '''
class {table_name}(Stage1):
    "class for stage 1 conversions"
    module = MODULE
    database = DATABASE
    table_names = TABLE_NAMES
    classes = CLASSES
    original_name = {original_name!r}
    stage1_table = None
    stage1_table_name = {dbf_file_1!r}
    stage1_field_names = BiDict(
            {field_names}
            )
    stage2_table = None
    stage2_table_name = '...'
    stage2_field_names = BiDict(
            {field_names}
            )
    stage2_field_structure = [
            {field_struct}
            ]
    stage2_field_types = [
            {field_types}
            ]
    relations = (
            {relations})
{table_name} = {table_name}()
'''

stage1_footer = '''
@Script(overwrite=('if True overwrites preexisting script', 'flag'))
def next_stage(overwrite=False):
    """    The purpose of stage 1 is to allow for custom record processing of the data
    exported in the initial convert step.  Create a `transfer(self, record)` method
    for each table that needs custom processing (which might include data normalization,
    data validation, etc.)."""
    lines = []
    table_names = TABLE_NAMES.keys()
    lines.append(stage2_header.format(
            basename=FILENAME,
            module=MODULE,
            database=FILENAME,
            table_names='\\n        '.join(["%s=%r," % (name, TABLE_NAMES[name]) for name in table_names]),
            ))
    classes = CLASSES.values()
    for cls in classes:
        cls._dbf_transfer()
    filename = ('%s_stage2' % (FILENAME, )).replace(' ','_')
    if not os.path.exists(filename) or overwrite:
        with open(filename, 'w') as py:
            py.write('\\n'.join(lines))
            for cls in classes:
                py.write(cls._create_py())
            py.write(stage2_footer)
        os.chmod(filename, stat.S_IRWXU)
    else:
        print "skipping creation of %s" % filename

if __name__ == '__main__':
    Run()
'''

stage2_header = '''\
#!/usr/bin/python

"""The purpose of stage 2 is to update the OpenERP field names (NOT the original names),
manually fix any records reported in stage 1, (possibly) drop any fields not desired
in the final output, and update the field names to match final relationships"""

import dbf, os, re, stat
from datetime import date, datetime, time
from scription import Script, Run
from VSS import Table
from VSS.conversion import Stage2, stage3_header, stage3_footer
from VSS.path import Path
from VSS.utils import BiDict

MODULE = {module!r}
DATABASE = {database!r}
TABLE_NAMES = BiDict(
        {table_names}
        )
CLASSES = {{}}
FILENAME = {basename!r}

'''

stage2_subclass = '''
class {table_name}(Stage2):
    "class for stage 2 conversions"
    module = MODULE
    database = DATABASE
    table_names = TABLE_NAMES
    classes = CLASSES
    original_name = {original_name!r}
    stage2_table = None
    stage2_table_name = {dbf_file_2!r}
    stage2_field_names = BiDict(
            {field_names}
            )
    stage3_table = None
    stage3_table_name = '...'
    stage3_field_names = BiDict(
            {field_names}
            )
    stage3_field_structure = [
            {field_struct}
            ]
    stage3_field_types = [
            {field_types}
            ]
    relations = (
            {relations})
    drop_fields = (
            )
{table_name} = {table_name}()
'''

stage2_footer = '''
@Script(overwrite=('if True overwrites preexisting script', 'flag'))
def next_stage(overwrite=False):
    """    The purpose of stage 2 is to update the OpenERP field names (NOT the original names),
    manually fix any records reported in stage 1, and (possibly) drop any fields not desired
    in the final output."""
    lines = []
    table_names = TABLE_NAMES.keys()
    lines.append(stage3_header.format(
            basename=FILENAME.lower(),
            module=MODULE,
            database=FILENAME,
            tables='\\n        '.join(["%s=%r," % (name, TABLE_NAMES[name]) for name in table_names]),
            ))
    classes = CLASSES.values()
    for cls in classes:
        cls._modify_stage3_structures_1()
    for cls in classes:
        cls._modify_stage3_structures_2()
    while "missing links may yet exist":
        dropped_records = 0
        for cls in classes:
            dropped_records += cls._drop_missing_links()
        if not dropped_records:
            break
    for cls in classes:
        cls._dbf_transfer()
    filename = ('%s_stage3' % (FILENAME, )).replace(' ','_')
    if not os.path.exists(filename) or overwrite:
        with open(filename, 'w') as py:
            py.write('\\n'.join(lines))
            for cls in classes:
                py.write(cls._create_py())
            py.write(stage3_footer)
        os.chmod(filename, stat.S_IRWXU)
    else:
        print "skipping creation of %s" % filename

if __name__ == '__main__':
    Run()
'''

stage3_header = """\
#!/usr/bin/python

'''Last chance to change the OE names, as after this it is a total PITA to do so;
xml display names can (and should) be changed in the next step -- if done now, make
sure and make the relation field names match'''

import dbf, os, shutil
from scription import Script, Run
from VSS import Table
from VSS.conversion import ConversionError, Stage3, ONE2MANY, MANY2ONE, BOOL, CHAR, FLOAT, INTEGER
from VSS.conversion import XML_HEADER, XML_FOOTER, TOP_MENU, SIDE_MENU, MENU_ENTRY, FORM_RECORD, TREE_RECORD, ACTION_RECORD
from VSS.path import Path
from VSS.utils import BiDict

MODULE = {module!r}
MODULE_ID = MODULE.lower().replace(' ','_')
DATABASE = {database!r}
DATABASE_ID = DATABASE.lower().replace(' ','_')
TABLES = BiDict(
        {tables}
        )
CLASSES = {{}}
FOLDER = Path(MODULE_ID.lower())
BASENAME = Path({basename!r}.lower())

if not os.path.exists(FOLDER):
    os.mkdir(FOLDER)

final_py = []
final_xml_header = [XML_HEADER]
final_xml_header.append(SIDE_MENU.format(
    side_name=DATABASE,
    side_id=DATABASE.lower().replace(' ','_'),
    top_id=MODULE.lower().replace(' ','_'),
    ))
final_xml_body = []
"""

stage3_subclass = '''
class {table_name}(Stage3):
    module = MODULE
    module_id = MODULE_ID
    database = DATABASE
    database_id = DATABASE_ID
    tables = TABLES
    classes = CLASSES
    original_name = {original_name!r}
    dbf_file = {dbf_file!r}
    folder = FOLDER
    relations = (
            {relations})
    field_names = BiDict(
            {field_names}
        )
    py_field_defs = (
            {py_defs}
        )
{table_name} = {table_name}()
'''

stage3_footer = """
@Script(overwrite=('if True overwrites preexisting script', 'flag'))
def next_stage(overwrite=False):

    for cls in CLASSES.values():
        cls.create_csv()
        final_py.append(cls.create_py())
        final_xml_body.append(cls.create_xml())

    py_file = (FOLDER/BASENAME+'.py').replace(' ','_')
    xml_file = (FOLDER/BASENAME+"_view.xml").replace(' ','_')
    if not os.path.exists(py_file) or overwrite:
        with open(py_file, "w") as final:
            final.write("from osv import osv, fields\\n\\n")
            final.write("\\n\\n".join(final_py))
    else:
        print "skipping creation of %s" % py_file

    if not os.path.exists(xml_file) or overwrite:
        with open(xml_file, "w") as final:
            final.write("\\n".join(final_xml_header))
            final.write("\\n")
            final.write("\\n".join(final_xml_body))
            final.write("\\n")
            final.write(XML_FOOTER)
    else:
        print "skipping creation of %s" % xml_file

    links = {}
    for class_name, cls in CLASSES.items():
        class_name = TABLES[class_name].lower()
        links[class_name] = []
        for src_field, (tgt_table, tgt_field) in cls.relations_out.items():
            links[class_name].append(TABLES[tgt_table].lower())

    final_order = []
    last_count = len(links)
    while links:
        done = []
        for table, dependencies in sorted(links.items()):
            if not dependencies:
                final_order.append(table)
                done.append(table)
                break
        for table in done:
            del links[table]
        for dependencies in links.values():
            for table in done:
                if table in dependencies:
                    dependencies.remove(table)
        if len(links) == last_count:    # nothing removed
            raise ConversionError('dependency loop detected')
        last_count = len(links)
    with open((BASENAME+'_openerp.py').replace(' ','_'), 'w') as oe:
        for i, name in enumerate(final_order):
            final_order[i] = "%s.%s_%s.csv" % (MODULE_ID, DATABASE_ID, name)
        oe.write("files = [\\n    %s\\n]" % '\\n    '.join(["%r," % f for f in final_order]))


if __name__ == '__main__':
    Run()
"""

SEL_FUNC = "    def _select_{field}(self, cr, uid, context=None):\n"\
           "        obj = self.pool.get({table!r})\n"\
           "        ids = obj.search(cr, uid, [])\n"\
           "        res = obj.read(cr, uid, ids, ['name', 'id'], context)\n"\
           "        res = [(r['id'], r['name']) for r in res]\n"\
           "        return res"
ONE2MANY = "'{oe_field}' : fields.one2many(\n"\
           "            '{module}.{target_table}',\n"\
           "            '{target_field}',\n"\
           "            {display_name!r},\n"\
           "            ),"
MANY2ONE = "'{oe_field}' : fields.many2one(\n"\
           "            '{module}.{target_table}',\n"\
           "            {display_name!r},\n"\
           "            ),"
           #"            selection={func_name},\n"\
BOOL = "'{oe_field}' : fields.boolean({display_name!r}),"
CHAR = "'{oe_field}' : fields.char({display_name!r}, size={size}),"
DATETIME = "'{oe_field}' : fields.datetime({display_name!r}),"
FLOAT = "'{oe_field}' : fields.float({display_name!r}),"
INTEGER = "'{oe_field}' : fields.integer({display_name!r}),"

XML_HEADER = """\
<?xml version="1.0"?>
<openerp>
    <data>
"""

XML_FOOTER = """
    </data>
</openerp>"""

TOP_MENU = '        <menuitem name="{top_name}" id="{top_id}" />'
SIDE_MENU = '        <menuitem name="{side_name}" id="{top_id}_{side_id}" parent="{top_id}" />'
MENU_ENTRY = '        <menuitem name="{entry_name}" id="{top_id}_{side_id}_{id}" parent="{top_id}_{side_id}" action="action_{side_id}_{id}" />'
FIELD_ENTRY = '<field name="{name}"/>'
FIELD_IDS = '''\
<page string="{tbd}">
    <field name="{name}" nolabel="1">
        <form>
            {target_fields}
        </form>
        <tree>
            <!--
            {target_fields}
            -->
        </tree>
    </field>
</page>'''

FORM_RECORD = """
        <record model="ir.ui.view" id="{side_id}_{id}_form">
            <field name="name">{side_id}_{id}</field>
            <field name="model">{top_id}.{side_id}_{id}</field>
            <field name="type">form</field>
            <field name="arch" type="xml">
                <form string="{id}">
                    <notebook colspan="4">
                        <page string="General Info">
                            {db_field_lines}
                        </page>
                        {link_ids}
                        <page string="Notes (TBI)"/>
                    </notebook>
                </form>
            </field>
        </record>
"""

TREE_RECORD = """
        <record model="ir.ui.view" id="{side_id}_{id}_tree">
            <field name="name">{side_id}_{id}</field>
            <field name="model">{top_id}.{side_id}_{id}</field>
            <field name="type">tree</field>
            <field name="arch" type="xml">
                <tree string="{id}">
                <!--
                    {db_field_lines}
                -->
                </tree>
            </field>
        </record>
"""


SEARCH_RECORD = """
        <record model="ir.ui.view" id="{side_id}_{id}_search">
            <field name="name">{side_id}_{id}</field>
            <field name="model">{top_id}.{side_id}_{id}</field>
            <field name="type">search</field>
            <field name="arch" type="xml">
                <search string="{id}">
                    {db_field_lines}
                </search>
            </field>
        </record>
"""

ACTION_RECORD = """
        <record model="ir.actions.act_window" id="action_{side_id}_{id}">
            <field name="name">{side_id}_{id}</field>
            <field name="res_model">{top_id}.{side_id}_{id}</field>
            <field name="view_type">form</field>
            <field name="view_id" ref="{side_id}_{id}_tree"/>
            <field name="view_mode">tree,form</field>
        </record>
"""

INSTALL_PY = """\
#!/usr/bin/python

import os, shutil
from VSS.conversion import XML_HEADER, XML_FOOTER, TOP_MENU

OE_NAME = 'Whole Herb Blends Test'
OE_VERSION = '0.1'
OE_CATEGORY = 'Generic Modules'
OE_DESCRIPTION = 'Testing automatic addon creation'
OE_AUTHOR = 'E & E'
OE_MAINTAINER = 'E'
OE_WEBSITE = 'www.openerp.com'
OE_DEPENDS = '["base",]'

module = {module!r}
module_id = module.lower().replace(' ','_')
dbs = {databases!r}
dir = Path({db_path!r})
dst = Path({addon_path!r})

try:
    shutil.rmtree(dst/module_id)
except OSError:
    pass
os.mkdir(dst/module_id)

csv_files = []
xml_files = ['"%s_view.xml",' % module_id]

for db in dbs:
    src = dir/db
    for file in src.listdir():
        if file.basename == 'create_%s' % db.lower() or file.ext == '.dbf':
            continue
        shutil.copy(src/file, dst/module_id)
        if file.ext == '.csv':
            csv_files.append('"' + file + '",')
        elif file.ext == '.xml':
            xml_files.append('"' + file + '",')

with open(dst/module_id/'__init__.py', 'w') as init:
    init.write('\\n'.join(['import %s' % db.lower() for db in dbs]))

with open(dst/module_id/'__openerp__.py', 'w') as oe:
    oe.write(
            "{{{{\\n"
            "    'name': {{name!r}},\\n"
            "    'version': {{ver!r}},\\n"
            "    'category': {{cat!r}},\\n"
            "    'description': {{desc!r}},\\n"
            "    'author': {{author!r}},\\n"
            "    'maintainer': {{maint!r}},\\n"
            "    'website': {{web!r}},\\n"
            "    'depends': {{dep}},\\n"
            "    'init_xml': [\\n"
            "        {{csv_files}}\\n"
            "        ],\\n"
            "    'update_xml': [\\n"
            "        {{xml_files}}\\n"
            "        ],\\n"
            "    'test': [],\\n"
            "    'installable': True,\\n"
            "    'active': False,\\n"
            "}}}}"
            .format(
                name=OE_NAME,
                ver=OE_VERSION,
                cat=OE_CATEGORY,
                desc=OE_DESCRIPTION,
                author=OE_AUTHOR,
                maint=OE_MAINTAINER,
                web=OE_WEBSITE,
                dep=OE_DEPENDS,
                csv_files='\\n        '.join(csv_files),
                xml_files='\\n        '.join(xml_files),
                )
            )
with open(dst/module_id/module_id+'_view.xml', 'w') as mod_xml:
    mod_xml.write(XML_HEADER)
    mod_xml.write(TOP_MENU.format(top_name={module!r}, top_id=module_id))
    mod_xml.write(XML_FOOTER)
"""

OE_AUTHOR = 'Emile van Sebille'
OE_MAINTAINER = 'Emile van Sebille'
OE_WEBSITE = 'www.openerp.com'
OE_DEPENDS = '["base",]'


