from __future__ import with_statement
from utils import PropertyDict

class EmbeddedNewlineError(Exception):
    "Embedded newline found in a quoted field"
    def __init__(self, state):
        Exception.__init__(self)
        self.state = state

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

