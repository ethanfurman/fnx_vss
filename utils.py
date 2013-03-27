import binascii
import string

String = str, unicode
Integer = int, long

def crc32(binary_data):
    "wrapper around binascii.crc32 that is consistent across python versions"
    return binascii.crc32(binary_data) & 0xffffffff

def translator(frm='', to='', delete='', keep=None):
    if len(to) == 1:
        to = to * len(frm)
    bytes_trans = string.maketrans(frm, to)
    if keep is not None:
        allchars = string.maketrans('', '')
        delete = allchars.translate(allchars, keep.translate(allchars, delete)+frm)
    uni_table = {}
    for src, dst in zip(frm, to):
        uni_table[ord(src)] = ord(dst)
    for chr in delete:
        uni_table[ord(chr)] = None
    def translate(s):
        if isinstance(s, unicode):
            s = s.translate(uni_table)
            if keep is not None:
                for chr in set(s) - set(keep):
                    uni_table[ord(chr)] = None
                s = s.translate(uni_table)
            return s
        else:
            return s.translate(bytes_trans, delete)
    return translate

spelled_out_numbers = set(['ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN','EIGHT','NINE','TEN'])

class BiDict(object):
    """
    key <=> value (value must also be hashable)
    """
    def __init__(yo, *args, **kwargs):
        _dict = yo._dict = dict()
        original_keys = yo._primary_keys = list()
        for k, v in args:
            if k not in original_keys:
                original_keys.append(k)
            _dict[k] = v
            if v != k and v in _dict:
                raise ValueError("%s:%s violates one-to-one mapping" % (k, v))
            _dict[v] = k
        for key, value in kwargs.items():
            if key not in original_keys:
                original_keys.append(key)
            _dict[key] = value
            if value != key and value in _dict:
                raise ValueError("%s:%s violates one-to-one mapping" % (key, value))
            _dict[value] = key
    def __contains__(yo, key):
        return key in yo._dict
    def __delitem__(yo, key):
        _dict = yo._dict
        value = _dict[key]
        del _dict[value]
        if key != value:
            del _dict[key]
        target = (key, value)[value in yo._primary_keys]
        yo._primary_keys.pop(yo._primary_keys.index(target))
    #def __getattr__(yo, key):
    #    return getattr(yo._dict, key)
    def __getitem__(yo, key):
        return yo._dict.__getitem__(key)
    def __iter__(yo):
        return iter(yo._primary_keys)
    def __len__(yo):
        return len(yo._primary_keys)
    def __setitem__(yo, key, value):
        _dict = yo._dict
        original_keys = yo._primary_keys
        if key in _dict:
            mapping = key, _dict[key]
        else:
            mapping = ()
        if value in _dict and value not in mapping:
            raise ValueError("%s:%s violates one-to-one mapping" % (key, value))
        if mapping:
            k, v = mapping
            del _dict[k]
            if k != v:
                del _dict[v]
            target = (k, v)[v in original_keys]
            original_keys.pop(original_keys.index(target))
        _dict[key] = value
        _dict[value] = key
        original_keys.append(key)
    def __repr__(yo):
        result = []
        for key in yo._primary_keys:
            result.append(repr((key, yo._dict[key])))
        return "BiDict(%s)" % ', '.join(result)
    def keys(yo):
        return yo._primary_keys[:]
    def items(yo):
        return [(k, yo._dict[k]) for k in yo._primary_keys]
    def values(yo):
        return [yo._dict[key] for key in yo._primary_keys]

class PropertyDict(object):
    """
    allows dictionary lookup using . notation
    allows a default similar to defaultdict
    """
    _internal = ['_illegal', '_values', '_default', '_order']
    _default = None
    def __init__(yo, *args, **kwargs):
        if 'default' in kwargs:
            yo._default = kwargs.pop('default')
        yo._values = _values = kwargs.copy()
        yo._order = _order = []
        yo._illegal = _illegal = tuple([attr for attr in dir(_values) if attr[0] != '_'])
        args = list(args)
        if len(args) == 1 and isinstance(args[0], tuple) and isinstance(args[0][0], tuple) and len(args[0][0]) == 2:
            for k, v in args[0]:
                if k in _illegal:
                    raise ValueError("%s is a reserved word" % k)
                _values[k] = v
                _order.append(k)
        else:
            for attr in args:
                if attr in _illegal:
                    raise ValueError("%s is a reserved word" % attr)
                elif isinstance(attr, dict):
                    attr.update(kwargs)
                    kwargs = attr
                    continue
                value = False
                _values[attr] = value
                _order.append(attr)
        for attr, value in sorted(kwargs.items()):
            if attr in _illegal:
                raise ValueError("%s is a reserved word" % attr)
            _values[attr] = value
            _order.append(attr)
    def __contains__(yo, key):
        return key in yo._values
    def __delitem__(yo, name):
        if name[0] == '_':
            raise KeyError("illegal key name: %s" % name)
        if name not in yo._values:
            raise KeyError("%s: no such key" % name)
        yo._values.pop(name)
        yo._order.pop(yo._order.index(name))
    def __delattr__(yo, name):
        if name[0] == '_':
            raise AttributeError("illegal key name: %s" % name)
        if name not in yo._values:
            raise AttributeError("%s: no such key" % name)
        yo._values.pop(name)
        yo._order.pop(yo._order.index(name))
    def __getitem__(yo, name):
        if name in yo._values:
            return yo._values[name]
        elif yo._default:
            yo._order.append(name)
            result = yo._values[name] = yo._default()
            return result
        raise KeyError("object has no key %s" % name)
    def __getattr__(yo, name):
        if name in yo._values:
            return yo._values[name]
        attr = getattr(yo._values, name, None)
        if attr is not None:
            return attr
        elif yo._default:
            yo._order.append(name)
            result = yo._values[name] = yo._default()
            return result
        raise AttributeError("object has no attribute %s" % name)
    def __iter__(yo):
        return iter(yo._order)
    def __len__(yo):
        return len(yo._values)
    def __setitem__(yo, name, value):
        if name in yo._internal:
            object.__setattr__(yo, name, value)
        elif name[0] == '_':
            raise KeyError("illegal attribute name: %s" % name)
        else:
            if name not in yo._values:
                yo._order.append(name)
            yo._values[name] = value
    def __setattr__(yo, name, value):
        if name in yo._internal:
            object.__setattr__(yo, name, value)
        elif name[0] == '_' or name in yo._illegal:
            raise AttributeError("illegal attribute name: %s" % name)
        else:
            if name not in yo._values:
                yo._order.append(name)
            yo._values[name] = value
    def __repr__(yo):
        return "PropertyDict((%s,))" % ', '.join(["(%r, %r)" % (x, yo._values[x]) for x in yo._order])
    def __str__(yo):
        return '\n'.join(["%r=%r" % (x, yo._values[x]) for x in yo._order])
    def keys(yo):
        return yo._order[:]
    def pop(yo, name):
        yo._order.pop(yo._order.index(name))
        return yo._values.pop(name)

class Sentinel(object):
    def __init__(yo, text):
        yo.text = text
    def __str__(yo):
        return "Sentinel: <%s>" % yo.text

building_subs = set([
    '#','APARTMENT','APT','BLDG','BUILDING','CONDO','FL','FLR','FLOOR','LOT','LOWER','NO','NUM','NUMBER',
    'RM','ROOM','SLIP','SLP','SPACE','SP','SPC','STE','SUITE','TRLR','UNIT','UPPER',
    ])
spelled_out_numbers = set(['ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN','EIGHT','NINE','TEN'])
caps_okay = set(['UCLA', 'OHSU', 'IBM', 'LLC', 'USA'])
lower_okay = set(['dba'])

alpha_num = translator(delete='.,:_#')
non_alpha_num = translator(delete="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,-")
any_digits = translator(keep='0123456789')
has_digits = any_digits
name_chars = translator(to=' ', keep="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' /")
name_chars_punc = translator(keep="' /")
grad_year = translator(keep="'0123456789")
vowels = translator(keep='aeiouyAEIOUY')
no_vowels = translator(delete='aeiouyAEIOUY')
has_lower = translator(keep="abcdefghijklmnopqrstuvwxyz")
has_upper = translator(keep="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
has_alpha = translator(keep="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")

mixed_case_names = {
    'aj'        : 'AJ',
    'bj'        : 'BJ',
    'cj'        : 'CJ',
    'deangelis' : 'DeAngelis',
    'decarlo'   : 'DeCarlo',
    'decosta'   : 'DeCosta',
    'decristoforo' : 'DeCristoforo',
    'deferrari' : 'DeFerrari',
    'degrandpre': 'DeGrandpre',
    'degroat'   : 'DeGroat',
    'delucia'   : 'DeLucia',
    'denardis'  : 'DeNardis',
    'denorch'   : 'DeNorch',
    'depaola'   : 'DePaola',
    'deprez'    : 'DePrez',
    'deshields' : 'DeShields',
    'deshon'    : 'DeShon',
    'desousa'   : 'deSousa',
    'devet'     : 'DeVet',
    'devida'    : 'DeVida',
    'devore'    : 'DeVore',
    'difrederico':'DiFrederico',
    'diponziano': 'DiPonziano',
    'jd'        : 'JD',
    'jj'        : 'JJ',
    'joann'     : 'JoAnn',
    'joanne'    : 'JoAnne',
    'jodee'     : 'JoDee',
    'jp'        : 'JP',
    'jumaal'    : 'JuMaal',
    'delany'    : 'DeLany',
    'demerritt' : 'DeMerritt',
    'dewaal'    : 'DeWaal',
    'lamon'     : 'LaMon',
    'lebarron'  : 'LeBarron',
    'leeanne'   : 'LeeAnne',
    'maryjo'    : 'MaryJo',
    'tachelle'  : 'TaChelle',
    'tj'        : 'TJ',
    }


def tuples(func):
    def wrapper(*args):
        print args
        if len(args) == 1 and not isinstance(args[0], String):
            args = args[0]
        print args
        result = tuple(func(*args))
        if len(result) == 1:
            result = result[0]
        return result
    #wrapper.__name__ = func.__name___
    wrapper.__doc__ = func.__doc__
    return wrapper


@tuples
def NameCase(*names):
    names = [n.strip() for n in names]
    if not any(names):
        return names
    final = []
    for name in names:
        pieces = name.lower().split()
        result = []
        for i, piece in enumerate(pieces):
            if '-' in piece:
                piece = ' '.join(piece.replace('-',' ').split())
                piece = '-'.join(NameCase(piece).split())
            elif alpha_num(piece) in ('i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x'):
                piece = piece.upper()
            elif piece in ('and', 'de', 'del', 'der', 'el', 'la', 'van', ):
                pass
            elif piece[:2] == 'mc':
                piece = 'Mc' + piece[2:].title()
            else:
                possible = mixed_case_names.get(piece, None)
                if possible is not None:
                    piece = possible
                else:
                    piece = piece.title()
                    if piece[-2:].startswith("'"):
                        piece = piece[:-1] + piece[-1].lower()
            result.append(piece)
        if result[0] == result[0].lower():
            result[0] = result[0].title()
        if result[-1] == result[-1].lower():
            result[-1] = result[-1].title()
        final.append(' '.join(result))
    return final


@tuples
def AddrCase(*fields):
    if not fields:
        return fields
    final = []
    for field in fields:
        result = []
        for word in field.split():
            uppered = word.upper()
            if uppered in ('N','NW','W','SW','S','SE','E','NE','PO','PMB','US'):
                result.append(uppered)
            elif word[:-2].isdigit() and word[-2:].lower() in ('st','nd','rd','th'):
                result.append(word.lower())
            elif has_alpha(word) and has_digits(word) or non_alpha_num(word):
                result.append(word)
            elif uppered[:2] == 'MC':
                result.append('Mc' + uppered[2:].title())
            else:
                result.append(word.title())
        final.append(' '.join(result))
    return final


@tuples
def BsnsCase(*fields):
    if not fields:
        return fields
    final = []
    for name in fields:
        print 0, final
        pieces = name.split()
        print 1, pieces
        #if len(pieces) <= 1:
        #    final.append(name)
        #    continue
        mixed = []
        last_piece = ''
        for piece in pieces:
            print 2, mixed
            #if has_lower(piece):
            #    return name
            lowered = piece.lower()
            if piece in caps_okay:
                mixed.append(piece)
            elif lowered in lower_okay:
                piece = lowered
                mixed.append(piece)
            elif lowered in ('a','an','and','of','the','at') and last_piece not in ('&','and'):
                mixed.append(lowered)
            elif lowered[:2] == 'mc':
                mixed.append('Mc' + lowered[2:].title())
            elif len(piece) == 2 and not vowels(piece):
                mixed.append(piece)
            else:
                number, suffix = lowered[:-2], lowered[-2:]
                if number.isdigit() and suffix in ('st','nd','rd','th'):
                    piece = piece[:-2].title() + suffix
                else:
                    piece = piece.title()
                    if piece[-2:].startswith("'"):
                        piece = piece[:-1] + piece[-1].lower()
                mixed.append(piece)
            last_piece = piece
        print mixed
        if mixed[0].lower() == mixed[0] and (mixed[0] not in lower_okay and mixed[0][-2:] not in ('st','nd','rd','th')):
            mixed[0] = mixed[0].title()
        final.append(' '.join(mixed))
    return final


def BusinessOrAddress(suspect):
    ususpect = suspect.upper().strip()
    company = address = ''
    m = Memory()
    if ususpect and \
       ((ususpect == 'GENERAL DELIVERY') or
        (ususpect.split()[0] in spelled_out_numbers or ususpect.split()[0] in building_subs) or
        (ususpect[:3] == 'PMB' and ususpect[3:4] in ('# 0123456789')) or
        (ususpect[:3] == 'MC:' or ususpect[:8] == 'MAILCODE') or 
        (ususpect[:4] == 'BOX ' and len(m.set(ususpect.split())) == 2 
            and (m.cell[1] in spelled_out_numbers or m.cell[1].isdigit() or len(m.cell[1]) < 2)) or
        ('BOX ' in ususpect and ususpect[:ususpect.index('BOX ')+4].replace('.','').replace(' ','')[:5] == 'POBOX') or
        ('DRAWER ' in ususpect and ususpect[:ususpect.index('DRAWER ')+7].replace('.','').replace(' ','')[:8] == 'PODRAWER') or
        ususpect.startswith('DRAWER ')):
           address = suspect
    else:
        for char in suspect:
            if char.isdigit():
                address = suspect
                break
        else:
            company = suspect
    return company, address


@tuples
def Rise(*fields):
    #fields = _fields(args)
    data = []
    empty = []
    for possible in fields:
        if possible:
            data.append(possible)
        else:
            empty.append(possible)
    results = data + empty
    return results


def Salute(name):
    pieces = name.split()
    for piece in pieces:
        if not piece.upper() in prefixi:
            return piece


@tuples
def Sift(*fields):
    #fields = _fields(args)
    data = []
    empty = []
    for possible in fields:
        if possible:
            data.append(possible)
        else:
            empty.append(possible)
    results = empty + data
    return results


class Sentinel(object):
    def __init__(yo, text):
        yo.text = text
    def __str__(yo):
        return "Sentinel: <%s>" % yo.text

_memory_sentinel = Sentinel("amnesiac")


class Memory(object):
    """
    allows attribute and item lookup
    allows a default similar to defaultdict
    remembers insertion order (alphabetic if not possible)
    """
    _default = None
    def __init__(yo, cell=_memory_sentinel, **kwargs):
        if 'default' in kwargs:
            yo._default = kwargs.pop('default')
        if cell is not _memory_sentinel:
            yo._order.append('cell')
            yo._values['cell'] = cell
        yo._values = _values = kwargs.copy()
        yo._order = _order = sorted(_values.keys())
        for attr, value in sorted(kwargs.items()):
            _values[attr] = value
            _order.append(attr)
    def __contains__(yo, key):
        return key in yo._values
    def __delitem__(yo, name):
        if name not in yo._values:
            raise KeyError("%s: no such key" % name)
        yo._values.pop(name)
        yo._order.pop(yo._order.index(name))
    def __delattr__(yo, name):
        if name not in yo._values:
            raise AttributeError("%s: no such key" % name)
        yo._values.pop(name)
        yo._order.pop(yo._order.index(name))
    def __getitem__(yo, name):
        if name in yo._values:
            return yo._values[name]
        elif yo._default:
            yo._order.append(name)
            result = yo._values[name] = yo._default()
            return result
        raise KeyError("object has no key %s" % name)
    def __getattr__(yo, name):
        if name in yo._values:
            return yo._values[name]
        elif yo._default:
            yo._order.append(name)
            result = yo._values[name] = yo._default()
            return result
        raise AttributeError("object has no attribute %s" % name)
    def __iter__(yo):
        return iter(yo._order)
    def __len__(yo):
        return len(yo._values)
    def __setitem__(yo, name, value):
        if name not in yo._values:
            yo._order.append(name)
        yo._values[name] = value
    def __setattr__(yo, name, value):
        if name in ('_values','_order'):
            object.__setattr__(yo, name, value)
        else:
            if name not in yo._values:
                yo._order.append(name)
            yo._values[name] = value
    def __repr__(yo):
        return "Memory(%s)" % ', '.join(["%r=%r" % (x, yo._values[x]) for x in yo._order])
    def __str__(yo):
        return "I am remembering...\n" + '\n\t'.join(["%r=%r" % (x, yo._values[x]) for x in yo._order])
    def keys(yo):
        return yo._order[:]
    def set(yo, cell=_memory_sentinel, **kwargs):
        _values = yo._values
        _order = yo._order
        if cell is not _memory_sentinel:
            if 'cell' not in _values:
                _order.append('cell')
            _values['cell'] = cell
            return cell
        for attr, value in sorted(kwargs.items()):
            _order.append(attr)
            _values[attr] = value
            return value


class PostalCode(object):
    """
    primarily for US and Canadian postal codes (ignores US +4)
    """

    def __init__(yo, postal):
        alpha2num = {
                'I' : 1,
                'O' : 0,
                'S' : 5,
                }
        num2alpha = {
                1   : 'I',
                0   : 'O',
                5   : 'S',
                }
        if len(postal.replace('-', '')) in (5, 9):
            yo.code = postal[:5]
        elif postal[:5].isdigit():
            yo.code = postal[:5]
        elif has_alpha(postal) and len(postal.replace(' ', '')) == 6:
            # alpha-num-alpha num-alpha-num
            postal = list(postal.replace(' ', '').upper())
            for i in (0, 2, 4):
                postal[i] = alpha2num.get(postal[i], postal[i])
            for i in (1, 3, 5):
                postal[i] = num2alpha.get(postal[i], postal[i])
            yo.code = "%s %s" % (''.join(postal[:3]), ''.join(postal[3:]))
        else:
            yo.code = postal

    def __eq__(yo, other):
        if not isinstance(other, (str, unicode, yo.__class__)):
            return NotImplemented
        if isinstance(other, yo.__class__):
            other = other.code
        return yo.code == other
    def __ne__(yo, other):
        return not yo.__eq__(other)
    def __str__(yo):
        return yo.code
