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

class AutoEnum(enum.Enum):
    __last_number__ = -1
    def __new__(cls, value=None):
        if value is None:
            value = cls.__last_number__ + 1
        cls.__last_number__ = value
        obj = object.__new__(cls)
        obj._value = value
        return obj
    def __init__(self, *args):
        cls = self.__class__
        if any(self.value == e.value for e in cls):
            a = self.name
            e = cls(self.value).name
            raise ValueError(
                    "aliases not allowed:  %r --> %r"
                    % (a, e))
    def __index__(self):
        return self._value
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self._value >= other._value
        return NotImplemented
    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self._value > other._value
        return NotImplemented
    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self._value <= other._value
        return NotImplemented
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self._value < other._value
        return NotImplemented
    @classmethod
    def export(cls, namespace):
        for name, member in cls.__members__.items():
            if name == member.name:
                namespace[name] = member

