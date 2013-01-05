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

import os, sys, shlex, shutil, subprocess, re, dbf, csv
from string import uppercase, lowercase
from VSS.decorators import LazyAttr, Missing
from VSS.utils import BiDict, PropertyDict, translator
from VSS.path import integrate
integrate(); del integrate
from VSS.iterators import OpenERPcsv, EmbeddedNewlineError
csv_line = OpenERPcsv._convert_line; del OpenERPcsv

strip_invalid_fieldname_chars = translator(keep=uppercase+lowercase+'_')

ONE2MANY = "'{oe_field}' : fields.one2many(\n"\
           "            '{module}.{target_table}',\n"\
           "            '{target_field}',\n"\
           "            {display_name!r},\n"\
           "            ),"
MANY2ONE = "'{oe_field}' : fields.many2one(\n"\
           "            '{module}.{target_table}',\n"\
           "            {display_name!r},\n"\
           "            select=True,\n"\
           "            ),"
BOOL = "'{oe_field}' : fields.boolean({display_name!r}),"
CHAR = "'{oe_field}' : fields.char({display_name!r}, size={size}),"
DATETIME = "'{oe_field}' : fields.datetime({display_name!r}),"
FLOAT = "'{oe_field}' : fields.float({display_name!r}),"
INTEGER = "'{oe_field}' : fields.integer({display_name!r}),"

class ConversionError(Exception):
    "all-purpose exception for conversion problems"

class AccessDB(object):
    dbs = PropertyDict()
    
    def __init__(yo, mdb_name, module):
        yo.module = module
        yo.module_id = module.lower().replace(' ','_')
        mdb_name = yo.diskname = Path(mdb_name)     # name of originating jet tables
        basename = yo.basename = mdb_name.basename.split('.', 1)[0].replace('-','')
        yo.dbs[basename] = yo       # keep track of
        yo.folder = mdb_name.path/basename #mdb_name.strip_ext()
        if os.path.exists(yo.folder):
            shutil.rmtree(yo.folder)
        os.mkdir(yo.folder)
        if yo.folder not in sys.path:
            sys.path.insert(0, yo.folder)
        tables = yo.tables = PropertyDict(default=PropertyDict)     # tablename -> various bits about the table
        jet_tables = yo.jet_tables = BiDict()                   # python table name <-> jet table name
        output = get_external_command_output("mdb-schema --no-not-null %s oracle" % mdb_name).split('\n')
        in_table = False
        relations = PropertyDict(default=list)   # tablename -> relations involving that table
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
                    tn1 = line[tn1_start:tn1_end].replace(' ','_')
                    fn1 = line[fn1_start:fn1_end] #.replace(' ','_')
                    tn2 = line[tn2_start:tn2_end].replace(' ','_')
                    fn2 = line[fn2_start:fn2_end] #.replace(' ','_')
                    fn1, fn2 = fix_fieldname(fn1), fix_fieldname(fn2)
                    if tn1 not in jet_tables or tn2 not in jet_tables:
                        print "%s: either %s or %s (or both) are not valid tables" % (mdb_name, tn1, tn2)
                        continue
                    relation = Jet2Dbf_Relation((tn1, fn1), (tn2, fn2), yo)
                    relations[tn1].append(relation)
                    relations[tn2].append(relation)
                    continue
                elif line.startswith('-- Relationship from '):      # linux mint 14 mdb tool
                    tn1, fn1, tn2, fn2 = re.findall('"([^"]*)"', line)
                    tn1, tn2 = tn1.replace(' ','_'), tn2.replace(' ','_')
                    fn1, fn2 = fix_fieldname(fn1), fix_fieldname(fn2)
                    if tn1 not in jet_tables or tn2 not in jet_tables:
                        print "%s: either %s or %s (or both) are not valid tables" % (mdb_name, tn1, tn2)
                        continue
                    relation = Jet2Dbf_Relation((tn1, fn1), (tn2, fn2), yo)
                    relations[tn1].append(relation)
                    relations[tn2].append(relation)
                    continue
                if not line.startswith('CREATE TABLE '):
                    continue
                jet_table_name = line[13:].strip('"')
                table_name = jet_table_name.replace(' ','_')
                if table_name.startswith(("_", "MSys", "Switchboard", "Errors", "TMPCL", "Paste", "~")):
                    continue
                jet_tables[table_name] = jet_table_name
                in_table = True
                tables[table_name].jet_fields = list()
                tables[table_name].oe_jet_map = BiDict()
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
            tables[table_name].oe_jet_map[oe_field_name] = jet_field_name
            tables[table_name].jet_fields.append((jet_field_name, field_def))
            tables[table_name].jet_name = jet_table_name
        for table_name, data in tables.items():
            data.relations = list(set(relations[table_name]))

    def __repr__(yo):
        return "AccessDB(%r)" % yo.diskname
    
    def _close(yo):
        "closes all dbf tables -- for testing only"
        for _, obj in yo.tables.items():
            obj.dbf.close()
    
    def _open(yo):
        "opens all dbf tables -- for testing only"
        for _, obj in yo.tables.items():
            obj.dbf.open()
    
    def create_stage2(yo):
        "step 3: create the *.stage2.[dbf|py] files"
        module = yo.module

        database = yo.basename
        tables = []
        for oe_name, obj in yo.tables.items():
            tables.append("%s=%r," % (oe_name.lower(), obj.jet_name))
        with open(yo.folder/'create_%s.py' % database.lower(), 'w') as stage2:
            stage2.write(template_header.format(
                    module=module,
                    database=database,
                    tables='\n        '.join(tables),
                    ))
            #stage2.write(SIDE_MENU.format(top_id=yo.module_id
            for table_name, obj in yo.tables.items():
                # doc string
                doc_str = '\n    '.join(yo.detail(table_name).split('\n'))
                # relations
                relations = ["%r," % rel for rel in obj.relations]
                # links from fields to tables
                rel_links = list()
                for rel in obj.relations:
                    if table_name == rel.src_table:
                        offset, table = rel.link_fields.copy().popitem()
                        table = yo.jet_tables[table]
                        rel_links.append("%3s : %r," % (offset, table))
                rel_links.sort()
                if rel_links:
                    rel_links = [''] + rel_links + ['']
                # fields to be dropped from final csv files
                skip_fields = tuple(["%s" % skip for skip in sorted(obj.skip_fields)])
                fields = obj.oe_jet_map.original_keys
                if fields[-1] == 'oe_id':
                    fields.insert(0, fields.pop())
                # map of final csv file and py field setup
                csv_map = []
                py_defs = []
                with obj.dbf:
                    record = obj.dbf.create_template(obj.dbf[1])
                for i, (jet, csv_field, data) in enumerate(zip(obj.jet_fields, fields, record)):
                    csv_field = csv_field.lower()
                    jet_name, jet_def = jet
                    jet_def, jet_size = fix_fieldtype(jet_def)
                    if jet_size:
                        jet_line = '(%r, %r, %r),' % (jet_def, jet_name, jet_size)
                    else:
                        jet_line = '(%r, %r),' % (jet_def, jet_name)
                    if csv_field == 'oe_id':
                        csv_field = 'id'
                        jet_line = '(),'
                    elif any([rel.src_table == table_name and rel.src_field.lower() == csv_field for rel in obj.relations]):
                        if csv_field[-3:] != '_id':
                            csv_field += '_id'
                        jet_line = "('many2one', %r)," % jet_name
                        csv_field += '/id'
                    elif (('f%d' % i) in obj.skip_fields
                    and any([rel.tgt_table == table_name and rel.tgt_field.lower() == csv_field for rel in obj.relations])):
                        continue
                    csv_map.append("%-30r, # %s" % (csv_field, data))
                    py_defs.append(jet_line)
                stage2.write(stage2_subclass.format(
                    db=table_name,
                    doc_str=doc_str,
                    jet_name=obj.jet_name,
                    dbf_file=obj.dbf.filename,
                    relations='\n        '.join(relations),
                    field_relation_links='\n        '.join(rel_links),
                    skip_fields=skip_fields,
                    csv_map='\n        '.join(csv_map),
                    py_defs='\n        '.join(py_defs),
                    ))
                stage2.write(
                        '{name} = {name}()\n'
                        '{name}.final_csv()\n'
                        'final_py.append({name}.create_py())\n'
                        'body = {name}.create_xml()\n'
                        'final_xml_body.append(body)\n'
                        '\n'.format(name=table_name))
            stage2.write(template_footer.format(basename=(yo.folder/database.lower())))
            return yo.folder, 'create_%s' % database.lower()

    def detail(yo, tablename):
        "'Blend Categories' --> 'Blend_Categories'"
        jet_field_defs = yo.tables[tablename].jet_fields
        relations = yo.tables[tablename].relations
        rel_to = []
        rel_from = []
        for rel in relations:
            if tablename == rel.src_table:
                rel_from.append("%s -> %s:%s"  % (rel.src_field, rel.tgt_table, rel.tgt_field))
            elif tablename == rel.tgt_table:
                rel_to.append("%s <- %s:%s" % (rel.tgt_field, rel.src_table, rel.src_field))
            else:
                raise ValueError("%r does not seem to belong to table %r" % (rel, tablename))
        fields = []
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
        return result

    def field_size(yo, name, jet_def):
        "VARCHAR (2) --> 2; NUMBER (4) --> 20"
        size = 30
        if jet_def.startswith('VARCHAR2'):
            size = max(size, int(re.search('\(\d+\)', jet_def).group()[1:-1]) + 12)
        if name.endswith('_ID'):
            size = max(size, 50)
        return size
    
    def jet2dbf(yo, tables=None):
        "step 1: create intermediate dbf files from jet files"
        if tables is None:
            tables = yo.tables.keys()
        elif isinstance(tables, (str, unicode)):
            tables = (tables, )
        for table in tables:
            command = 'mdb-export -D "%Y-%m-%d %H:%M:%S" ' + "%s '%s'" % (yo.diskname, yo.jet_tables[table])
            csv_contents = get_external_command_output(command)
            if not csv_contents:
                #command = 'mdb-export -S -D "%Y-%m-%d %H:%M:%S" ' + "%s '%s'" % (mdb_file, table.replace('_',' '))
                #csv_contents = get_external_command_output(command)
                #if not csv_contents:
                    raise ValueError("unable to get data for %s:%s" % (yo.diskname, yo.jet_tables[table]))
            csv_contents = csv_contents.strip().split('\n')
            csv_file = yo.folder/"%s.stage1.csv" % table
            oe_id = "oe-id_"
            need_oe_id = False
            yo.tables[table].skip_fields = set()
            if yo.tables[table].jet_fields[0] != ('oe_ID', 'VARCHAR2 (50)'):
                for rel in yo.tables[table].relations:
                    if table == rel.tgt_table:
                        need_oe_id = True
                        yo.tables[table].jet_fields.insert(0, ('oe_ID', 'VARCHAR2 (50)'))
                        yo.tables[table].oe_jet_map['oe_id'] = 'oe_ID'
                        break
            else:
                need_oe_id = True
            if need_oe_id:
                for rel in yo.tables[table].relations:
                    if table == rel.tgt_table:
                        for i, (field_name, field_def) in enumerate(yo.tables[table].jet_fields):
                            if yo.tables[table].oe_jet_map[field_name] == rel.tgt_field:
                                if field_def.startswith('NUMBER'):
                                    yo.tables[table].skip_fields.add('f%d' % i)
                                break
            yo.tables[table].fields = BiDict()
            dbf_fields = []
            field_names = dict()
            for i, (field_name, field_def) in enumerate(yo.tables[table].jet_fields):
                field_name = yo.tables[table].oe_jet_map[field_name]
                size = yo.field_size(field_name, field_def)
                dbf_field_name = 'f%d' % i
                field_names[field_name] = dbf_field_name
                dbf_fields.append('%s C(%d)' % (dbf_field_name, size))
                yo.tables[table].fields[field_name] = dbf_field_name
            for rel in yo.tables[table].relations:
                if table == rel.src_table:
                    yo.tables[table].skip_fields.add(field_names[rel.src_field])
                    link_field = field_names[rel.src_field] + '_link'
                    offset = int(field_names[rel.src_field][1:])
                    dbf_fields.append("%s C(75)" % link_field)
                    rel.link_fields[offset] = rel.tgt_table
                    field_name = yo.tables[table].jet_fields[offset][0] + '_Link'
                    yo.tables[table].fields[field_name] = link_field
            dbf_table = yo.tables[table].dbf = dbf.Table(
                    csv_file.strip_ext(),
                    dbf_fields,
                    dbf_type='clp',
                    codepage='utf8',
                    default_data_types={'C':dbf.Char},
                    )
            with dbf_table:
                state = None
                for i, line in enumerate(csv_contents):
                    final_line = []
                    if need_oe_id:
                        final_line.append("%s%d" % (oe_id, i))
                    try:
                        for i, value in enumerate(csv_line(line, prev_state=state)):
                            final_line.append(value.decode('utf8', 'ignore'))
                    except EmbeddedNewlineError, exc:
                        state = exc.state
                    else:
                        dbf_table.append(tuple(final_line))
                        state = None
    def relink_dbfs(yo):
        "step 2: reestablish links from jet files in dbf files"
        tables = []
        for table_name, data in yo.tables.items():
            tables.append(data.dbf)
        with dbf.Tables(tables):
            # first, create all the indices
            for table_name, data in yo.tables.items():
                for rel in data.relations:
                    rel.create_index()
            # then, use them for relinking
            while "broken links may exist":
                broken = False
                for table_name, data in yo.tables.items():
                    for rel in data.relations:
                        if table_name == rel.src_table:
                            for rec in dbf.Process(data.dbf[1:]):
                                try:
                                    match = rel[rec]
                                except KeyError, exc:
                                    broken = True
                                    print dbf.source_table(rec).filename, '|'.join(rec)
                                    dbf.delete(rec)
                                else:
                                    if dbf.is_deleted(match):
                                        broken = True
                                        print dbf.source_table(rec).filename, '|'.join(rec)
                                        dbf.delete(rec)
                                    else:
                                        rec[rel.tgt_dbf_field] = match.f0
                else:
                    if not broken:
                        break
                    for data in yo.tables.values():
                        data.dbf.pack()
                        if data.jet_fields[0][0] == 'oe_ID':
                            for i, rec in enumerate(data.dbf):
                                with rec:
                                    rec[0] = "oe-id_%d" % i


class Jet2Dbf_Relation(object):
    "mirrors Access relations in dbf tables; requires an instance of AccessDB for full functionality"
    def __new__(cls, src, tgt, access_db=None):
        if (len(src) != 2 or  len(tgt) != 2):
            raise TypeError("Jet2Dbf_Relation should be called with ((src_table, src_field), (tgt_table, tgt_field))")
        obj = object.__new__(cls)
        if access_db is not None:
            obj.access_db = access_db
        obj._src_table, obj._src_field = src
        obj._tgt_table, obj._tgt_field = tgt
        obj._tables = dict()
        obj.link_fields = dict()
        return obj
    def __eq__(yo, other):
        if (yo.access_db == other.access_db
        and yo._src_table == other._src_table
        and yo._src_field == other._src_field
        and yo._tgt_table == other._tgt_table
        and yo._tgt_field == other._tgt_field):
            return True
        return False
    def __getitem__(yo, record):
        key = (record[yo.src_dbf_field], )
        return yo.index[key]
    def __hash__(yo):
        return hash((yo._src_table, yo._src_field, yo._tgt_table, yo._tgt_field))
    def __ne__(yo, other):
        if (yo.access_db != other.access_db
        or  yo._src_table != other._src_table
        or  yo._src_field != other._src_field
        or  yo._tgt_table != other._tgt_table
        or  yo._tgt_field != other._tgt_field):
            return True
        return False
    def __repr__(yo):
        return "Jet2Dbf_Relation((%r, %r), (%r, %r))" % (yo._src_table, yo._src_field, yo._tgt_table, yo._tgt_field)
    @Missing
    def access_db(yo):
        return "place holder for an Access_DB()"
    @LazyAttr
    def source(yo):
        yo.source = attr = yo.access_db.tables[yo._src_table].dbf
        return attr
    @property
    def src_table(yo):
        "name of source table"
        return yo._src_table
    @property
    def src_field(yo):
        "name of source field"
        return yo._src_field
    @LazyAttr
    def target(yo):
        yo.target = attr = yo.access_db.tables[yo._tgt_table].dbf
        return attr
    @property
    def tgt_table(yo):
        "name of target table"
        return yo._tgt_table
    @property
    def tgt_field(yo):
        "name of target field"
        return yo._tgt_field
    def create_index(yo):
        for i, jet_def in enumerate(yo.access_db.tables[yo._tgt_table].jet_fields):
            jet_field = jet_def[0]
            adjusted_field = yo.access_db.tables[yo._tgt_table].oe_jet_map[yo.tgt_field]
            if jet_field == adjusted_field:
                field_offset = tgt_offset = i
                break
        else:
            raise ValueError("unable to locate field %s in table %s" % (yo.tgt_field, yo.tgt_table))
        for i, jet_def in enumerate(yo.access_db.tables[yo._src_table].jet_fields):
            jet_field = jet_def[0]
            adjusted_field = yo.access_db.tables[yo._src_table].oe_jet_map[yo.src_field]
            if jet_field == adjusted_field:
                src_offset = i
                break
        else:
            raise ValueError("unable to locate field %s in table %s" % (yo.tgt_field, yo.tgt_table))
        def index(record, offset=field_offset):
            return record[offset]
        index.__doc__ = "%s:%s --> %s:%s" % (yo._src_table, yo._src_field, yo._tgt_table, yo._tgt_field)
        yo.index = yo.target.create_index(index)
        yo.src_dbf_field = "f%d" % i
        yo.tgt_dbf_field = "f%d_link" % i
        source = dbf.List(yo.source, key=lambda rec, field=src_offset: rec[field])
        target = dbf.List(yo.target, key=lambda rec, field=tgt_offset: rec[field])
        if len(source) != len(yo.source):
            yo._tables[yo._src_table] = 'many'
        else:
            yo._tables[yo._src_table] = 'one'
        if len(target) != len(yo.target):
            yo._tables[yo._tgt_table] = 'many'
        else:
            yo._tables[yo._tgt_table] = 'one'
    def one_or_many(yo, table):
        return yo._tables[table]

class Stage2(object):
    "base class for stage 2 conversions"

    def __init__(yo):
        dbf_file = Path(yo.dbf_file)
        final_dbf = dbf_file.path/('%s.%s_%s.dbf' % (yo.module_id, yo.database_id, yo.tables[yo.jet_name]))
        yo.input = dbf.Table(
                dbf_file,
                dbf_type='clp',
                default_data_types={'C':dbf.Char},
                )
        fields = yo.input.field_names
        for field in yo.skip_fields:
            fields.pop(fields.index(field))
        fields.sort(key=lambda name: int(name.split('_')[0][1:]))
        structure = yo.input.structure(fields)
        yo.output = dbf.Table(
                final_dbf,
                structure,
                dbf_type='clp',
                codepage='utf8',
                default_data_types={'C':dbf.Char},
                )
        yo.field_lookup = field_lookup = dict()
        for i, field in enumerate(yo.input.field_names):
            if field in yo.skip_fields:
                field_lookup[i] = None
            elif field.endswith('_link'):
                field_lookup[int(field.split('_')[0][1:])] = i
                field_lookup[i] = None
            else:
                field_lookup[i] = i
        yo.one2many = []

    def final_csv(yo):
        "step 1"
        with dbf.Tables(yo.input, yo.output):
            yo.output.append(yo.csv_map)
            for record in yo.input[1:]:
                data = []
                self = "%s_%s_%s_" % (yo.module_id, yo.database_id, yo.tables[yo.jet_name])
                for i, field in enumerate(record):
                    offset = yo.field_lookup[i]
                    if offset is None:
                        continue
                    field = record[offset]
                    if i in yo.field_relation_links:
                        if field[:6] != 'oe-id_':
                            raise ValueError("field %d: incorrect data -> %s" % (i, field))
                        field = "%s_%s_%s_%s" % (
                                yo.module_id,
                                yo.database_id,
                                yo.tables[yo.field_relation_links[i]],
                                field[6:],
                                )
                    elif i == 0 and field[:6] == 'oe-id_':
                        field = self + field[6:]
                    data.append(field)
                yo.output.append(tuple(data))
            filename = Path(yo.output.filename).strip_ext() + '.csv'
            with open(filename, 'w') as csv_file:
                for record in yo.output:
                    fields = []
                    for field in record:
                        if field and field[0] == field[-1] == '"':
                            field = '"%s"' % field[1:-1].replace('"','""')
                        fields.append(field.encode('utf8'))
                    csv_file.write(','.join(fields))
                    csv_file.write('\n')

    def create_py(yo):
        "step 2"
        name = "%s.%s_%s" % (yo.module_id, yo.database_id,  yo.tables[yo.jet_name])
        desc = "table data for %s" % name
        columns = ['    _columns = {']
        for i, (oe_field, col_def) in enumerate(zip(yo.csv_map, yo.py_field_defs)):
            if not col_def:
                continue    # primarily to skip 'id' columns
            elif col_def[0] == 'many2one':
                subst = PropertyDict()
                subst.oe_field = oe_field[:-3]
                subst.display_name = col_def[1]
                subst.module = yo.module_id
                subst.target_table = "%s_%s" % (yo.database_id, yo.tables[yo.field_relation_links[i]])
                columns.append(MANY2ONE.format(**subst))
            elif col_def[0] == 'char':
                subst = PropertyDict()
                subst.oe_field = oe_field
                subst.display_name = col_def[1]
                subst.size = col_def[2]
                columns.append(CHAR.format(**subst))
            else:
                subst = PropertyDict()
                subst.oe_field = oe_field
                subst.display_name = col_def[1]
                columns.append(globals()[col_def[0].upper()].format(**subst))
        for rel in [rel for rel in yo.relations if rel.tgt_table == yo.__class__.__name__]:
            subst = PropertyDict()
            subst.oe_field = yo.tables[rel.src_table] + '_ids'
            subst.module = yo.module_id
            subst.target_table = "%s_%s" % (yo.database_id, yo.tables[rel.src_table])
            subst.target_field = rel.src_field.lower()
            if subst.target_field[-3:] != '_id':
                subst.target_field += '_id'
            subst.display_name = rel.src_table
            columns.append(ONE2MANY.format(**subst))
            yo.one2many.append(subst.oe_field)
        result = []
        result.append('class %s(osv.Model):' % yo.tables[yo.jet_name])
        result.append('    _name = %r' % name)
        result.append('    _description = %r' % desc)
        result.append('\n        '.join(columns))
        result.append('        }')
        result.append('%s()' % yo.tables[yo.jet_name])
        return '\n'.join(result)

    def create_xml(yo):
        "step 3"
        final = []
        top_name = yo.module
        top_id = top_name.lower().replace(' ','_')
        side_name = yo.database
        side_id = side_name.lower().replace(' ','_')
        table_id = yo.tables[yo.jet_name]
        fields = []
        field_ids = []
        for f in yo.csv_map:
            if f == 'id':
                continue
            else:
                if f.endswith('/id'):
                    f = f[:-3]
                fields.append(FIELD_ENTRY.format(name=f))
        for field in yo.one2many:
            field_ids.append('    ' + FIELD_ENTRY.format(name=field))
        if field_ids:
            field_ids.insert(0, '<page string="TBD">')
            field_ids.append('</page>')
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
    fieldname = fieldname.replace('#','Number').replace('%','Percent')
    if fieldname.endswith('ID') and not fieldname.endswith('_ID'):
        fieldname = fieldname[:-2] + '_ID'
    fieldname = strip_invalid_fieldname_chars(fieldname).strip('_')
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
            new_type = 'integer'
        elif fieldtype.startswith('VARCHAR2'):
            new_type, size = fieldtype.split()
            new_type = {'NUMBER':'integer','VARCHAR2':'char'}[new_type]
            size = size.strip('()')
        else:
            raise ConversionError("unknown field type: %s" % fieldtype)
    return new_type, size

def get_external_command_output(command):
    args = shlex.split(command)
    ret = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
    return ret

template_header = """\
import dbf
from VSS.conversion import Jet2Dbf_Relation, Stage2, ONE2MANY, MANY2ONE, BOOL, CHAR, FLOAT, INTEGER
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

final_py = []
final_xml_header = [XML_HEADER]
final_xml_header.append(SIDE_MENU.format(
    side_name=DATABASE,
    side_id=DATABASE.lower().replace(' ','_'),
    top_id=MODULE.lower().replace(' ','_'),
    ))
final_xml_body = []
"""

template_footer = """
with open("{basename}.py", "w") as final:
    final.write("from osv import osv, fields\\n\\n")
    final.write("\\n\\n".join(final_py))

with open("{basename}_view.xml", "w") as final:
    final.write("\\n".join(final_xml_header))
    final.write("\\n")
    final.write("\\n".join(final_xml_body))
    final.write("\\n")
    final.write(XML_FOOTER)
"""

stage2_subclass = '''
class {db}(Stage2):
    """
    {doc_str}
    """
    module = MODULE
    module_id = MODULE_ID
    database = DATABASE
    database_id = DATABASE_ID
    tables = TABLES
    jet_name = {jet_name!r}
    dbf_file = {dbf_file!r}
    skip_fields = {skip_fields!r}
    relations = (
        {relations}
        )
    field_relation_links = {{{field_relation_links}}}
    csv_map = (
        {csv_map}
        )
    py_field_defs = (
        {py_defs}
        )
'''
'''    field_def = {{
        {field_def}
        }}
'''

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
                    {db_field_lines}
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
from VSS.path import integrate; integrate(); del integrate

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
    for file in os.listdir(src):
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
