from generators import *
from iterators import *
from utils import *
import dbf
import enum

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

class AutoEnum(enum.Enum):
    __last_number__ = 0
    def __new__(cls, *args):
        value = cls.__last_number__ + 1
        cls.__last_number__ = value
        obj = object.__new__(cls)
        obj._value = value
        return obj
    def __init__(self, *args):
        if args:
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

IntEnum = enum.IntEnum
#class IntEnum(enum.IntEnum):
#    def __new__(cls, value, *args):
#        return super(IntEnum, cls).__new__(cls, value)
#    def __init__(self, value, *args):
#        if args:
#            raise TypeError('%s not dealt with -- need custom __init__' % (args,))

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
