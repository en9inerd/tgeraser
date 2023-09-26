"""
Code so python -m will executed
"""

import asyncio
from . import core

if __name__ == "__main__":
    asyncio.run(core.main())
