import sys
if sys.version_info[0] == 3:
    raise SystemExit("Django-Tagcon does not yet support Python 3")
if sys.version_info[0] != 2 or sys.version_info[1] < 5:
    raise SystemExit("Django-Tagcon requires Python 2.5 or greater")
del sys

from tagcon.base import TemplateTag
from tagcon.exceptions import *
from tagcon.args import *
