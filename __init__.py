from generators import *
from iterators import *
from utils import *
import dbf

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
