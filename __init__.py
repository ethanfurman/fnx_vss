import dbf
import enum
import path

import sys
sys.modules['VSS.dbf'] = dbf
sys.modules['VSS.enum'] = enum
sys.modules['VSS.path'] = path

from utils import *
