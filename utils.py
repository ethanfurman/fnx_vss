from __future__ import absolute_import

import __builtin__
import binascii
import datetime
import re
import smtplib
import string
import sys
import syslog
from datetime import date, timedelta
from decimal import Decimal
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.Encoders import encode_base64
from email import email
from enum import Enum, IntEnum
from math import floor
from scription import mail
from VSS import dbf
from VSS.dbf import DateTime, Date, Time, Integer, String
from VSS.time_machine import Sentinel, simplegeneric

one_day = timedelta(1)

spelled_out_numbers = set(['ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN','EIGHT','NINE','TEN'])


def Table(*args, **kwargs):
    'default to Clipper, Char, Logical, etc'
    data_types = {
            'C' : dbf.Char,
            'L' : dbf.Logical,
            'D' : dbf.Date,
            }
    if 'default_data_types' in kwargs:
        data_types.update(kwargs['default_data_types'])
    kwargs['default_data_types'] = data_types
    kwargs['dbf_type'] = 'clp'
    if (len(args) > 1 or kwargs.get('field_specs') is not None) \
    and ('codepage' not in kwargs):
        kwargs['codepage'] = 'utf8'
    return dbf.Table(*args, **kwargs)


def days_per_month(year):
    return (dbf.days_per_month, dbf.days_per_leap_month)[dbf.is_leapyear(year)]


class AutoEnum(Enum):
    """
    Automatically numbers enum members starting from 1.
    Includes support for a custom docstring per member.
    """

    __last_number__ = 0

    def __new__(cls, *args):
        """Ignores arguments (will be handled in __init__."""
        value = cls.__last_number__ + 1
        cls.__last_number__ = value
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, *args):
        """Can handle 0 or 1 argument; more requires a custom __init__.
        0  = auto-number w/o docstring
        1  = auto-number w/ docstring
        2+ = needs custom __init__
        """
        if len(args) == 1 and isinstance(args[0], (str, unicode)):
            self.__doc__ = args[0]
        elif args:
            raise TypeError('%s not dealt with -- need custom __init__' % (args,))

    def __index__(self):
        return self.value

    def __int__(self):
        return self.value

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    @classmethod
    def export(cls, namespace):
        for name, member in cls.__members__.items():
            if name == member.name:
                namespace[name] = member


class IndexEnum(Enum):

    def __index__(self):
        return self.value

    def __int__(self):
        return self.value

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class Weekday(AutoEnum):
    __order__ = 'MONDAY TUESDAY WEDNESDAY THURSDAY FRIDAY SATURDAY SUNDAY'
    MONDAY = ()
    TUESDAY = ()
    WEDNESDAY = ()
    THURSDAY = ()
    FRIDAY = ()
    SATURDAY = ()
    SUNDAY = ()


class Month(AutoEnum):
    __order__ = 'JANUARY FEBRUARY MARCH APRIL MAY JUNE JULY AUGUST SEPTEMBER OCTOBER NOVEMBER DECEMBER'
    JANUARY = ()
    FEBRUARY = ()
    MARCH = ()
    APRIL = ()
    MAY = ()
    JUNE = ()
    JULY = ()
    AUGUST = ()
    SEPTEMBER = ()
    OCTOBER = ()
    NOVEMBER = ()
    DECEMBER = ()


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
phone = translator(delete=' -().')

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
        if len(args) == 1 and not isinstance(args[0], String):
            args = args[0]
        result = tuple(func(*args))
        if len(result) == 1:
            result = result[0]
        return result
    #wrapper.__name__ = func.__name___
    wrapper.__doc__ = func.__doc__
    return wrapper


@tuples
def NameCase(*names):
    '''names should already be stripped of whitespace'''
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
            elif piece in ('and', 'de', 'del', 'der', 'el', 'la', 'van', 'of'):
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
    if not any(fields):
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
    if not any(fields):
        return fields
    final = []
    for name in fields:
        pieces = name.split()
        #if len(pieces) <= 1:
        #    final.append(name)
        #    continue
        mixed = []
        last_piece = ''
        for piece in pieces:
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




class xrange(object):
    '''
    accepts arbitrary objects to use to produce sequences
    '''

    types = {
            int :    {
                     'start' : 0,
                     'step'  : 1,
                     },
            float :  {
                     'start' : 0.0,
                     'step'  : 1.0,
                     },
            date :   {
                     'start' : None,
                     'step'  : one_day,
                     },
            Decimal: {'start' : 0,
                      'step'  : 1.0,
                     }
            }
    
    def __init__(yo, start, stop=None, step=None, count=None):
        if stop is not None and count is not None:
            raise TypeError("cannot specify both stop and count")
        if stop is None and count is None:    # check for default start based on type
            start, stop = None, start
            for t in yo.types:
                if isinstance(stop, t):
                    start = yo.types[t]['start']
                    break
            else:
                raise TypeError("start must be specified for unknown type %r" % stop.__class__)
            if start is None:
                raise TypeError("start must be specified for type %r" % stop.__class__)
        if step is None:
            step = yo.types[type(start or stop)]['step']

        yo.start = yo.init_start = start
        yo.count = yo.init_count = count
        yo.stop = stop
        yo.step = step
        yo.reverse = stop is not None and stop < start

    def __iter__(yo):
        return yo

    def __next__(yo):
        if not yo.reverse:
            if (yo.count is not None and yo.count < 1
            or  yo.stop is not None and yo.start >= yo.stop):   # all done!
                raise StopIteration
        else:
            if (yo.count is not None and yo.count < 1
            or  yo.start <= yo.stop):   # all done!
                raise StopIteration
        current = yo.start
        if callable(yo.step):   # custom function?
            yo.start = yo.step(yo.start)
        else:
            yo.start = yo.start + yo.step
        if yo.count is not None:
            yo.count -= 1
        return current
    next = __next__

    def __repr__(yo):
        values = [ '%s=%s' % (k,v) for k,v in (('start',yo.start), ('stop',yo.stop), ('step', yo.step), ('count', yo.count)) if v is not None ]
        return '<%s(%s)>' % (yo.__class__.__name__, ', '.join(values))

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


def fix_phone(text):
    text = str(text) # convert numbers to digits
    text = text.strip()
    data = phone(text)
    if len(data) not in (7, 10, 11):
        return text
    if len(data) == 11:
        if data[0] != '1':
            return text
        data = data[1:]
    if len(data) == 7:
        return '%s.%s' % (data[:3], data[3:])
    return '%s.%s.%s' % (data[:3], data[3:6], data[6:])


def fix_date(text, format='mdy'):
    '''takes mmddyy (with yy in hex (A0 = 2000)) and returns a Date'''
    text = text.strip()
    if len(text) != 6:
        return None
    if format == 'mdy':
        yyyy, mm, dd = int(text[4:], 16)-160+2000, int(text[:2]), int(text[2:4])
    elif format == 'ymd':
        yyyy, mm, dd = int(text[:2], 16)-160+2000, int(text[2:4]), int(text[4:])
    return Date(yyyy, mm, dd)


def text_to_date(text, format='ymd'):
    '''(yy)yymmdd'''
    if not text.strip():
        return None
    try:
        dd = mm = yyyy = None
        if '-' in text:
            pieces = [p.zfill(2) for p in text.split('-')]
            if len(pieces) != 3 or not all_equal(pieces, lambda p: p and len(p) in (2, 4)):
                raise ValueError
            text = ''.join(pieces)
        elif '/' in text:
            pieces = [p.zfill(2) for p in text.split('/')]
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
    if not text.strip():
        return None
    return Time(int(text[:2]), int(text[2:]))


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
        return yo.fget(instance)


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
