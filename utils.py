from __future__ import absolute_import

import binascii
import datetime
import re
import smtplib
import string
import syslog
from datetime import date, timedelta
from decimal import Decimal
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.Encoders import encode_base64
from VSS import dbf
from VSS.dbf import Date, Time
from enum import Enum, IntEnum

String = str, unicode
Integer = int, long

one_day = timedelta(1)

spelled_out_numbers = set(['ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN','EIGHT','NINE','TEN'])

try:
    next
except NameError:
    from dbf import next

try:
    from collections import OrderedDict
except:
    # Backport of OrderedDict() class that runs on Python 2.4, 2.5, 2.6, 2.7 and pypy.
    # Passes Python2.7's test suite and incorporates all the latest updates.
    # Many thanks to Raymond Hettinger
    try:
        from thread import get_ident as _get_ident
    except ImportError:
        from dummy_thread import get_ident as _get_ident

    try:
        from _abcoll import KeysView, ValuesView, ItemsView
    except ImportError:
        pass


    class OrderedDict(dict):
        'Dictionary that remembers insertion order'
        # An inherited dict maps keys to values.
        # The inherited dict provides __getitem__, __len__, __contains__, and get.
        # The remaining methods are order-aware.
        # Big-O running times for all methods are the same as for regular dictionaries.

        # The internal self.__map dictionary maps keys to links in a doubly linked list.
        # The circular doubly linked list starts and ends with a sentinel element.
        # The sentinel element never gets deleted (this simplifies the algorithm).
        # Each link is stored as a list of length three:  [PREV, NEXT, KEY].

        def __init__(self, *args, **kwds):
            '''Initialize an ordered dictionary.  Signature is the same as for
            regular dictionaries, but keyword arguments are not recommended
            because their insertion order is arbitrary.

            '''
            if len(args) > 1:
                raise TypeError('expected at most 1 arguments, got %d' % len(args))
            try:
                self.__root
            except AttributeError:
                self.__root = root = []                     # sentinel node
                root[:] = [root, root, None]
                self.__map = {}
            self.__update(*args, **kwds)

        def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
            'od.__setitem__(i, y) <==> od[i]=y'
            # Setting a new item creates a new link which goes at the end of the linked
            # list, and the inherited dictionary is updated with the new key/value pair.
            if key not in self:
                root = self.__root
                last = root[0]
                last[1] = root[0] = self.__map[key] = [last, root, key]
            dict_setitem(self, key, value)

        def __delitem__(self, key, dict_delitem=dict.__delitem__):
            'od.__delitem__(y) <==> del od[y]'
            # Deleting an existing item uses self.__map to find the link which is
            # then removed by updating the links in the predecessor and successor nodes.
            dict_delitem(self, key)
            link_prev, link_next, key = self.__map.pop(key)
            link_prev[1] = link_next
            link_next[0] = link_prev

        def __iter__(self):
            'od.__iter__() <==> iter(od)'
            root = self.__root
            curr = root[1]
            while curr is not root:
                yield curr[2]
                curr = curr[1]

        def __reversed__(self):
            'od.__reversed__() <==> reversed(od)'
            root = self.__root
            curr = root[0]
            while curr is not root:
                yield curr[2]
                curr = curr[0]

        def clear(self):
            'od.clear() -> None.  Remove all items from od.'
            try:
                for node in self.__map.itervalues():
                    del node[:]
                root = self.__root
                root[:] = [root, root, None]
                self.__map.clear()
            except AttributeError:
                pass
            dict.clear(self)

        def popitem(self, last=True):
            '''od.popitem() -> (k, v), return and remove a (key, value) pair.
            Pairs are returned in LIFO order if last is true or FIFO order if false.

            '''
            if not self:
                raise KeyError('dictionary is empty')
            root = self.__root
            if last:
                link = root[0]
                link_prev = link[0]
                link_prev[1] = root
                root[0] = link_prev
            else:
                link = root[1]
                link_next = link[1]
                root[1] = link_next
                link_next[0] = root
            key = link[2]
            del self.__map[key]
            value = dict.pop(self, key)
            return key, value

        # -- the following methods do not depend on the internal structure --

        def keys(self):
            'od.keys() -> list of keys in od'
            return list(self)

        def values(self):
            'od.values() -> list of values in od'
            return [self[key] for key in self]

        def items(self):
            'od.items() -> list of (key, value) pairs in od'
            return [(key, self[key]) for key in self]

        def iterkeys(self):
            'od.iterkeys() -> an iterator over the keys in od'
            return iter(self)

        def itervalues(self):
            'od.itervalues -> an iterator over the values in od'
            for k in self:
                yield self[k]

        def iteritems(self):
            'od.iteritems -> an iterator over the (key, value) items in od'
            for k in self:
                yield (k, self[k])

        def update(*args, **kwds):
            '''od.update(E, **F) -> None.  Update od from dict/iterable E and F.

            If E is a dict instance, does:           for k in E: od[k] = E[k]
            If E has a .keys() method, does:         for k in E.keys(): od[k] = E[k]
            Or if E is an iterable of items, does:   for k, v in E: od[k] = v
            In either case, this is followed by:     for k, v in F.items(): od[k] = v

            '''
            if len(args) > 2:
                raise TypeError('update() takes at most 2 positional '
                                'arguments (%d given)' % (len(args),))
            elif not args:
                raise TypeError('update() takes at least 1 argument (0 given)')
            self = args[0]
            # Make progressively weaker assumptions about "other"
            other = ()
            if len(args) == 2:
                other = args[1]
            if isinstance(other, dict):
                for key in other:
                    self[key] = other[key]
            elif hasattr(other, 'keys'):
                for key in other.keys():
                    self[key] = other[key]
            else:
                for key, value in other:
                    self[key] = value
            for key, value in kwds.items():
                self[key] = value

        __update = update  # let subclasses override update without breaking __init__

        __marker = object()

        def pop(self, key, default=__marker):
            '''od.pop(k[,d]) -> v, remove specified key and return the corresponding value.
            If key is not found, d is returned if given, otherwise KeyError is raised.

            '''
            if key in self:
                result = self[key]
                del self[key]
                return result
            if default is self.__marker:
                raise KeyError(key)
            return default

        def setdefault(self, key, default=None):
            'od.setdefault(k[,d]) -> od.get(k,d), also set od[k]=d if k not in od'
            if key in self:
                return self[key]
            self[key] = default
            return default

        def __repr__(self, _repr_running={}):
            'od.__repr__() <==> repr(od)'
            call_key = id(self), _get_ident()
            if call_key in _repr_running:
                return '...'
            _repr_running[call_key] = 1
            try:
                if not self:
                    return '%s()' % (self.__class__.__name__,)
                return '%s(%r)' % (self.__class__.__name__, self.items())
            finally:
                del _repr_running[call_key]

        def __reduce__(self):
            'Return state information for pickling'
            items = [[k, self[k]] for k in self]
            inst_dict = vars(self).copy()
            for k in vars(OrderedDict()):
                inst_dict.pop(k, None)
            if inst_dict:
                return (self.__class__, (items,), inst_dict)
            return self.__class__, (items,)

        def copy(self):
            'od.copy() -> a shallow copy of od'
            return self.__class__(self)

        @classmethod
        def fromkeys(cls, iterable, value=None):
            '''OD.fromkeys(S[, v]) -> New ordered dictionary with keys from S
            and values equal to v (which defaults to None).

            '''
            d = cls()
            for key in iterable:
                d[key] = value
            return d

        def __eq__(self, other):
            '''od.__eq__(y) <==> od==y.  Comparison to another OD is order-sensitive
            while comparison to a regular mapping is order-insensitive.

            '''
            if isinstance(other, OrderedDict):
                return len(self)==len(other) and self.items() == other.items()
            return dict.__eq__(self, other)

        def __ne__(self, other):
            return not self == other

        # -- the following methods are only used in Python 2.7 --

        def viewkeys(self):
            "od.viewkeys() -> a set-like object providing a view on od's keys"
            return KeysView(self)

        def viewvalues(self):
            "od.viewvalues() -> an object providing a view on od's values"
            return ValuesView(self)

        def viewitems(self):
            "od.viewitems() -> a set-like object providing a view on od's items"
            return ItemsView(self)

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
    __last_number__ = 0
    def __new__(cls, *args):
        value = cls.__last_number__ + 1
        cls.__last_number__ = value
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
    def __init__(self, *args):
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
    try:
        if test is None:
            target = next(it)
        else:
            target = test(next(it))
    except StopIteration:
        return True
    if test is None:
        test = lambda x: x == target
    for item in it:
        if test(item) != target:
            return False
    return True

def bb_text_to_date(text):
    mm, dd, yy = map(int, (text[:2], text[2:4], text[4:]))
    if any([i == 0 for i in (mm, dd, yy)]):
        Date()
    yyyy = yy + 2000
    return Date(yyyy, mm, dd)

building_subs = set([
    '#','APARTMENT','APT','BLDG','BUILDING','CONDO','FL','FLR','FLOOR','LOT','LOWER','NO','NUM','NUMBER',
    'RM','ROOM','SLIP','SLP','SPACE','SP','SPC','STE','SUITE','TRLR','UNIT','UPPER',
    ])
caps_okay = set(['UCLA', 'OHSU', 'IBM', 'LLC', 'USA', 'NASA'])
lower_okay = set(['dba', 'c/o', 'attn'])

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

us_ca_state_abbr = {
    'AB' : 'ALBERTA' ,
    'AK' : 'ALASKA' ,
    'AL' : 'ALABAMA' ,
    'AR' : 'ARKANSAS' ,
    'AS' : 'AMERICAN SAMOA' ,
    'AZ' : 'ARIZONA' ,
    'BC' : 'BRITISH COLUMBIA' ,
    'CA' : 'CALIFORNIA' ,
    'CO' : 'COLORADO' ,
    'CT' : 'CONNECTICUT' ,
    'DC' : 'DISTRICT OF COLUMBIA' ,
    'DE' : 'DELAWARE' ,
    'FL' : 'FLORIDA' ,
    'FM' : 'FEDERATED STATES OF MICRONESIA' ,
    'GA' : 'GEORGIA' ,
    'GU' : 'GUAM' ,
    'HI' : 'HAWAII' ,
    'IA' : 'IOWA' ,
    'ID' : 'IDAHO' ,
    'IL' : 'ILLINOIS' ,
    'IN' : 'INDIANA' ,
    'KS' : 'KANSAS' ,
    'KY' : 'KENTUCKY' ,
    'LA' : 'LOUISIANA' ,
    'MA' : 'MASSACHUSETTS' ,
    'MB' : 'MANITOBA' ,
    'MD' : 'MARYLAND' ,
    'ME' : 'MAINE' ,
    'MH' : 'MARSHALL ISLANDS' ,
    'MI' : 'MICHIGAN' ,
    'MN' : 'MINNESOTA' ,
    'MO' : 'MISSOURI' ,
    'MP' : 'NORTHERN MARIANA ISLANDS' ,
    'MS' : 'MISSISSIPPI' ,
    'MT' : 'MONTANA' ,
    'NB' : 'NEW BRUNSWICK' ,
    'NC' : 'NORTH CAROLINA' ,
    'ND' : 'NORTH DAKOTA' ,
    'NE' : 'NEBRASKA' ,
    'NH' : 'NEW HAMPSHIRE' ,
    'NJ' : 'NEW JERSEY' ,
    'NL' : 'NEWFOUNDLAND' ,
    'NM' : 'NEW MEXICO' ,
    'NS' : 'NOVA SCOTIA' ,
    'NT' : 'NORTHWEST TERRITORY' ,
    'NU' : 'NUNAVUT' ,
    'NV' : 'NEVADA' ,
    'NY' : 'NEW YORK' ,
    'OH' : 'OHIO' ,
    'OK' : 'OKLAHOMA' ,
    'ON' : 'ONTARIO' ,
    'OR' : 'OREGON' ,
    'PA' : 'PENNSYLVANIA' ,
    'PE' : 'PRINCE EDWARD ISLAND' ,
    'PR' : 'PUERTO RICO' ,
    'PW' : 'PALAU' ,
    'QC' : 'QUEBEC' ,
    'RI' : 'RHODE ISLAND' ,
    'SC' : 'SOUTH CAROLINA' ,
    'SD' : 'SOUTH DAKOTA' ,
    'SK' : 'SASKATCHEWAN' ,
    'TN' : 'TENNESSEE' ,
    'TX' : 'TEXAS' ,
    'UT' : 'UTAH' ,
    'VA' : 'VIRGINIA' ,
    'VI' : 'VIRGIN ISLANDS' ,
    'VT' : 'VERMONT' ,
    'WA' : 'WASHINGTON' ,
    'WI' : 'WISCONSIN' ,
    'WV' : 'WEST VIRGINIA' ,
    'WY' : 'WYOMING' ,
    'YT' : 'YUKON' ,
    }
us_ca_state_name = dict([(v, k) for k, v in us_ca_state_abbr.items()])

ca_province_abbr = {
    'AB' : 'ALBERTA' ,
    'BC' : 'BRITISH COLUMBIA' ,
    'MB' : 'MANITOBA' ,
    'NB' : 'NEW BRUNSWICK' ,
    'NL' : 'NEWFOUNDLAND' ,
    'NS' : 'NOVA SCOTIA' ,
    'NT' : 'NORTHWEST TERRITORY' ,
    'NU' : 'NUNAVUT' ,
    'ON' : 'ONTARIO' ,
    'PE' : 'PRINCE EDWARD ISLAND' ,
    'QC' : 'QUEBEC' ,
    'SK' : 'SASKATCHEWAN' ,
    'YT' : 'YUKON' ,
    }
ca_province_name = dict([(v, k) for k, v in ca_province_abbr.items()])

addr_abbr = {
        'rd.'       : 'road',
        'rd'        : 'road',
        'st.'       : 'street',
        'st'        : 'street',
        'ste'       : 'suite',
        'ste.'      : 'suite',
        'ave.'      : 'avenue',
        'blvd.'     : 'boulevard',
        'blvd'      : 'boulevard',
        'e.'        : 'e',
        'east'      : 'e',
        'w.'        : 'w',
        'west'      : 'w',
        'n.'        : 'n',
        'north'     : 'n',
        's.'        : 's',
        'south'     : 's',
        'ne.'       : 'ne',
        'northeast' : 'ne',
        'se.'       : 'se',
        'southeast' : 'se',
        'nw.'       : 'nw',
        'northwest' : 'nw',
        'sw.'       : 'sw',
        'southwest' : 'sw',
        'so.'       : 's',
        'highway'   : 'hwy',
        'hwy.'      : 'hwy',
        'building'  : 'bldg',
        'bldg.'     : 'bldg',
        'ln.'       : 'lane',
        'apt.'      : 'apt',
        'apartment' : 'apt',
        'p.o.'      : 'po',
        'p.o'       : 'po',
        'po.'       : 'po',
        'p.o.box'   : 'po box',
        'po.box'    : 'po box',
        'pobox'     : 'po box',
        'pob'       : 'po box',
        }

bsns_abbr = {
        'inc.'      : 'incorporated',
        'inc'       : 'incorporated',
        'co.'       : 'company',
        'co'        : 'company',
        'corp.'     : 'corporation',
        'corp'      : 'corporation',
        'dept.'     : 'department',
        'dept'      : 'department',
        'ltd.'      : 'limited',
        'ltd'       : 'limited',
        }

country_abbr = {
    "AF":  "AFGHANISTAN",
    "AX":  "ALAND ISLANDS",
    "AL":  "ALBANIA",
    "DZ":  "ALGERIA",
    "AS":  "AMERICAN SAMOA",
    "AD":  "ANDORRA",
    "AO":  "ANGOLA",
    "AI":  "ANGUILLA",
    "AQ":  "ANTARCTICA",
    "AG":  "ANTIGUA AND BARBUDA",
    "AR":  "ARGENTINA",
    "AM":  "ARMENIA",
    "AW":  "ARUBA",
    "AU":  "AUSTRALIA",
    "AT":  "AUSTRIA",
    "AZ":  "AZERBAIJAN",
    "BS":  "BAHAMAS",
    "BH":  "BAHRAIN",
    "BD":  "BANGLADESH",
    "BB":  "BARBADOS",
    "BY":  "BELARUS",
    "BE":  "BELGIUM",
    "BZ":  "BELIZE",
    "BJ":  "BENIN",
    "BM":  "BERMUDA",
    "BT":  "BHUTAN",
    "BO":  "BOLIVIA, PLURINATIONAL STATE OF",
    "BQ":  "BONAIRE, SINT EUSTATIUS AND SABA",
    "BA":  "BOSNIA AND HERZEGOVINA",
    "BW":  "BOTSWANA",
    "BV":  "BOUVET ISLAND",
    "BR":  "BRAZIL",
    "IO":  "BRITISH INDIAN OCEAN TERRITORY",
    "BN":  "BRUNEI DARUSSALAM",
    "BG":  "BULGARIA",
    "BF":  "BURKINA FASO",
    "BI":  "BURUNDI",
    "KH":  "CAMBODIA",
    "CM":  "CAMEROON",
    "CA":  "CANADA",
    "CV":  "CAPE VERDE",
    "KY":  "CAYMAN ISLANDS",
    "CF":  "CENTRAL AFRICAN REPUBLIC",
    "TD":  "CHAD",
    "CL":  "CHILE",
    "CN":  "CHINA",
    "CX":  "CHRISTMAS ISLAND",
    "CC":  "COCOS (KEELING) ISLANDS",
    "CO":  "COLOMBIA",
    "KM":  "COMOROS",
    "CG":  "CONGO",
    "CD":  "CONGO, THE DEMOCRATIC REPUBLIC OF THE",
    "CK":  "COOK ISLANDS",
    "CR":  "COSTA RICA",
    "CI":  "IVORY COAST",
    "HR":  "CROATIA",
    "CU":  "CUBA",
    "CW":  "CURACAO",
    "CY":  "CYPRUS",
    "CZ":  "CZECH REPUBLIC",
    "DK":  "DENMARK",
    "DJ":  "DJIBOUTI",
    "DM":  "DOMINICA",
    "DO":  "DOMINICAN REPUBLIC",
    "EC":  "ECUADOR",
    "EG":  "EGYPT",
    "SV":  "EL SALVADOR",
    "GQ":  "EQUATORIAL GUINEA",
    "ER":  "ERITREA",
    "EE":  "ESTONIA",
    "ET":  "ETHIOPIA",
    "FK":  "FALKLAND ISLANDS (MALVINAS)",
    "FO":  "FAROE ISLANDS",
    "FJ":  "FIJI",
    "FI":  "FINLAND",
    "FR":  "FRANCE",
    "GF":  "FRENCH GUIANA",
    "PF":  "FRENCH POLYNESIA",
    "TF":  "FRENCH SOUTHERN TERRITORIES",
    "GA":  "GABON",
    "GM":  "GAMBIA",
    "GE":  "GEORGIA",
    "DE":  "GERMANY",
    "GH":  "GHANA",
    "GI":  "GIBRALTAR",
    "GR":  "GREECE",
    "GL":  "GREENLAND",
    "GD":  "GRENADA",
    "GP":  "GUADELOUPE",
    "GU":  "GUAM",
    "GT":  "GUATEMALA",
    "GG":  "GUERNSEY",
    "GN":  "GUINEA",
    "GW":  "GUINEA-BISSAU",
    "GY":  "GUYANA",
    "HT":  "HAITI",
    "HM":  "HEARD ISLAND AND MCDONALD ISLANDS",
    "VA":  "HOLY SEE (VATICAN CITY STATE)",
    "HN":  "HONDURAS",
    "HK":  "HONG KONG",
    "HU":  "HUNGARY",
    "IS":  "ICELAND",
    "IN":  "INDIA",
    "ID":  "INDONESIA",
    "IR":  "IRAN, ISLAMIC REPUBLIC OF",
    "IQ":  "IRAQ",
    "IE":  "IRELAND",
    "IM":  "ISLE OF MAN",
    "IL":  "ISRAEL",
    "IT":  "ITALY",
    "JM":  "JAMAICA",
    "JP":  "JAPAN",
    "JE":  "JERSEY",
    "JO":  "JORDAN",
    "KZ":  "KAZAKHSTAN",
    "KE":  "KENYA",
    "KI":  "KIRIBATI",
    "KP":  "KOREA, DEMOCRATIC PEOPLE'S REPUBLIC OF",
    "KR":  "KOREA, REPUBLIC OF",
    "KW":  "KUWAIT",
    "KG":  "KYRGYZSTAN",
    "LA":  "LAO PEOPLE'S DEMOCRATIC REPUBLIC",
    "LV":  "LATVIA",
    "LB":  "LEBANON",
    "LS":  "LESOTHO",
    "LR":  "LIBERIA",
    "LY":  "LIBYA",
    "LI":  "LIECHTENSTEIN",
    "LT":  "LITHUANIA",
    "LU":  "LUXEMBOURG",
    "MO":  "MACAO",
    "MK":  "MACEDONIA, THE FORMER YUGOSLAV REPUBLIC OF",
    "MG":  "MADAGASCAR",
    "MW":  "MALAWI",
    "MY":  "MALAYSIA",
    "MV":  "MALDIVES",
    "ML":  "MALI",
    "MT":  "MALTA",
    "MH":  "MARSHALL ISLANDS",
    "MQ":  "MARTINIQUE",
    "MR":  "MAURITANIA",
    "MU":  "MAURITIUS",
    "YT":  "MAYOTTE",
    "MX":  "MEXICO",
    "FM":  "MICRONESIA, FEDERATED STATES OF",
    "MD":  "MOLDOVA, REPUBLIC OF",
    "MC":  "MONACO",
    "MN":  "MONGOLIA",
    "ME":  "MONTENEGRO",
    "MS":  "MONTSERRAT",
    "MA":  "MOROCCO",
    "MZ":  "MOZAMBIQUE",
    "MM":  "MYANMAR",
    "NA":  "NAMIBIA",
    "NR":  "NAURU",
    "NP":  "NEPAL",
    "NL":  "NETHERLANDS",
    "NC":  "NEW CALEDONIA",
    "NZ":  "NEW ZEALAND",
    "NI":  "NICARAGUA",
    "NE":  "NIGER",
    "NG":  "NIGERIA",
    "NU":  "NIUE",
    "NF":  "NORFOLK ISLAND",
    "MP":  "NORTHERN MARIANA ISLANDS",
    "NO":  "NORWAY",
    "OM":  "OMAN",
    "PK":  "PAKISTAN",
    "PW":  "PALAU",
    "PS":  "PALESTINE, STATE OF",
    "PA":  "PANAMA",
    "PG":  "PAPUA NEW GUINEA",
    "PY":  "PARAGUAY",
    "PE":  "PERU",
    "PH":  "PHILIPPINES",
    "PN":  "PITCAIRN",
    "PL":  "POLAND",
    "PT":  "PORTUGAL",
    "PR":  "PUERTO RICO",
    "QA":  "QATAR",
    "RE":  "REUNION",
    "RO":  "ROMANIA",
    "RU":  "RUSSIAN FEDERATION",
    "RW":  "RWANDA",
    "BL":  "SAINT BARTHELEMY",
    "SH":  "SAINT HELENA, ASCENSION AND TRISTAN DA CUNHA",
    "KN":  "SAINT KITTS AND NEVIS",
    "LC":  "SAINT LUCIA",
    "MF":  "SAINT MARTIN (FRENCH PART)",
    "PM":  "SAINT PIERRE AND MIQUELON",
    "VC":  "SAINT VINCENT AND THE GRENADINES",
    "WS":  "SAMOA",
    "SM":  "SAN MARINO",
    "ST":  "SAO TOME AND PRINCIPE",
    "SA":  "SAUDI ARABIA",
    "SN":  "SENEGAL",
    "RS":  "SERBIA",
    "SC":  "SEYCHELLES",
    "SL":  "SIERRA LEONE",
    "SG":  "SINGAPORE",
    "SX":  "SINT MAARTEN (DUTCH PART)",
    "SK":  "SLOVAKIA",
    "SI":  "SLOVENIA",
    "SB":  "SOLOMON ISLANDS",
    "SO":  "SOMALIA",
    "ZA":  "SOUTH AFRICA",
    "GS":  "SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS",
    "SS":  "SOUTH SUDAN",
    "ES":  "SPAIN",
    "LK":  "SRI LANKA",
    "SD":  "SUDAN",
    "SR":  "SURINAME",
    "SJ":  "SVALBARD AND JAN MAYEN",
    "SZ":  "SWAZILAND",
    "SE":  "SWEDEN",
    "CH":  "SWITZERLAND",
    "SY":  "SYRIAN ARAB REPUBLIC",
    "TW":  "TAIWAN, PROVINCE OF CHINA",
    "TJ":  "TAJIKISTAN",
    "TZ":  "TANZANIA, UNITED REPUBLIC OF",
    "TH":  "THAILAND",
    "TL":  "TIMOR-LESTE",
    "TG":  "TOGO",
    "TK":  "TOKELAU",
    "TO":  "TONGA",
    "TT":  "TRINIDAD AND TOBAGO",
    "TN":  "TUNISIA",
    "TR":  "TURKEY",
    "TM":  "TURKMENISTAN",
    "TC":  "TURKS AND CAICOS ISLANDS",
    "TV":  "TUVALU",
    "UG":  "UGANDA",
    "UA":  "UKRAINE",
    "AE":  "UNITED ARAB EMIRATES",
    "UK":  "UNITED KINGDOM",
    "GB":  "UNITED KINGDOM",
    "ENGLAND":  "UNITED KINGDOM",
    "US":  "UNITED STATES",
    "UM":  "UNITED STATES MINOR OUTLYING ISLANDS",
    "UY":  "URUGUAY",
    "UZ":  "UZBEKISTAN",
    "VU":  "VANUATU",
    "VE":  "VENEZUELA, BOLIVARIAN REPUBLIC OF",
    "VN":  "VIET NAM",
    "VG":  "VIRGIN ISLANDS, BRITISH",
    "VI":  "VIRGIN ISLANDS, U.S.",
    "WF":  "WALLIS AND FUTUNA",
    "EH":  "WESTERN SAHARA",
    "YE":  "YEMEN",
    "ZM":  "ZAMBIA",
    "ZW":  "ZIMBABWE",
    }
country_name = dict([(v, k) for k, v in country_abbr.items()])

def cszk(line1, line2):
    """
    parses two lines of text into blah, city, state, zip, country

    supported formats:
      line1: city (state)
      line2: zip zip country

      line1: ...
      line2: city state zip zip country

      line1: city state zip zip
      line2: country

      line1: ...
      line2: city, state zip zip

      returns street, city, state, zip, country; but state is only
      populated if country is US or CA
    """
    line1 = re.sub(r'\b[A-Z]\.[A-Z]\.[^A-Z]', lambda s: s.group().replace('.',''), line1)
    line2 = re.sub(r'\b[A-Z]\.[A-Z]\.[^A-Z]', lambda s: s.group().replace('.',''), line2)
    line1, line2 = Sift(line1.replace('.',' ').replace(',',' '), line2.replace('.',' ').replace(',',' '))
    line1 = ' '.join(line1.split())
    line2 = ' '.join(line2.split())
    street = city = state = postal = country = ''
    try:
        pieces, line2 = line2.split(), ''
        k = kountry = ''
        while pieces:
            new_k = pieces.pop().upper()
            if has_digits(new_k):
                city = k
                pieces.append(new_k)
                break
            k = (new_k + ' ' + k).strip()
            if k in country_abbr:
                k, kountry = country_abbr[k], k
            if k in country_name:
                country = k
                if pieces and pieces[-1].upper() == 'THE':
                    pieces.pop()
                break
            else:
                # check for a state
                if k in us_ca_state_abbr:
                    k = us_ca_state_abbr[k]
                if k in us_ca_state_name:
                    state = k
                    break
        else:
            pieces = k.split()
        if not pieces:
            pieces, line1 = line1.split(), ''
        if has_digits(pieces[-1]) or len(pieces[-1]) == 3:  # zip code!
            if len(pieces) > 1 and (has_digits(pieces[-2]) or len(pieces[-2]) == 3):
                postal = PostalCode(' '.join(pieces[-2:]), country=country)
                pieces.pop(); pieces.pop()
            else:
                postal = PostalCode(pieces.pop(), country=country)
        if not pieces:
            pieces, line1 = line1.split(), ''
        if not country and pieces[-1] == 'CANADA' and (len(pieces) == 1 or pieces[-2] != 'OF'):
            country = 'CANADA'
            pieces.pop()
        elif not country and pieces[-1] not in us_ca_state_abbr and (
                pieces[-1] in country_name or pieces[-1] in country_abbr):
            country = country_abbr.get(pieces[-1], pieces[-1])
            pieces.pop()
        if not pieces:
            pieces, line1 = line1.split(), ''
        if country not in ('CANADA', ''):
            city = (' '.join(pieces) + city).strip(' ,')
            pieces = []
        else:
            s = pieces.pop()  # now looking for a state
            while s not in us_ca_state_abbr and s not in us_ca_state_name:
                if s[-1] == ')':
                    if s[0] == '(':
                        s = s[1:-1]
                        continue
                elif pieces and pieces[-1][-1:] == ',':
                    break
                if pieces:
                    s = (pieces.pop() + ' ' + s).strip()
                    if len(s) == 3 and s[1] == ' ':
                        s = s[0] + s[2]
                else:
                    break
            if s in us_ca_state_abbr:
                s = us_ca_state_abbr[s]
            if s in us_ca_state_name:
                state = s
            else:
                city = (s + ' ' + city).strip(', ')
        # see if state is canadian
        if state in ca_province_name and not country:
            country = 'CANADA'
        # if state is empty but we have a country, check that country abbreviation is not a state
        if country and not state:
            if kountry in us_ca_state_abbr:
                state = us_ca_state_abbr[kountry]
                country = ''
        if pieces:
            city = (' '.join(pieces) + ' ' + city).strip(', ')
            pieces[:] = []
        if city : # early bail
            street, line1 = line1, ''
            return street, city, state, postal, country
        else:
            city, line1 = line1.strip(', '), ''
            return street, city, state, postal, country
    except IndexError:
        if line1 or line2 or pieces:
            raise
        return street, city, state, postal, country


usps_street_suffix_common = {
	'ALLEE'      :  'ALLEY',
	'ALLEY'      :  'ALLEY',
	'ALLY'       :  'ALLEY',
	'ALY'        :  'ALLEY',
	'ANEX'       :  'ANNEX',
	'ANNEX'      :  'ANNEX',
	'ANNEX'      :  'ANNEX',
	'ANX'        :  'ANNEX',
	'ARC'        :  'ARCADE',
	'ARCADE'     :  'ARCADE',
	'AV'         :  'AVENUE',
	'AVE'        :  'AVENUE',
	'AVEN'       :  'AVENUE',
	'AVENU'      :  'AVENUE',
	'AVENUE'     :  'AVENUE',
	'AVN'        :  'AVENUE',
	'AVNUE'      :  'AVENUE',
	'BAYOO'      :  'BAYOO',
	'BAYOU'      :  'BAYOO',
	'BCH'        :  'BEACH',
	'BEACH'      :  'BEACH',
	'BEND'       :  'BEND',
	'BND'        :  'BEND',
	'BLF'        :  'BLUFF',
	'BLUF'       :  'BLUFF',
	'BLUFF'      :  'BLUFF',
	'BLUFFS'     :  'BLUFFS',
	'BOT'        :  'BOTTOM',
	'BOTTM'      :  'BOTTOM',
	'BOTTOM'     :  'BOTTOM',
	'BTM'        :  'BOTTOM',
	'BLVD'       :  'BOULEVARD',
	'BOUL'       :  'BOULEVARD',
	'BOULEVARD'  :  'BOULEVARD',
	'BOULV'      :  'BOULEVARD',
	'BR'         :  'BRANCH',
	'BRANCH'     :  'BRANCH',
	'BRNCH'      :  'BRANCH',
	'BRDGE'      :  'BRIDGE',
	'BRG'        :  'BRIDGE',
	'BRIDGE'     :  'BRIDGE',
	'BRK'        :  'BROOK',
	'BROOK'      :  'BROOK',
	'BROOKS'     :  'BROOKS',
	'BURG'       :  'BURG',
	'BURGS'      :  'BURGS',
	'BYP'        :  'BYPASS',
	'BYPA'       :  'BYPASS',
	'BYPAS'      :  'BYPASS',
	'BYPASS'     :  'BYPASS',
	'BYPS'       :  'BYPASS',
	'CAMP'       :  'CAMP',
	'CMP'        :  'CAMP',
	'CP'         :  'CAMP',
	'CANYN'      :  'CANYON',
	'CANYON'     :  'CANYON',
	'CNYN'       :  'CANYON',
	'CYN'        :  'CANYON',
	'CAPE'       :  'CAPE',
	'CPE'        :  'CAPE',
	'CAUSEWAY'   :  'CAUSEWAY',
	'CAUSWAY'    :  'CAUSEWAY',
	'CSWY'       :  'CAUSEWAY',
	'CEN'        :  'CENTER',
	'CENT'       :  'CENTER',
	'CENTER'     :  'CENTER',
	'CENTR'      :  'CENTER',
	'CENTRE'     :  'CENTER',
	'CNTER'      :  'CENTER',
	'CNTR'       :  'CENTER',
	'CTR'        :  'CENTER',
	'CENTERS'    :  'CENTERS',
	'CIR'        :  'CIRCLE',
	'CIRC'       :  'CIRCLE',
	'CIRCL'      :  'CIRCLE',
	'CIRCLE'     :  'CIRCLE',
	'CRCL'       :  'CIRCLE',
	'CRCLE'      :  'CIRCLE',
	'CIRCLES'    :  'CIRCLES',
	'CLF'        :  'CLIFF',
	'CLIFF'      :  'CLIFF',
	'CLFS'       :  'CLIFFS',
	'CLIFFS'     :  'CLIFFS',
	'CLB'        :  'CLUB',
	'CLUB'       :  'CLUB',
	'COMMON'     :  'COMMON',
	'COR'        :  'CORNER',
	'CORNER'     :  'CORNER',
	'CORNERS'    :  'CORNERS',
	'CORS'       :  'CORNERS',
	'COURSE'     :  'COURSE',
	'CRSE'       :  'COURSE',
	'COURT'      :  'COURT',
	'CRT'        :  'COURT',
	'CT'         :  'COURT',
	'COURTS'     :  'COURTS',
	'CT'         :  'COURTS',
	'COVE'       :  'COVE',
	'CV'         :  'COVE',
	'COVES'      :  'COVES',
	'CK'         :  'CREEK',
	'CR'         :  'CREEK',
	'CREEK'      :  'CREEK',
	'CRK'        :  'CREEK',
	'CRECENT'    :  'CRESCENT',
	'CRES'       :  'CRESCENT',
	'CRESCENT'   :  'CRESCENT',
	'CRESENT'    :  'CRESCENT',
	'CRSCNT'     :  'CRESCENT',
	'CRSENT'     :  'CRESCENT',
	'CRSNT'      :  'CRESCENT',
	'CREST'      :  'CREST',
	'CROSSING'   :  'CROSSING',
	'CRSSING'    :  'CROSSING',
	'CRSSNG'     :  'CROSSING',
	'XING'       :  'CROSSING',
	'CROSSROAD'  :  'CROSSROAD',
	'CURVE'      :  'CURVE',
	'DALE'       :  'DALE',
	'DL'         :  'DALE',
	'DAM'        :  'DAM',
	'DM'         :  'DAM',
	'DIV'        :  'DIVIDE',
	'DIVIDE'     :  'DIVIDE',
	'DV'         :  'DIVIDE',
	'DVD'        :  'DIVIDE',
	'DR'         :  'DRIVE',
	'DRIV'       :  'DRIVE',
	'DRIVE'      :  'DRIVE',
	'DRV'        :  'DRIVE',
	'DRIVES'     :  'DRIVES',
	'EST'        :  'ESTATE',
	'ESTATE'     :  'ESTATE',
	'ESTATES'    :  'ESTATES',
	'ESTS'       :  'ESTATES',
	'EXP'        :  'EXPRESSWAY',
	'EXPR'       :  'EXPRESSWAY',
	'EXPRESS'    :  'EXPRESSWAY',
	'EXPRESSWAY' :  'EXPRESSWAY',
	'EXPW'       :  'EXPRESSWAY',
	'EXPY'       :  'EXPRESSWAY',
	'EXT'        :  'EXTENSION',
	'EXTENSION'  :  'EXTENSION',
	'EXTN'       :  'EXTENSION',
	'EXTNSN'     :  'EXTENSION',
	'EXTENSIONS' :  'EXTENSIONS',
	'EXTS'       :  'EXTENSIONS',
	'FALL'       :  'FALL',
	'FALLS'      :  'FALLS',
	'FLS'        :  'FALLS',
	'FERRY'      :  'FERRY',
	'FRRY'       :  'FERRY',
	'FRY'        :  'FERRY',
	'FIELD'      :  'FIELD',
	'FLD'        :  'FIELD',
	'FIELDS'     :  'FIELDS',
	'FLDS'       :  'FIELDS',
	'FLAT'       :  'FLAT',
	'FLT'        :  'FLAT',
	'FLATS'      :  'FLATS',
	'FLTS'       :  'FLATS',
	'FORD'       :  'FORD',
	'FRD'        :  'FORD',
	'FORDS'      :  'FORDS',
	'FOREST'     :  'FOREST',
	'FORESTS'    :  'FOREST',
	'FRST'       :  'FOREST',
	'FORG'       :  'FORGE',
	'FORGE'      :  'FORGE',
	'FRG'        :  'FORGE',
	'FORGES'     :  'FORGES',
	'FORK'       :  'FORK',
	'FRK'        :  'FORK',
	'FORKS'      :  'FORKS',
	'FRKS'       :  'FORKS',
	'FORT'       :  'FORT',
	'FRT'        :  'FORT',
	'FT'         :  'FORT',
	'FREEWAY'    :  'FREEWAY',
	'FREEWY'     :  'FREEWAY',
	'FRWAY'      :  'FREEWAY',
	'FRWY'       :  'FREEWAY',
	'FWY'        :  'FREEWAY',
	'GARDEN'     :  'GARDEN',
	'GARDN'      :  'GARDEN',
	'GDN'        :  'GARDEN',
	'GRDEN'      :  'GARDEN',
	'GRDN'       :  'GARDEN',
	'GARDENS'    :  'GARDENS',
	'GDNS'       :  'GARDENS',
	'GRDNS'      :  'GARDENS',
	'GATEWAY'    :  'GATEWAY',
	'GATEWY'     :  'GATEWAY',
	'GATWAY'     :  'GATEWAY',
	'GTWAY'      :  'GATEWAY',
	'GTWY'       :  'GATEWAY',
	'GLEN'       :  'GLEN',
	'GLN'        :  'GLEN',
	'GLENS'      :  'GLENS',
	'GREEN'      :  'GREEN',
	'GRN'        :  'GREEN',
	'GREENS'     :  'GREENS',
	'GROV'       :  'GROVE',
	'GROVE'      :  'GROVE',
	'GRV'        :  'GROVE',
	'GROVES'     :  'GROVES',
	'HARB'       :  'HARBOR',
	'HARBOR'     :  'HARBOR',
	'HARBR'      :  'HARBOR',
	'HBR'        :  'HARBOR',
	'HRBOR'      :  'HARBOR',
	'HARBORS'    :  'HARBORS',
	'HAVEN'      :  'HAVEN',
	'HAVN'       :  'HAVEN',
	'HVN'        :  'HAVEN',
	'HEIGHT'     :  'HEIGHTS',
	'HEIGHTS'    :  'HEIGHTS',
	'HGTS'       :  'HEIGHTS',
	'HT'         :  'HEIGHTS',
	'HTS'        :  'HEIGHTS',
	'HIGHWAY'    :  'HIGHWAY',
	'HIGHWY'     :  'HIGHWAY',
	'HIWAY'      :  'HIGHWAY',
	'HIWY'       :  'HIGHWAY',
	'HWAY'       :  'HIGHWAY',
	'HWY'        :  'HIGHWAY',
	'HILL'       :  'HILL',
	'HL'         :  'HILL',
	'HILLS'      :  'HILLS',
	'HLS'        :  'HILLS',
	'HLLW'       :  'HOLLOW',
	'HOLLOW'     :  'HOLLOW',
	'HOLLOWS'    :  'HOLLOW',
	'HOLW'       :  'HOLLOW',
	'HOLWS'      :  'HOLLOW',
	'INLET'      :  'INLET',
	'INLT'       :  'INLET',
	'IS'         :  'ISLAND',
	'ISLAND'     :  'ISLAND',
	'ISLND'      :  'ISLAND',
	'ISLANDS'    :  'ISLANDS',
	'ISLNDS'     :  'ISLANDS',
	'ISS'        :  'ISLANDS',
	'ISLE'       :  'ISLE',
	'ISLES'      :  'ISLE',
	'JCT'        :  'JUNCTION',
	'JCTION'     :  'JUNCTION',
	'JCTN'       :  'JUNCTION',
	'JUNCTION'   :  'JUNCTION',
	'JUNCTN'     :  'JUNCTION',
	'JUNCTON'    :  'JUNCTION',
	'JCTNS'      :  'JUNCTIONS',
	'JCTS'       :  'JUNCTIONS',
	'JUNCTIONS'  :  'JUNCTIONS',
	'KEY'        :  'KEY',
	'KY'         :  'KEY',
	'KEYS'       :  'KEYS',
	'KYS'        :  'KEYS',
	'KNL'        :  'KNOLL',
	'KNOL'       :  'KNOLL',
	'KNOLL'      :  'KNOLL',
	'KNLS'       :  'KNOLLS',
	'KNOLLS'     :  'KNOLLS',
	'LAKE'       :  'LAKE',
	'LK'         :  'LAKE',
	'LAKES'      :  'LAKES',
	'LKS'        :  'LAKES',
	'LAND'       :  'LAND',
	'LANDING'    :  'LANDING',
	'LNDG'       :  'LANDING',
	'LNDNG'      :  'LANDING',
	'LA'         :  'LANE',
	'LANE'       :  'LANE',
	'LANES'      :  'LANE',
	'LN'         :  'LANE',
	'LGT'        :  'LIGHT',
	'LIGHT'      :  'LIGHT',
	'LIGHTS'     :  'LIGHTS',
	'LF'         :  'LOAF',
	'LOAF'       :  'LOAF',
	'LCK'        :  'LOCK',
	'LOCK'       :  'LOCK',
	'LCKS'       :  'LOCKS',
	'LOCKS'      :  'LOCKS',
	'LDG'        :  'LODGE',
	'LDGE'       :  'LODGE',
	'LODG'       :  'LODGE',
	'LODGE'      :  'LODGE',
	'LOOP'       :  'LOOP',
	'LOOPS'      :  'LOOP',
	'MALL'       :  'MALL',
	'MANOR'      :  'MANOR',
	'MNR'        :  'MANOR',
	'MANORS'     :  'MANORS',
	'MNRS'       :  'MANORS',
	'MDW'        :  'MEADOW',
	'MEADOW'     :  'MEADOW',
	'MDWS'       :  'MEADOWS',
	'MEADOWS'    :  'MEADOWS',
	'MEDOWS'     :  'MEADOWS',
	'MEWS'       :  'MEWS',
	'MILL'       :  'MILL',
	'ML'         :  'MILL',
	'MILLS'      :  'MILLS',
	'MLS'        :  'MILLS',
	'MISSION'    :  'MISSION',
	'MISSN'      :  'MISSION',
	'MSN'        :  'MISSION',
	'MSSN'       :  'MISSION',
	'MOTORWAY'   :  'MOTORWAY',
	'MNT'        :  'MOUNT',
	'MOUNT'      :  'MOUNT',
	'MT'         :  'MOUNT',
	'MNTAIN'     :  'MOUNTAIN',
	'MNTN'       :  'MOUNTAIN',
	'MOUNTAIN'   :  'MOUNTAIN',
	'MOUNTIN'    :  'MOUNTAIN',
	'MTIN'       :  'MOUNTAIN',
	'MTN'        :  'MOUNTAIN',
	'MNTNS'      :  'MOUNTAINS',
	'MOUNTAINS'  :  'MOUNTAINS',
	'NCK'        :  'NECK',
	'NECK'       :  'NECK',
	'ORCH'       :  'ORCHARD',
	'ORCHARD'    :  'ORCHARD',
	'ORCHRD'     :  'ORCHARD',
	'OVAL'       :  'OVAL',
	'OVL'        :  'OVAL',
	'OVERPASS'   :  'OVERPASS',
	'PARK'       :  'PARK',
	'PK'         :  'PARK',
	'PRK'        :  'PARK',
	'PARKS'      :  'PARKS',
	'PARKWAY'    :  'PARKWAY',
	'PARKWY'     :  'PARKWAY',
	'PKWAY'      :  'PARKWAY',
	'PKWY'       :  'PARKWAY',
	'PKY'        :  'PARKWAY',
	'PARKWAYS'   :  'PARKWAYS',
	'PKWYS'      :  'PARKWAYS',
	'PASS'       :  'PASS',
	'PASSAGE'    :  'PASSAGE',
	'PATH'       :  'PATH',
	'PATHS'      :  'PATH',
	'PIKE'       :  'PIKE',
	'PIKES'      :  'PIKE',
	'PINE'       :  'PINE',
	'PINES'      :  'PINES',
	'PNES'       :  'PINES',
	'PL'         :  'PLACE',
	'PLACE'      :  'PLACE',
	'PLAIN'      :  'PLAIN',
	'PLN'        :  'PLAIN',
	'PLAINES'    :  'PLAINS',
	'PLAINS'     :  'PLAINS',
	'PLNS'       :  'PLAINS',
	'PLAZA'      :  'PLAZA',
	'PLZ'        :  'PLAZA',
	'PLZA'       :  'PLAZA',
	'POINT'      :  'POINT',
	'PT'         :  'POINT',
	'POINTS'     :  'POINTS',
	'PTS'        :  'POINTS',
	'PORT'       :  'PORT',
	'PRT'        :  'PORT',
	'PORTS'      :  'PORTS',
	'PRTS'       :  'PORTS',
	'PR'         :  'PRAIRIE',
	'PRAIRIE'    :  'PRAIRIE',
	'PRARIE'     :  'PRAIRIE',
	'PRR'        :  'PRAIRIE',
	'RAD'        :  'RADIAL',
	'RADIAL'     :  'RADIAL',
	'RADIEL'     :  'RADIAL',
	'RADL'       :  'RADIAL',
	'RAMP'       :  'RAMP',
	'RANCH'      :  'RANCH',
	'RANCHES'    :  'RANCH',
	'RNCH'       :  'RANCH',
	'RNCHS'      :  'RANCH',
	'RAPID'      :  'RAPID',
	'RPD'        :  'RAPID',
	'RAPIDS'     :  'RAPIDS',
	'RPDS'       :  'RAPIDS',
	'REST'       :  'REST',
	'RST'        :  'REST',
	'RDG'        :  'RIDGE',
	'RDGE'       :  'RIDGE',
	'RIDGE'      :  'RIDGE',
	'RDGS'       :  'RIDGES',
	'RIDGES'     :  'RIDGES',
	'RIV'        :  'RIVER',
	'RIVER'      :  'RIVER',
	'RIVR'       :  'RIVER',
	'RVR'        :  'RIVER',
	'RD'         :  'ROAD',
	'ROAD'       :  'ROAD',
	'RDS'        :  'ROADS',
	'ROADS'      :  'ROADS',
	'ROUTE'      :  'ROUTE',
	'ROW'        :  'ROW',
	'RUE'        :  'RUE',
	'RUN'        :  'RUN',
	'SHL'        :  'SHOAL',
	'SHOAL'      :  'SHOAL',
	'SHLS'       :  'SHOALS',
	'SHOALS'     :  'SHOALS',
	'SHOAR'      :  'SHORE',
	'SHORE'      :  'SHORE',
	'SHR'        :  'SHORE',
	'SHOARS'     :  'SHORES',
	'SHORES'     :  'SHORES',
	'SHRS'       :  'SHORES',
	'SKYWAY'     :  'SKYWAY',
	'SPG'        :  'SPRING',
	'SPNG'       :  'SPRING',
	'SPRING'     :  'SPRING',
	'SPRNG'      :  'SPRING',
	'SPGS'       :  'SPRINGS',
	'SPNGS'      :  'SPRINGS',
	'SPRINGS'    :  'SPRINGS',
	'SPRNGS'     :  'SPRINGS',
	'SPUR'       :  'SPUR',
	'SPURS'      :  'SPURS',
	'SQ'         :  'SQUARE',
	'SQR'        :  'SQUARE',
	'SQRE'       :  'SQUARE',
	'SQU'        :  'SQUARE',
	'SQUARE'     :  'SQUARE',
	'SQRS'       :  'SQUARES',
	'SQUARES'    :  'SQUARES',
	'STA'        :  'STATION',
	'STATION'    :  'STATION',
	'STATN'      :  'STATION',
	'STN'        :  'STATION',
	'STRA'       :  'STRAVENUE',
	'STRAV'      :  'STRAVENUE',
	'STRAVE'     :  'STRAVENUE',
	'STRAVEN'    :  'STRAVENUE',
	'STRAVENUE'  :  'STRAVENUE',
	'STRAVN'     :  'STRAVENUE',
	'STRVN'      :  'STRAVENUE',
	'STRVNUE'    :  'STRAVENUE',
	'STREAM'     :  'STREAM',
	'STREME'     :  'STREAM',
	'STRM'       :  'STREAM',
	'ST'         :  'STREET',
	'STR'        :  'STREET',
	'STREET'     :  'STREET',
	'STRT'       :  'STREET',
	'STREETS'    :  'STREETS',
	'SMT'        :  'SUMMIT',
	'SUMIT'      :  'SUMMIT',
	'SUMITT'     :  'SUMMIT',
	'SUMMIT'     :  'SUMMIT',
	'TER'        :  'TERRACE',
	'TERR'       :  'TERRACE',
	'TERRACE'    :  'TERRACE',
	'THROUGHWAY' :  'THROUGHWAY',
	'TRACE'      :  'TRACE',
	'TRACES'     :  'TRACE',
	'TRCE'       :  'TRACE',
	'TRACK'      :  'TRACK',
	'TRACKS'     :  'TRACK',
	'TRAK'       :  'TRACK',
	'TRK'        :  'TRACK',
	'TRKS'       :  'TRACK',
	'TRAFFICWAY' :  'TRAFFICWAY',
	'TRFY'       :  'TRAFFICWAY',
	'TR'         :  'TRAIL',
	'TRAIL'      :  'TRAIL',
	'TRAILS'     :  'TRAIL',
	'TRL'        :  'TRAIL',
	'TRLS'       :  'TRAIL',
	'TUNEL'      :  'TUNNEL',
	'TUNL'       :  'TUNNEL',
	'TUNLS'      :  'TUNNEL',
	'TUNNEL'     :  'TUNNEL',
	'TUNNELS'    :  'TUNNEL',
	'TUNNL'      :  'TUNNEL',
	'TPK'        :  'TURNPIKE',
	'TPKE'       :  'TURNPIKE',
	'TRNPK'      :  'TURNPIKE',
	'TRPK'       :  'TURNPIKE',
	'TURNPIKE'   :  'TURNPIKE',
	'TURNPK'     :  'TURNPIKE',
	'UNDERPASS'  :  'UNDERPASS',
	'UN'         :  'UNION',
	'UNION'      :  'UNION',
	'UNIONS'     :  'UNIONS',
	'VALLEY'     :  'VALLEY',
	'VALLY'      :  'VALLEY',
	'VLLY'       :  'VALLEY',
	'VLY'        :  'VALLEY',
	'VALLEYS'    :  'VALLEYS',
	'VLYS'       :  'VALLEYS',
	'VDCT'       :  'VIADUCT',
	'VIA'        :  'VIADUCT',
	'VIADCT'     :  'VIADUCT',
	'VIADUCT'    :  'VIADUCT',
	'VIEW'       :  'VIEW',
	'VW'         :  'VIEW',
	'VIEWS'      :  'VIEWS',
	'VWS'        :  'VIEWS',
	'VILL'       :  'VILLAGE',
	'VILLAG'     :  'VILLAGE',
	'VILLAGE'    :  'VILLAGE',
	'VILLG'      :  'VILLAGE',
	'VILLIAGE'   :  'VILLAGE',
	'VLG'        :  'VILLAGE',
	'VILLAGES'   :  'VILLAGES',
	'VLGS'       :  'VILLAGES',
	'VILLE'      :  'VILLE',
	'VL'         :  'VILLE',
	'VIS'        :  'VISTA',
	'VIST'       :  'VISTA',
	'VISTA'      :  'VISTA',
	'VST'        :  'VISTA',
	'VSTA'       :  'VISTA',
	'WALK'       :  'WALK',
	'WALKS'      :  'WALKS',
	'WALL'       :  'WALL',
	'WAY'        :  'WAY',
	'WY'         :  'WAY',
	'WAYS'       :  'WAYS',
	'WELL'       :  'WELL',
	'WELLS'      :  'WELLS',
	'WLS'        :  'WELLS',
	}

usps_street_suffix_abbr = {
	'ALLEY'      :  'ALY',
	'ANNEX'      :  'ANX',
	'ARCADE'     :  'ARC',
	'AVENUE'     :  'AVE',
	'BAYOO'      :  'BYU',
	'BEACH'      :  'BCH',
	'BEND'       :  'BND',
	'BLUFF'      :  'BLF',
	'BLUFFS'     :  'BLFS',
	'BOTTOM'     :  'BTM',
	'BOULEVARD'  :  'BLVD',
	'BRANCH'     :  'BR',
	'BRIDGE'     :  'BRG',
	'BROOK'      :  'BRK',
	'BROOKS'     :  'BRKS',
	'BURG'       :  'BG',
	'BURGS'      :  'BGS',
	'BYPASS'     :  'BYP',
	'CAMP'       :  'CP',
	'CANYON'     :  'CYN',
	'CAPE'       :  'CPE',
	'CAUSEWAY'   :  'CSWY',
	'CENTER'     :  'CTR',
	'CENTERS'    :  'CTRS',
	'CIRCLE'     :  'CIR',
	'CIRCLES'    :  'CIRS',
	'CLIFF'      :  'CLF',
	'CLIFFS'     :  'CLFS',
	'CLUB'       :  'CLB',
	'COMMON'     :  'CMN',
	'CORNER'     :  'COR',
	'CORNERS'    :  'CORS',
	'COURSE'     :  'CRSE',
	'COURT'      :  'CT',
	'COURTS'     :  'CTS',
	'COVE'       :  'CV',
	'COVES'      :  'CVS',
	'CREEK'      :  'CRK',
	'CRESCENT'   :  'CRES',
	'CREST'      :  'CRST',
	'CROSSING'   :  'XING',
	'CROSSROAD'  :  'XRD',
	'CURVE'      :  'CURV',
	'DALE'       :  'DL',
	'DAM'        :  'DM',
	'DIVIDE'     :  'DV',
	'DRIVE'      :  'DR',
	'DRIVES'     :  'DRS',
	'ESTATE'     :  'EST',
	'ESTATES'    :  'ESTS',
	'EXPRESSWAY' :  'EXPY',
	'EXTENSION'  :  'EXT',
	'EXTENSIONS' :  'EXTS',
	'FALL'       :  'FALL',
	'FALLS'      :  'FLS',
	'FERRY'      :  'FRY',
	'FIELD'      :  'FLD',
	'FIELDS'     :  'FLDS',
	'FLAT'       :  'FLT',
	'FLATS'      :  'FLTS',
	'FORD'       :  'FRD',
	'FORDS'      :  'FRDS',
	'FOREST'     :  'FRST',
	'FORGE'      :  'FRG',
	'FORGES'     :  'FRGS',
	'FORK'       :  'FRK',
	'FORKS'      :  'FRKS',
	'FORT'       :  'FT',
	'FREEWAY'    :  'FWY',
	'GARDEN'     :  'GDN',
	'GARDENS'    :  'GDNS',
	'GATEWAY'    :  'GTWY',
	'GLEN'       :  'GLN',
	'GLENS'      :  'GLNS',
	'GREEN'      :  'GRN',
	'GREENS'     :  'GRNS',
	'GROVE'      :  'GRV',
	'GROVES'     :  'GRVS',
	'HARBOR'     :  'HBR',
	'HARBORS'    :  'HBRS',
	'HAVEN'      :  'HVN',
	'HEIGHTS'    :  'HTS',
	'HIGHWAY'    :  'HWY',
	'HILL'       :  'HL',
	'HILLS'      :  'HLS',
	'HOLLOW'     :  'HOLW',
	'INLET'      :  'INLT',
	'ISLAND'     :  'IS',
	'ISLANDS'    :  'ISS',
	'ISLE'       :  'ISLE',
	'JUNCTION'   :  'JCT',
	'JUNCTIONS'  :  'JCTS',
	'KEY'        :  'KY',
	'KEYS'       :  'KYS',
	'KNOLL'      :  'KNL',
	'KNOLLS'     :  'KNLS',
	'LAKE'       :  'LK',
	'LAKES'      :  'LKS',
	'LAND'       :  'LAND',
	'LANDING'    :  'LNDG',
	'LANE'       :  'LN',
	'LIGHT'      :  'LGT',
	'LIGHTS'     :  'LGTS',
	'LOAF'       :  'LF',
	'LOCK'       :  'LCK',
	'LOCKS'      :  'LCKS',
	'LODGE'      :  'LDG',
	'LOOP'       :  'LOOP',
	'MALL'       :  'MALL',
	'MANOR'      :  'MNR',
	'MANORS'     :  'MNRS',
	'MEADOW'     :  'MDW',
	'MEADOWS'    :  'MDWS',
	'MEWS'       :  'MEWS',
	'MILL'       :  'ML',
	'MILLS'      :  'MLS',
	'MISSION'    :  'MSN',
	'MOTORWAY'   :  'MTWY',
	'MOUNT'      :  'MT',
	'MOUNTAIN'   :  'MTN',
	'MOUNTAINS'  :  'MTNS',
	'NECK'       :  'NCK',
	'ORCHARD'    :  'ORCH',
	'OVAL'       :  'OVAL',
	'OVERPASS'   :  'OPAS',
	'PARK'       :  'PARK',
	'PARKWAY'    :  'PKWY',
	'PASS'       :  'PASS',
	'PASSAGE'    :  'PSGE',
	'PATH'       :  'PATH',
	'PIKE'       :  'PIKE',
	'PINE'       :  'PNE',
	'PINES'      :  'PNES',
	'PLACE'      :  'PL',
	'PLAIN'      :  'PLN',
	'PLAINS'     :  'PLNS',
	'PLAZA'      :  'PLZ',
	'POINT'      :  'PT',
	'POINTS'     :  'PTS',
	'PORT'       :  'PRT',
	'PORTS'      :  'PRTS',
	'PRAIRIE'    :  'PR',
	'RADIAL'     :  'RADL',
	'RAMP'       :  'RAMP',
	'RANCH'      :  'RNCH',
	'RAPID'      :  'RPD',
	'RAPIDS'     :  'RPDS',
	'REST'       :  'RST',
	'RIDGE'      :  'RDG',
	'RIDGES'     :  'RDGS',
	'RIVER'      :  'RIV',
	'ROAD'       :  'RD',
	'ROADS'      :  'RDS',
	'ROUTE'      :  'RTE',
	'ROW'        :  'ROW',
	'RUE'        :  'RUE',
	'RUN'        :  'RUN',
	'SHOAL'      :  'SHL',
	'SHOALS'     :  'SHLS',
	'SHORE'      :  'SHR',
	'SHORES'     :  'SHRS',
	'SKYWAY'     :  'SKWY',
	'SPRING'     :  'SPG',
	'SPRINGS'    :  'SPGS',
	'SPUR'       :  'SPUR',
	'SQUARE'     :  'SQ',
	'SQUARES'    :  'SQS',
	'STATION'    :  'STA',
	'STRAVENUE'  :  'STRA',
	'STREAM'     :  'STRM',
	'STREET'     :  'ST',
	'STREETS'    :  'STS',
	'SUMMIT'     :  'SMT',
	'TERRACE'    :  'TER',
	'THROUGHWAY' :  'TRWY',
	'TRACE'      :  'TRCE',
	'TRACK'      :  'TRAK',
	'TRAFFICWAY' :  'TRFY',
	'TRAIL'      :  'TRL',
	'TUNNEL'     :  'TUNL',
	'TURNPIKE'   :  'TPKE',
	'UNDERPASS'  :  'UPAS',
	'UNION'      :  'UN',
	'UNIONS'     :  'UNS',
	'VALLEY'     :  'VLY',
	'VALLEYS'    :  'VLYS',
	'VIADUCT'    :  'VIA',
	'VIEW'       :  'VW',
	'VIEWS'      :  'VWS',
	'VILLAGE'    :  'VLG',
	'VILLAGES'   :  'VLGS',
	'VILLE'      :  'VL',
	'VISTA'      :  'VIS',
	'WALK'       :  'WALK',
	'WALL'       :  'WALL',
	'WAY'        :  'WAY',
	'WAYS'       :  'WAYS',
	'WELL'       :  'WL',
	'WELLS'      :  'WLS',
	}

usps_secondary_designator = {
    'APARTMENT'  :  'APT',
    'APT'        :  'APT',
    'BASEMENT'   :  'BSMT',
    'BSMT'       :  'BSMT',
    'BUILDING'   :  'BLDG',
    'BLDG'       :  'BLDG',
    'DEPARTMENT' :  'DEPT',
    'DEPT'       :  'DEPT',
    'FLOOR'      :  'FLOOR',
    'FLR'        :  'FLOOR',
    'FRONT'      :  'FRONT',
    'FRNT'       :  'FRONT',
    'HANGER'     :  'HNGR',
    'HNGR'       :  'HNGR',
    'KEY'        :  'KEY',
    'KEY'        :  'KEY',
    'LOBBY'      :  'LOBBY',
    'LBBY'       :  'LOBBY',
    'LOT'        :  'LOT',
    'LOWER'      :  'LOWER',
    'LOWR'       :  'LOWER',
    'OFFICE'     :  'OFC',
    'OFC'        :  'OFC',
    'PENTHOUSE'  :  'PH',
    'PH'         :  'PH',
    'PIER'       :  'PIER',
    'REAR'       :  'REAR',
    'ROOM'       :  'RM',
    'RM'         :  'RM',
    'SIDE'       :  'SIDE',
    'SLIP'       :  'SLIP',
    'SLIP'       :  'SLIP',
    'SPACE'      :  'SPC',
    'SPC'        :  'SPC',
    'STOP'       :  'STOP',
    'SUITE'      :  'STE',
    'STE'        :  'STE',
    'TRAILER'    :  'TRLR',
    'TRLR'       :  'TRLR',
    'UNIT'       :  'UNIT',
    'UPPER'      :  'UPPER',
    'UPPR'       :  'UPPER',
    '#'          :  '#',
    }

pobox = translator(keep='BOPX')

abbr_ordinal = dict(
    NORTHEAST='NE', NORTH='N',
    NORTHWEST='NW', SOUTH='S',
    SOUTHEAST='SE', EAST='E',
    SOUTHWEST='SW', WEST='W',
    )
full_ordinal = dict([(v, k) for k, v in abbr_ordinal.items()])

all_ordinals = set(full_ordinal.keys() + abbr_ordinal.keys())

class AddressSegment(AutoEnum):
    misc = "not currently tracked"
    ordinal = "N S E W etc"
    secondary = "apt bldg floor etc"
    street = "st ave blvd etc"

def ordinals(text):
    # we want, at most, one ordinal abbreviation in a row (no sequential)
    # if two ordinal type words appear together which one gets abbreviated depends
    # on where they are: if at the end of the address (or just before a Secondary
    # Unit Designator (apt, bldng, flr, etc), then the second one as shortened,
    # otherwise the first one is;
    # if there is only one ordinal, but less than four components (e.g.
    # 823 West St), then we do not shorten it.
    # if two ordinals are separated by more than one non-secondary piece, shorten
    # both

    pieces = text
    if isinstance(pieces, String):
        pieces = pieces.split()
    AS = AddressSegment
    tokens = []
    for i, p in enumerate(pieces):
        if p in all_ordinals:
            tokens.append(AS.ordinal)
        elif p in usps_secondary_designator:
            tokens.append(AS.secondary)
        elif p in usps_street_suffix_common:
            tokens.append(AS.street)
        elif i >= 2 and p.startswith('#'):
            tokens.append(AS.secondary)
        else:
            tokens.append(AS.misc)
    # there should be, at most, one AS.street token, and it should be either
    # the last, or next to last, token in the primary portion (before any
    # AS.secondary token); if we find a AS.street token anywhere else, change
    # it to a AS.misc token
    for i, t in enumerate(tokens):
        if t is AS.secondary:
            secondary = i
            break
    else:
        secondary = -1
    final = len(tokens) - 1
    if secondary != -1:
        final = secondary - 1
    for i, token in enumerate(tokens):
        if token is AS.secondary:
            break
        if token is AS.street:
            if i == final:
                continue
            elif i == final -1 and tokens[final] is AS.ordinal:
                continue
            tokens[i] = AS.misc
    primary = []
    secondary = []
    if AS.secondary in tokens:
        index = tokens.index(AS.secondary)
        for p in pieces[index:]:
            secondary.append(
                    usps_secondary_designator.get(p, 
                        full_ordinal.get(p, p)))
        tokens = tokens[:index]
        pieces = pieces[:index]
    counted_ordinals = tokens.count(AS.ordinal)
    if len(tokens) <= 3:
        for p in pieces:
            if len(p) != 1:
                p = full_ordinal.get(p, p)
            primary.append(p)
    elif counted_ordinals == 1:
        for i, p in enumerate(pieces):
            if tokens[i+1:i+2] != [AS.street]:
                p = abbr_ordinal.get(p, p)
            primary.append(p)
    elif counted_ordinals:
        ending_ordinal = 0
        if tokens[-1] is AS.ordinal:
            ending_ordinal = len(tokens) - 1
        prev_ordinal = False
        for i, (piece, token) in enumerate(zip(pieces, tokens)):
            if token is AS.ordinal:
                if prev_ordinal is True:
                    if len(piece) != 1:
                        piece = full_ordinal.get(piece, piece)
                    primary.append(piece)
                    prev_ordinal = False
                else:
                    if i + 1 == ending_ordinal:
                        if len(piece) != 1:
                            piece = full_ordinal.get(piece, piece)
                        primary.append(piece)
                    else:
                        if tokens[i+1:i+2] != [AS.street]:
                            piece = abbr_ordinal.get(piece, piece)
                        primary.append(piece)
                        prev_ordinal = True
            else:
                prev_ordinal = False
                primary.append(piece)
    else:
        primary = pieces
    pieces, primary = primary, []
    for piece, token in zip(pieces, tokens):
        if token is AS.street:
            piece = usps_street_suffix_abbr[piece]
        primary.append(piece)
    return primary + secondary


def normalize_address(line):
    if not line.strip():
        return line
    orig_line = line
    line = ' '.join(line.replace(',',' ').replace('.',' ').replace('-',' ').upper().split())
    if pobox(line) == 'POBOX':
        index = line.index('X')
        trailer = line[index+1:]
        if trailer and not trailer.isalpha():
            line = ' '.join(['PO BOX', line[index+1:].strip()])
            return line
    pieces = line.split()
    if not has_digits(pieces[0]) and pieces[0].upper() not in spelled_out_numbers:
        return orig_line
    line = []
    for p in pieces:
        line.append(usps_street_suffix_common.get(p, p))
    line = ordinals(line)
    return ' '.join(line)


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
        elif isinstance(name, String) and name[0:1] == '_':
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


_memory_sentinel = Sentinel("amnesiac")


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

    def __init__(yo, postal, country=None):
        alpha2num = {
                'I' : '1',
                'O' : '0',
                'S' : '5',
                }
        num2alpha = {
                '1'   : 'I',
                '0'   : 'O',
                '5'   : 'S',
                }
        postal = postal.strip('-,')
        if len(postal.replace('-', '')) in (5, 9):
            yo.code = postal[:5]
        elif postal[:5].isdigit():
            yo.code = postal[:5]
        elif (has_alpha(postal) and len(postal.replace(' ', '')) == 6
        and   (not country or country == 'CANADA')):
            # alpha-num-alpha num-alpha-num
            postal = list(postal.replace(' ', '').upper())
            for i in (0, 2, 4):
                postal[i] = num2alpha.get(postal[i], postal[i])
            for i in (1, 3, 5):
                postal[i] = alpha2num.get(postal[i], postal[i])
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
    def __repr__(yo):
        return repr(yo.code)
    def __str__(yo):
        return yo.code


def fix_phone(text):
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


def fix_date(text):
    '''takes mmddyy (with yy in hex (A0 = 2000)) and returns a Date'''
    text = text.strip()
    if len(text) != 6:
        return None
    yyyy, mm, dd = int(text[4:], 16)-160+2000, int(text[:2]), int(text[2:4])
    return Date(yyyy, mm, dd)

def text_to_date(text, format='ymd'):
    '''(yy)yymmdd'''
    if not text.strip():
        return None
    dd = mm = yyyy = None
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
    if dd is None:
        raise ValueError("don't know how to convert %r using %r" % (text, format))
    return Date(yyyy, mm, dd)

def text_to_time(text):
    if not text.strip():
        return None
    return Time(int(text[:2]), int(text[2:]))

def simplegeneric(func):
    """Make a trivial single-dispatch generic function (from Python3.4 functools)"""
    registry = {}
    def wrapper(*args, **kw):
        ob = args[0]
        try:
            cls = ob.__class__
        except AttributeError:
            cls = type(ob)
        try:
            mro = cls.__mro__
        except AttributeError:
            try:
                class cls(cls, object):
                    pass
                mro = cls.__mro__[1:]
            except TypeError:
                mro = object,   # must be an ExtensionClass or some such  :(
        for t in mro:
            if t in registry:
                return registry[t](*args, **kw)
        else:
            return func(*args, **kw)
    try:
        wrapper.__name__ = func.__name__
    except (TypeError, AttributeError):
        pass    # Python 2.3 doesn't allow functions to be renamed

    def register(typ, func=None):
        if func is None:
            return lambda f: register(typ, f)
        registry[typ] = func
        return func

    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__
    wrapper.register = register
    return wrapper

def mail(server, port, sender, receiver, message):
    """sends email.message to server:port

    receiver is a list of addresses
    """
    msg = MIMEText(message.get_payload())
    for address in receiver:
        msg['To'] = address
    msg['From'] = sender
    for header, value in message.items():
        if header in ('To','From'):
            continue
        msg[header] = value
    smtp = smtplib.SMTP(server, port)
    try:
        send_errs = smtp.sendmail(msg['From'], receiver, msg.as_string())
    except smtplib.SMTPRecipientsRefused, exc:
        send_errs = exc.recipients
    smtp.quit()
    errs = {}
    if send_errs:
        for user in send_errs:
            server = 'mail.' + user.split('@')[1]
            smtp = smtplib.SMTP(server, 25)
            try:
                smtp.sendmail(msg['From'], [user], msg.as_string())
            except smtplib.SMTPRecipientsRefused, exc:
                errs[user] = [send_errs[user], exc.recipients[user]]
            smtp.quit()
    for user, errors in errs.items():
        for code, response in errors:
            syslog.syslog('%s --> %s: %s' % (user, code, response))

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


