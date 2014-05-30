import sys

import dbf
sys.modules['VSS.dbf'] = dbf
import enum
sys.modules['VSS.enum'] = enum
import path
sys.modules['VSS.path'] = path

import address
sys.modules['VSS.address'] = address
import finance
sys.modules['VSS.finance'] = finance
import time_machine
sys.modules['VSS.time_machine'] = time_machine
del sys

from utils import *
