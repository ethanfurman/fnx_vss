from __future__ import absolute_import, with_statement

import __builtin__
import binascii
import dbf
import inspect
import random
import string
import sys
import threading
from datetime import timedelta
from math import floor
from socket import socket, AF_INET, SOCK_DGRAM
from dbf import Date, Time, baseinteger, basestring
from VSS.time_machine import Sentinel, simplegeneric

one_day = timedelta(1)

def Table(fn, *args, **kwds):
    'default to Clipper, Char, Logical, etc'
    data_types = {
            'C' : dbf.Char,
            'L' : dbf.Logical,
            'D' : dbf.Date,
            }
    if 'default_data_types' in kwds:
        data_types.update(kwds['default_data_types'])
    kwds['default_data_types'] = data_types
    if (args or kwds.get('field_specs') is not None):
        new_table = True
    else:
        new_table = False
    if 'dbf_type' not in kwds:
        try:
            possibilities = dbf.guess_table_type(fn)
        except dbf.DbfError:
            possibilities = [('clp',)]
        if len(possibilities) != 1 or 'clp' in [t[0] for t in possibilities]:
            kwds['dbf_type'] = 'clp'
    if new_table:
        kwds['codepage'] = 'utf8'
    return dbf.Table(fn, *args, **kwds)


def days_per_month(year):
    return (dbf.days_per_month, dbf.days_per_leap_month)[dbf.is_leapyear(year)]


def all_equal(iterator, test=None):
    '''if `test is None` do a straight equality test'''
    it = iter(iterator)
    if test is None:
        try:
            target = next(it)
            test = lambda x: x == target
        except StopIteration:
            return True
    for item in it:
        if not test(item):
            return False
    return True


def bb_text_to_date(text):
    mm, dd, yy = map(int, (text[:2], text[2:4], text[4:]))
    if any([i == 0 for i in (mm, dd, yy)]):
        Date()
    yyyy = yy + 2000
    return Date(yyyy, mm, dd)


def currency(number):
    if not isinstance(number, (baseinteger, basestring)):
        raise ValueError('currency only works with integer and string types (received %s %r )' % (type(number), number))
    if isinstance(number, baseinteger):
        number = str(number)
        number = '0' * (3 - len(number)) + number
        number = number[:-2] + '.' + number[-2:]
    elif isinstance(number, basestring):
        number = int(number.replace('.',''))
    return number

_trans_sentinel = Sentinel('no strip argument')
def translator(frm='', to='', delete='', keep=None, strip=_trans_sentinel, compress=False):
    replacement = None
    if len(to) == 1:
        if frm == '':
            replacement = to
            to = ''
        else:
            to = to * len(frm)
    bytes_trans = string.maketrans(frm, to)
    if keep is not None:
        allchars = string.maketrans('', '')
        delete = allchars.translate(allchars, keep.translate(allchars, delete)+frm)
        if replacement is not None:
            frm = delete
            to = replacement * len(delete)
            delete = ''
            bytes_trans = string.maketrans(frm, to)
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
                    uni_table[ord(chr)] = replacement
                s = s.translate(uni_table)
        else:
            s = s.translate(bytes_trans, delete)
        if strip is not _trans_sentinel:
            s = s.strip(strip)
        if replacement and compress:
            s = replacement.join([p for p in s.split(replacement) if p])
        return s
    return translate

def contains_any(container, *targets):
    for t in targets:
        if t in container:
            return True
    return False

def crc32(binary_data):
    "wrapper around binascii.crc32 that is consistent across python versions"
    return binascii.crc32(binary_data) & 0xffffffff


def unabbreviate(text, abbr):
    """
    returns line lower-cased with standardized abbreviations
    text: text to work with
    abbr: dictionary of abbreviations to use
    """
    text = text.lower().replace(u'\uffa6', ' ')
    words = text.split()
    final = []
    for word in words:
        final.append(abbr.get(word, word))
    return ' '.join(final)


def tuples(func):
    def wrapper(*args):
        if len(args) == 1 and not isinstance(args[0], basestring):
            args = args[0]
        result = tuple(func(*args))
        if len(result) == 1:
            result = result[0]
        return result
    #wrapper.__name__ = func.__name___
    wrapper.__doc__ = func.__doc__
    return wrapper


class xrange(object):
    '''
    accepts arbitrary objects to use to produce sequences
    '''

    def __init__(self, start, stop=None, step=None, count=None, epsilon=None):
        if stop is not None and count is not None:
            raise ValueError("cannot specify both stop and count")
        if stop is None and count is None:
            # check for default start based on type
            start, stop = None, start
            try:
                start = type(stop)(0)
            except Exception:
                raise ValueError("start must be specified for type %r" %
                        type(stop))
        if start is None:
            ref = type(stop)
        else:
            ref = type(start)
        if step is None:
            try:
                step = ref(1)
            except TypeError:
                raise ValueError("step must be specified for type %r" %
                        type(stop))
        if epsilon is None:
            try:
                epsilon = .5 * step
                if not isinstance(epsilon, ref):
                    raise TypeError
            except TypeError:
                try:
                    epsilon = ref(0)
                except Exception:
                    pass
        self.start = self.init_start = start
        self.stop = stop
        self.step = step
        self.count = self.init_count = count
        self.epsilon = epsilon

    def __contains__(self, value):
        start, stop, step = self.start, self.stop, self.step
        count = self.count
        if callable(step):
            raise TypeError(
                    "range with step %r does not support containment checks" %
                    step)
        try:
            value % step
        except TypeError:
            raise TypeError(
                    "range of %s with step %s does not support "
                    "containment checks" % (type(start), type(step)))
        if stop is None:
            stop = start + (step * count)
        if stop == start:
            return False
        if start < stop and not start <= value < stop:
            return False
        elif stop < start and not stop >= value > stop:
            return False
        try:
            distance = value - start
            return distance % step == 0.0
        except TypeError:
            raise TypeError(
                    "range of %s with step %s does not support "
                    "containment checks" % (type(start), type(step)))

    def __iter__(self):
        start = self.start
        stop = self.stop
        step = self.step
        count = self.count
        epsilon = self.epsilon
        if stop is not None and epsilon is not None:
            stop -= epsilon
        value = None
        i = -1
        while 'more values to yield':
            i += 1
            if callable(step):
                if i:
                    value = step(start, i, value)
                else:
                    value = start
            else:
                value = start + i * step
            if count is not None:
                if count < 1:
                    break
                count -= 1
            else:
                if stop > start and value >= stop:
                    break
                if stop < start and value <= stop:
                    break
            yield value

    def __repr__(self):
        values = [
                '%s=%s' % (k,v)
                for k,v in (
                    ('start',self.start),
                    ('stop',self.stop),
                    ('step', self.step),
                    ('count', self.count),
                    ('epsilon', self.epsilon),
                    )
                if v is not None
                ]
        return '<%s(%s)>' % (self.__class__.__name__, ', '.join(values))


_memory_sentinel = Sentinel("amnesiac")

class Memory(object):
    """
    allows attribute and item lookup
    allows a default similar to defaultdict
    remembers insertion order (alphabetic if not possible)
    """

    _default = None

    def __init__(yo, cell=_memory_sentinel, **kwds):
        if 'default' in kwds:
            yo._default = kwds.pop('default')
        if cell is not _memory_sentinel:
            yo._order.append('cell')
            yo._values['cell'] = cell
        yo._values = _values = kwds.copy()
        yo._order = _order = sorted(_values.keys())
        for attr, value in sorted(kwds.items()):
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

    def set(yo, cell=_memory_sentinel, **kwds):
        _values = yo._values
        _order = yo._order
        if cell is not _memory_sentinel:
            if 'cell' not in _values:
                _order.append('cell')
            _values['cell'] = cell
            return cell
        for attr, value in sorted(kwds.items()):
            _order.append(attr)
            _values[attr] = value
            return value

phone = translator(delete=' -().etET')

def fix_phone(text):
    text = str(text) # convert numbers to digits
    text = text.strip()
    data = phone(text)
    if not data:
        return text
    # fix double leading zeros
    if data[:2] == '00':
        data = '011' + data[2:]
    # fix leading '+' signs
    if data[0] == '+':
        data = '011' + data[1:].replace('+', '')
    data = data.replace('#', 'x').replace('X','x')
    if 'x' in data:
        data, ext = data.split('x', 1)
    else:
        ext = ''
    if ext:
        ext = ' x%s' % ext
    if data.startswith('011'):
        if int(data[3:4]) in (
                20, 27, 30, 31, 32, 33, 34, 36, 39, 40, 41, 43, 44, 45, 46, 47, 49, 49,
                51, 52, 53, 54, 55, 56, 57, 58, 60, 61, 62, 63, 64, 65, 66,  7, 81, 82,
                84, 86, 90, 91, 92, 93, 94, 95, 98,
                ):
            pre = [data[:3], data[3:5]]
            data = data[5:]
        else:
            pre = [data[:3], data[3:6]]
            data = data[6:]
        post = [data[-4:]]
        data = data[:-4]
        if len(data) % 4 == 0:
            while data:
                post.append(data[-4:])
                data = data[:-4]
        else:
            while data:
                post.append(data[-3:])
                data = data[:-3]
        post.reverse()
        return '.'.join(pre + post) + ext
    if len(data) not in (7, 10, 11):
        return text
    if len(data) == 11:
        if data[0] != '1':
            return text
        data = data[1:]
    if len(data) == 7:
        return '%s.%s' % (data[:3], data[3:]) + ext
    return '%s.%s.%s' % (data[:3], data[3:6], data[6:]) + ext


def fix_date(text, format='mdy'):
    '''takes mmddyy (with yy in hex (A0 = 2000)) and returns a Date'''
    text = text.strip()
    if len(text) != 6:
        return None
    if format == 'mdy':
        yyyy, mm, dd = text[4:], text[:2], text[2:4]
    elif format == 'ymd':
        yyyy, mm, dd = text[:2], text[2:4], text[4:]
    try:
        yyyy = int(yyyy) + 1900
    except ValueError:
        yyyy = int(yyyy, 16) - 160 + 2000
    mm = int(mm)
    dd = int(dd)
    return Date(yyyy, mm, dd)

def date(year, month=None, day=None):
    if not year:
        return dbf.Date(None)
    elif isinstance(year, basestring):
        return text_to_date(year)
    else:
        return dbf.Date(year, month, day)

def get_local_ip(target):
    "get local ip address needed to talk to target"
    # based on http://www.linux-support.com/cms/get-local-ip-address-with-python/
    try:
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect((target, 8000))
        ipaddr = s.getsockname()[0]
        s.close()
    except Exception:
        ipaddr = None
    return ipaddr 


def generate_password(length, upper=True, lower=True, digit=True, special='!@#$%^'):
    """
    generate a random password that is length characters, and contains at least one of
    the True items, plus special if only two Trues present
    """
    uppers = 'ABCDEFHJKLMNPQRTUVWXY'
    lowers = 'abcdefghijkmnopqrstuvwxyz'
    digits = '0123456789'
    if not isinstance(length, (int, long)):
        if length[0] < 4:
            raise ValueError('Minimum length is four')
        length = random.randint(*length)
    if length < 4:
        raise ValueError('Minimum length is four')
    result = []
    source = ''
    if upper:
        result.append(random.choice(uppers))
        source += uppers
    if lower:
        result.append(random.choice(lowers))
        source += lowers
    if digit:
        result.append(random.choice(digits))
        source += digits
    if upper + lower + digit < 3 and special:
        result.append(random.choice(special))
    source += special or ''
    result.extend(random.sample(source, length - len(result)))
    random.shuffle(result)
    return ''.join(result)

def generate_passphrase(words=[]):
    """
    xkcd password generator

    http://xkcd.com/936/
    """
    if not words:
        with open('/usr/share/dict/words') as fh:
            for line in fh:
                word = line.strip()
                if word.isalpha() and word.islower() and 5 <= len(word) <= 7:
                    words.append(word)
    pass_phrase = []
    while len(pass_phrase) < 4:
        word = random.choice(words)
        if word in pass_phrase:
            continue
        pass_phrase.append(word)
    return ' '.join(pass_phrase)

def grouped(it, size):
    'yield chunks of it in groups of size'
    if size < 1:
        raise ValueError('size must be greater than 0 (not %r)' % size)
    result = []
    count = 0
    for ele in it:
        result.append(ele)
        count += 1
        if count == size:
            yield tuple(result)
            count = 0
            result = []
    if result:
        yield tuple(result)


def text_to_date(text, format='ymd'):
    '''(yy)yymmdd'''
    if not text.strip():
        return None
    try:
        dd = mm = yyyy = None
        if '-' in text:
            pieces = [p.zfill(2) for p in text.strip().split('-')]
            if len(pieces) != 3 or not all_equal(pieces, lambda p: p and len(p) in (2, 4)):
                raise ValueError
            text = ''.join(pieces)
        elif '/' in text:
            pieces = [p.zfill(2) for p in text.strip().split('/')]
            if len(pieces) != 3 or not all_equal(pieces, lambda p: p and len(p) in (2, 4)):
                raise ValueError
            text = ''.join(pieces)
        if len(text) == 6:
            if format == 'ymd':
                yyyy, mm, dd = int(text[:2])+2000, int(text[2:4]), int(text[4:])
            elif format == 'mdy':
                mm, dd, yyyy = int(text[:2]), int(text[2:4]), int(text[4:])+2000
        elif len(text) == 8:
            if format == 'ymd':
                yyyy, mm, dd = int(text[:4]), int(text[4:6]), int(text[6:])
            elif format == 'mdy':
                mm, dd, yyyy = int(text[:2]), int(text[2:4]), int(text[4:])
    except Exception, exc:
        if exc.args:
            arg0 = exc.args[0] + '\n'
        else:
            arg0 = ''
            exc.args = (arg0 + 'date %r must have two digits for day and month, and two or four digits for year' % text, ) + exc.args[1:]
        raise
    if dd is None:
        raise ValueError("don't know how to convert %r using %r" % (text, format))
    return Date(yyyy, mm, dd)


def text_to_time(text):
    """
    convert text to time
    
    hhmmss... -> hh and mm are required, ss is optional, ... is ignored
    """
    if not text.strip():
        return None
    return Time(int(text[:2]), int(text[2:4]), int(text[4:6] or 0))


@simplegeneric
def float(*args, **kwds):
    return __builtin__.float(*args, **kwds)


@float.register(timedelta)
def timedelta_as_float(td):
    seconds = td.seconds
    hours = seconds // 3600
    seconds = (seconds - hours * 3600) * (1.0 / 3600)
    return td.days * 24 + hours + seconds


@float.register(Time)
def Time_as_float(t):
    return t.tofloat()


class copy_argspec(object):
    """
    copy_argspec is a signature modifying decorator.  Specifically, it copies
    the signature from `source_func` to the wrapper, and the wrapper will call
    the original function (which should be using *args, **kwds).
    """
    def __init__(self, src_func):
        self.argspec = inspect.getargspec(src_func)
        self.src_doc = src_func.__doc__
        self.src_defaults = src_func.func_defaults

    def __call__(self, tgt_func):
        tgt_argspec = inspect.getargspec(tgt_func)
        need_self = False
        if tgt_argspec[0][0] == 'self':
            need_self = True
            
        name = tgt_func.__name__
        argspec = self.argspec
        if argspec[0][0] == 'self':
            need_self = False
        if need_self:
            newargspec = (['self'] + argspec[0],) + argspec[1:]
        else:
            newargspec = argspec
        signature = inspect.formatargspec(formatvalue=lambda val: "", *newargspec)[1:-1]
        new_func = (
                'def _wrapper_(%(signature)s):\n' 
                '    return %(tgt_func)s(%(signature)s)' % 
                {'signature':signature, 'tgt_func':'tgt_func'}
                   )
        evaldict = {'tgt_func' : tgt_func}
        exec new_func in evaldict
        wrapped = evaldict['_wrapper_']
        wrapped.__name__ = name
        wrapped.__doc__ = self.src_doc
        wrapped.func_defaults = self.src_defaults
        return wrapped


class LazyAttr(object):
    "doesn't create object until actually accessed"
    def __init__(yo, func=None, doc=None):
        yo.fget = func
        yo.__doc__ = doc or func.__doc__
    def __call__(yo, func):
        yo.fget = func
    def __get__(yo, instance, owner):
        if instance is None:
            return yo
        result =  yo.fget(instance)
        setattr(instance, yo.fget.__name__, result)
        return result

class Open(object):
    builtin_open = open
    _cache = {}
    @classmethod
    def __call__(cls, name, *args):
        file = cls.builtin_open(name, *args)
        cls._cache[name] = file
        return file
    @classmethod
    def active(cls, name):
        cls.open_files()
        try:
            return cls._cache[name]
        except KeyError:
            raise ValueError('%s has been closed' % name)
    @classmethod
    def open_files(cls):
        closed = []
        for name, file in cls._cache.items():
            if file.closed:
                closed.append(name)
        for name in closed:
            cls._cache.pop(name)
        return cls._cache.items()


class Missing(object):
    "if object hasn't been created, raise AttributeError"
    def __init__(yo, func=None, doc=None):
        yo.fget = func
        yo.__doc__ = doc or func.__doc__
    def __call__(yo, func):
        yo.fget = func
    def __get__(yo, instance, owner):
        if instance is None:
            return yo.fget(instance)
        raise AttributeError("%s must be added to this %s instance for full functionality" % (yo.fget.__name__, owner.__name__))


class ProgressBar(object):
    def __init__(yo, finalcount, block_char='.', message=None):
        yo.current_count = 0
        yo.finalcount = finalcount
        yo.blockcount = 0
        yo.block = block_char
        yo.f = sys.stdout
        if not yo.finalcount:
            return
        if message is not None:
            yo.f.write('\n\n%s\n' % message)
        yo.f.write('\n-------------------- % Progress ---------------- 1\n')
        yo.f.write('    1    2    3    4    5    6    7    8    9    0\n')
        yo.f.write('    0    0    0    0    0    0    0    0    0    0\n')
    def progress(yo, count):
        yo.current_count = count
        count = min(count, yo.finalcount)
        if yo.finalcount == count or not yo.finalcount:
            percentcomplete = 100
        else:
            percentcomplete = int(floor(100.0*count/yo.finalcount))
        blockcount = int(percentcomplete//2)
        if blockcount <= yo.blockcount:
            return
        for i in range(yo.blockcount, blockcount):
            yo.f.write(yo.block)
        yo.f.flush()
        yo.blockcount = blockcount
        if percentcomplete == 100:
            yo.f.write('\n')
    def tick(yo):
        yo.current_count += 1
        yo.progress(yo.current_count)

_var_sentinel = Sentinel('no value')
def var(value=_var_sentinel, _storage=threading.local()):
    if value is not _var_sentinel:
        _storage.value = value
    else:
        value = _storage.value
    return value

class Pocket(object):
    '''container to save values from intermediate expressions'''
    pocket = threading.local()
    pocket.stack = list()

    @classmethod
    def pop(cls):
        return cls.pocket.stack.pop()

    @classmethod
    def push(cls, *args):
        cls.pocket.stack.append(args)
        return args



def xml_quote(string):
    if any(ch in string for ch in (' ','<','>',"'")):
        string = string.replace(' ','%20').replace('<','%3C').replace('>','%3E').replace("'",'&apos;')
    return string

def xml_unquote(string):
    if any(qch in string for qch in ('%20', '%3C', '%3E', '&apos;')):
        string = string.replace('%20',' ').replace('%3C','<').replace('%3E','>').replace('&apos;',"'")
    return string
