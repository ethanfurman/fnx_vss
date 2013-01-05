import binascii
import string

def crc32(binary_data):
    "wrapper around binascii.crc32 that is consistent across python versions"
    return binascii.crc32(binary_data) & 0xffffffff

def translator(frm='', to='', delete='', keep=None):
    if len(to) == 1:
        to = to * len(frm)
    trans = string.maketrans(frm, to)
    if keep is not None:
        allchars = string.maketrans('', '')
        delete = allchars.translate(allchars, keep.translate(allchars, delete)+frm)
    def translate(s):
        return s.translate(trans, delete)
    return translate

class BiDict(object):
    """
    key <=> value (no difference between them)
    """
    def __init__(yo, *args, **kwargs):
        _dict = yo._dict = dict()
        original_keys = yo.original_keys = list()
        for k, v in args:
            if k not in original_keys:
                original_keys.append(k)
            _dict[k] = v
        for key, value in kwargs.items():
            if key not in original_keys:
                original_keys.append(key)
            _dict[key] = value
            if value in _dict:
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
    def __getattr__(yo, key):
        return getattr(yo._dict, key)
    def __getitem__(yo, key):
        return yo._dict.__getitem__(key)
    def __setitem__(yo, key, value):
        _dict = yo._dict
        original_keys = yo.original_keys
        if key in _dict:
            mapping = key, _dict[key]
        else:
            mapping = ()
        if value in _dict and value not in mapping:
            raise ValueError("%s:%s violates one-to-one mapping" % (key, value))
        if mapping:
            del _dict[mapping[0]]
            if mapping[0] != mapping[1]:
                del _dict[mapping[1]]
            original_keys.pop(original_keys.index(key))
        _dict[key] = value
        _dict[value] = key
        original_keys.append(key)
    def __repr__(self):
        result = []
        for key in self.original_keys:
            result.append(repr((key, self._dict[key])))
        return "BiDict(%s)" % ', '.join(result)

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

alpha_num = translator(delete='.,:_#')

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

def NameCase(name):
    if not name:
        return name
    pieces = name.lower().split()
    result = []
    for i, piece in enumerate(pieces):
        if '-' in piece:
            piece = piece.replace('-',' ')
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
    return ' '.join(result)
