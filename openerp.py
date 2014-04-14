"various utilities for working with OpenErp"

from __future__ import division, print_function, with_statement

import openerplib
from VSS.time_machine import PropertyDict
from VSS.path import Path

execfile('/etc/openerp/VSS.conf')

# format of employee dbf file
#   login C(25)
#   password C(26)
#   emp_num N(6,0)
#   name C(50)
#   active L
#   groups C(50)
#   old_login C(25)
#   image_crc N(10,0)
#   email C(50)

try:
    with open(FILE_PATHS.db) as db:
        FILE_PATHS.db = db.readline().strip()
    del db
except Exception:
    pass

def adjust_permissions(oe_groups, allowed_groups, user):
    permissions = set(user.groups_id)
    for group_name, ints in oe_groups.items():
        if group_name.endswith('_default'):
            continue
        ints = set(ints)
        if group_name in allowed_groups:
            if not ints & permissions:  # add default if nothing already there
                permissions.add(oe_groups[group_name + '_default'][0])
        else:  # remove all priveleges for this group
            permissions -= ints
    return list(permissions)

def host_site(hostname, database, login='admin', password='admin'):
    hostname = {'wsg':'westernstatesglass.com','falcon':'falcon.tzo.com','salesinq':'demo.salesinq.com'}.get(hostname, hostname)
    result = PropertyDict()
    result.connection = conn = openerplib.get_connection(hostname=hostname, database=database, login=login, password=password)
    result.user_model = um = conn.get_model('res.users')
    users = um.read(um.search([('login','!=','""')]))
    users.extend(um.read(um.search([('login','!=','""'), ('active','!=','True')])))
    result.users = [PropertyDict(d) for d in users]
    result.group_model = gm = conn.get_model('res.groups')
    groups = gm.read(gm.search([('name','!=','""')]))
    result.groups = [PropertyDict(d) for d in groups]
    return result

def get_records(OE, model, domain=[], fields=None, max_qty=None):
    """get records from model

    domain <- OpenERP domain for selecting records
    fields <- fields to retrieve (otherwise all)
    max_qty <- raises ValueError if more than max_qty records retrieved

    returns a list of all records found
    """
    model = OE.conn.get_model(model)
    result = model.search_read(domain=domain, fields=fields)
    if max_qty is not None and len(result) > max_qty:
        raise ValueError('no more than %s records expected, but received %s' % (max_qty, len(results)))
    return [_normalize(r) for r in result]

def _normalize(d):
    'recursively convert each dict into a PropertyDict'
    res = PropertyDict()
    for key, value in d.items():
        if isinstance(value, dict):
            res[key] = _normalize(value)
        else:
            res[key] = value
    return res

def update_from_nightly():
    "routine to install nightly updates"
    # rename existing openerp out of the way

    # get list of possible .tar files from http://nightly.openerp.com/trunk/nightly/deb

    # download openerp_6.2dev-latest*.tar  (* may or may not be '-1')

    # extract contents of tar file, gathering exact folder name in the process

class EmbeddedNewlineError(Exception):
    "Embedded newline found in a quoted field"
    def __init__(self, state):
        Exception.__init__(self)
        self.state = state

    # run the setup.py file that was extracted

class OpenERPcsv(object):
    """csv file in OE format (utf-8, "-encapsulated, comma seperated)
    returns a list of str, bool, float, and int types, one row for each record
    Note: discards first record -- make sure it is the header!"""
    def __init__(self, filename):
        with open(filename) as source:
            self.data = source.readlines()
        self.row = 0        # skip header during iteration
        header = self.header = self._convert_line(self.data[0])
        self.types = []
        known = globals()
        for name in header:
            if '%' in name:
                name, type = name.split('%')
                if type in known:
                    self.types.append(known[type])
                else:
                    func = known['__builtins__'].get(type, None)
                    if func is not None:
                        self.types.append(func)
                    else:
                        raise ValueError("unknown type: %s" % type)
            else:
                self.types.append(None)
    def __iter__(self):
        return self
    def __next__(self):     # just plain 'next' in python 2
        try:
            self.row += 1
            line = self.data[self.row]
        except IndexError:
            raise StopIteration
        items = self._convert_line(line)
        if len(self.types) != len(items):
            raise ValueError('field/header count mismatch on line: %d' % self.row)
        result = []
        for item, type in zip(items, self.types):
            if type is not None:
                result.append(type(item))
            elif item.lower() in ('true','yes','on','t','y'):
                result.append(True)
            elif item.lower() in ('false','no','off','f','n'):
                result.append(False)
            else:
                for type in (int, float, lambda s: str(s.strip('"'))):
                    try:
                        result.append(type(item))
                    except Exception:
                        pass
                    else:
                        break
                else:
                    result.append(None)
        return result
    next = __next__
    @staticmethod
    def _convert_line(line, prev_state=None):
        line = line.strip() + ','
        if prev_state:
            fields = prev_state.fields
            word = prev_state.word
            encap = prev_state.encap
            skip_next = prev_state.skip_next
        else:
            fields = []
            word = []
            encap = False
            skip_next = False
        for i, ch in enumerate(line):
            if skip_next:
                skip_next = False
                continue
            if encap:
                if ch == '"' and line[i+1:i+2] == '"':
                    word.append(ch)
                    skip_next = True
                elif ch =='"' and line[i+1:i+2] in ('', ','):
                    while word[-1] == '\\n':
                        word.pop()
                    word.append(ch)
                    encap = False
                elif ch == '"':
                    raise ValueError(
                            'invalid char following ": <%s> (should be comma or double-quote)\n%r\n%s^' 
                            % (ch, line, ' ' * i)
                            )
                else:
                    word.append(ch)
            else:
                if ch == ',':
                    fields.append(''.join(word))
                    word = []
                elif ch == '"':
                    if word: # embedded " are not allowed
                        raise ValueError('embedded quotes not allowed:\n%s\n%s' % (line[:i], line))
                    encap = True
                    word.append(ch)
                else:
                    word.append(ch)
        if encap:
            word.pop()  # discard trailing comma
            if len(word) > 1:  # more than opening quote
                word[-1] = '\\n'
            current_state = PropertyDict(fields=fields, word=word, encap=encap, skip_next=skip_next)
            raise EmbeddedNewlineError(state=current_state)
        return fields

class UpdateFile(object):
    "loops through lines of filename *if it exists* (no error if missing)"
    def __init__(self, filename):
        try:
            with open(filename) as source:
                self.data = source.readlines()
        except IOError:
            self.data = []
        self.row = -1
    def __iter__(self):
        return self
    def __next__(self):     # just plain 'next' in python 2
        try:
            self.row += 1
            return self.data[self.row]
        except IndexError:
            raise StopIteration
    next = __next__

