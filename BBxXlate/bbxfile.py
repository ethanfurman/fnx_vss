import sys
if sys.version_info[0] == 2:
    from ._bbxfile_2 import *
else:
    from ._bbxfile_3 import *
