import asyncio
from threading import Event
from typing import ClassVar, Mapping, Optional, Sequence, cast

from typing_extensions import Self
from viam.components.base import Base, Vector3
from viam.components.camera import Camera
from viam.module.module import Module
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.services.generic import Generic
from viam.services.vision import Vision
from viam.utils import struct_to_dict, ValueTypes


class Tracker(Generic, EasyResource):
    MODEL: ClassVar[Model] = Model(
        ModelFamily("hipsterbrown", "pan-tilt-camera"), "tracker"
    )

    auto_start = False
    task = None
    event = Event()

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        """This method creates a new instance of this Generic service.
        The default implementation sets the name from the `config` parameter and then calls `reconfigure`.

        Args:
            config (ComponentConfig): The configuration for this resource
            dependencies (Mapping[ResourceName, ResourceBase]): The dependencies (both implicit and explicit)

        Returns:
            Self: The resource
        """
        return super().new(config, dependencies)

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        """This method allows you to validate the configuration object received from the machine,
        as well as to return any implicit dependencies based on that `config`.

        Args:
            config (ComponentConfig): The configuration for this resource

        Returns:
            Sequence[str]: A list of implicit dependencies
        """
        attrs = struct_to_dict(config.attributes)

        base_name, camera_name, vision_name = (
            attrs.get("base_name"),
            attrs.get("camera_name"),
            attrs.get("vision_name"),
        )

        if base_name is None:
            raise Exception("Missing required base_name attribute.")

        if camera_name is None:
            raise Exception("Missing required camera_name attribute.")

        if vision_name is None:
            raise Exception("Missing required vision_name attribute.")

        return [str(base_name), str(vision_name), str(camera_name)]

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        """This method allows you to dynamically update your service when it receives a new `config` object.

        Args:
            config (ComponentConfig): The new configuration
            dependencies (Mapping[ResourceName, ResourceBase]): Any dependencies (both implicit and explicit)
        """
        attrs = struct_to_dict(config.attributes)
        self.auto_start = bool(attrs.get("auto_start", self.auto_start))

        self.base = cast(
            Base, dependencies.get(Base.get_resource_name(str(attrs.get("base_name"))))
        )
        self.camera = cast(
            Camera,
            dependencies.get(Camera.get_resource_name(str(attrs.get("camera_name")))),
        )
        self.logger.info(
            f"Camera {attrs.get('camera_name')} - {Camera.get_resource_name(str(attrs.get('camera_name')))}: {self.camera}"
        )
        self.detector = cast(
            Vision,
            dependencies.get(Vision.get_resource_name(str(attrs.get("vision_name")))),
        )

        self.object_label = str(attrs.get("object_label", "Person"))
        self.confidence_level = float(attrs.get("confidence_level", 0.55))

        if self.auto_start:
            self.start()

    async def on_loop(self):
        self.logger.debug(f"Looking for {self.object_label} to track")
        try:
            for _ in range(0, 3):
                await self.camera.get_image()
            image = await self.camera.get_image()

            detections = await self.detector.get_detections(image)
            detections_of_object = [
                detection
                for detection in detections
                if detection.class_name == self.object_label
                and detection.confidence >= self.confidence_level
            ]

            if len(detections_of_object) == 0:
                self.logger.debug(f"No {self.object_label} found")
                await asyncio.sleep(1)
                return

            if len(detections_of_object) > 1:
                detected_object = sorted(
                    detections_of_object,
                    key=lambda detection: (detection.x_max - detection.x_min)
                    * (detection.y_max - detection.y_min),
                    reverse=True,
                )[0]
            else:
                detected_object = detections_of_object[0]

            x_min, x_max, y_min, y_max = (
                detected_object.x_min,
                detected_object.x_max,
                detected_object.y_min,
                detected_object.y_max,
            )
            frame_height, frame_width = image.height, image.width
            if frame_height is None:
                return
            if frame_width is None:
                return

            frame_center_y, frame_center_x = frame_height // 2, frame_width // 2
            box_center_y, box_center_x = (
                y_min + ((y_max - y_min) // 2),
                x_min + ((x_max - x_min) // 2),
            )

            # reverse movement to mirror subject
            tilt_movement = ((box_center_y - frame_center_y) / frame_center_y) * -1
            pan_movement = ((box_center_x - frame_center_x) / frame_center_x) * -1

            await self.base.set_power(
                linear=Vector3(y=tilt_movement),
                angular=Vector3(z=pan_movement),
            )
        except Exception as err:
            self.logger.error(err)
        finally:
            await asyncio.sleep(1)

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Mapping[str, ValueTypes]:
        result = {key: False for key in command.keys()}
        for name, _args in command.items():
            if name == "start":
                self.start()
                result[name] = True
            if name == "stop":
                self.stop()
                result[name] = True
        return result

    def start(self):
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self.control_loop())
        self.event.clear()

    def stop(self):
        self.event.set()
        if self.task is not None:
            self.task.cancel()

    async def control_loop(self):
        while not self.event.is_set():
            await self.on_loop()
            await asyncio.sleep(0)

    def __del__(self):
        self.stop()

    async def close(self):
        self.stop()


if __name__ == "__main__":
    asyncio.run(Module.run_from_registry())
