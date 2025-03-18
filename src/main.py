import asyncio
from viam.module.module import Module

try:
    from models.base_control import BaseControl
    from models.tracker_service import Tracker
except ModuleNotFoundError:
    # when running as local module with run.sh
    from .models.base_control import BaseControl
    from .models.tracker_service import Tracker


if __name__ == "__main__":
    asyncio.run(Module.run_from_registry())
