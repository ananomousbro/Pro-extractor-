import os
files = [
    "Extractor/modules/freeappx.py",
    "Extractor/modules/freepw.py",
    "Extractor/modules/freecp.py"
]
for file in files:
    with open(file, "r") as f:
        content = f.read()
    content = content.replace("from pyromod.exceptions import ListenerTimeout", "import asyncio\nListenerTimeout = asyncio.TimeoutError")
    with open(file, "w") as f:
        f.write(content)
