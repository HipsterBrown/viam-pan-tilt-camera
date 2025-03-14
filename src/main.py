import asyncio
from viam.module.module import Module
try:
    from models.base_control import BaseControl
except ModuleNotFoundError:
    # when running as local module with run.sh
    from .models.base_control import BaseControl


if __name__ == '__main__':
    asyncio.run(Module.run_from_registry())
