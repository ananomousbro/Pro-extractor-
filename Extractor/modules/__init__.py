import asyncio

# --- Event Loop Fix (इसे सबसे ऊपर ही रखना है) ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
# ------------------------------------------------

# अगर pyromod import करना है, तो इवेंट लूप सेट होने के बाद ही करें
from pyromod import listen 

import glob
from os.path import basename, dirname, isfile

def __list_all_modules():
    mod_paths = glob.glob(dirname(__file__) + "/*.py")

    all_modules = [
        basename(f)[:-3]
        for f in mod_paths
        if isfile(f) and f.endswith(".py") and not f.endswith("__init__.py")
    ]

    return all_modules


ALL_MODULES = sorted(__list_all_modules())
__all__ = ALL_MODULES + ["ALL_MODULES"]