from pathlib import Path
__location__ = Path(__file__).parent.resolve()

import sys
sys.path.insert(1, __location__.__str__() + "/SearchEngine")

import os
os.chdir(__location__.__str__() + "/SearchEngine")

from flask_search_engine import app
application = app
