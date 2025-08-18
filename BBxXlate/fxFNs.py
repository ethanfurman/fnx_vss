import sys
if sys.version_info[0] == 2:
    from ._fxFNs_2 import *
else:
    from ._fxFNs_3 import *
