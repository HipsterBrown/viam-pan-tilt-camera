import asyncio
from dataclasses import dataclass
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Union,
    cast,
)

from typing_extensions import Self
from viam.components.base import Base, Vector3
from viam.components.servo import Servo
from viam.operations import run_with_operation
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import Geometry, ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.utils import ValueTypes, struct_to_dict


@dataclass(frozen=True)
class ServoLimit:
    min: int = 0
    max: int = 180


class BaseControl(Base, EasyResource):
    # To enable debug-level logging, either run viam-server with the --debug option,
    # or configure your resource/machine to display debug logs.
    MODEL: ClassVar[Model] = Model(
        ModelFamily("hipsterbrown", "pan-tilt-camera"), "base-control"
    )

    tilt_limit: ServoLimit
    pan_limit: ServoLimit
    pan: Servo
    tilt: Servo
    step_amount: int = 10

    state: Union[Literal["moving"], Literal["stopped"]] = "stopped"
    task_lock = asyncio.Lock()

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        """This method creates a new instance of this Base component.
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

        pan_servo, tilt_servo = attrs.get("pan", ""), attrs.get("tilt", "")
        if pan_servo == "" or tilt_servo == "":
            raise Exception(
                "`pan` and `tilt` servo component names are required for configuration."
            )

        return [str(pan_servo), str(tilt_servo)]

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        """This method allows you to dynamically update your service when it receives a new `config` object.

        Args:
            config (ComponentConfig): The new configuration
            dependencies (Mapping[ResourceName, ResourceBase]): Any dependencies (both implicit and explicit)
        """
        attrs = struct_to_dict(config.attributes)

        pan_servo, tilt_servo = str(attrs.get("pan", "")), str(attrs.get("tilt", ""))

        self.pan = cast(Servo, dependencies.get(Servo.get_resource_name(pan_servo)))
        self.pan_limit = ServoLimit()
        self.tilt = cast(Servo, dependencies.get(Servo.get_resource_name(tilt_servo)))
        self.tilt_limit = ServoLimit()

        return

    @dataclass
    class Properties(Base.Properties):
        pass

    async def move_straight(
        self,
        distance: int,
        velocity: float,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        self.logger.error("`move_straight` is not implemented")
        raise NotImplementedError()

    async def spin(
        self,
        angle: float,
        velocity: float,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        self.logger.error("`spin` is not implemented")
        raise NotImplementedError()

    async def set_power(
        self,
        linear: Vector3,
        angular: Vector3,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        await self.task_lock.acquire()
        self.state = "moving"
        self.logger.debug(f"set_power - linear: {linear}, angular: {angular}")
        try:
            current_tilt_position, current_pan_position = await asyncio.gather(
                self.tilt.get_position(), self.pan.get_position()
            )
            tasks = []
            if linear.y:
                next_tilt_position = int(
                    max(
                        self.tilt_limit.min,
                        min(
                            self.tilt_limit.max,
                            round(linear.y * self.step_amount * -1)
                            + current_tilt_position,
                        ),
                    )
                )
                self.logger.debug(f"next_tilt_position: {next_tilt_position}")
                tasks.append(self.tilt.move(next_tilt_position))
            if angular.z:
                next_pan_position = int(
                    max(
                        self.pan_limit.min,
                        min(
                            self.pan_limit.max,
                            round(angular.z * self.step_amount) + current_pan_position,
                        ),
                    )
                )
                self.logger.debug(f"next_pan_position: {next_pan_position}")
                tasks.append(self.pan.move(next_pan_position))

            if self.state == "stopped":
                self.logger.debug("set_power operation cancelled. stopping...")
                await self.stop()
                return

            await asyncio.gather(*tasks)
        finally:
            self.state = "stopped"
            self.task_lock.release()

    async def set_velocity(
        self,
        linear: Vector3,
        angular: Vector3,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        self.logger.error("`set_velocity` is not implemented")
        raise NotImplementedError()

    async def stop(
        self,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        try:
            await asyncio.gather(self.pan.stop(), self.tilt.stop())
            self.state = "stopped"
        finally:
            self.task_lock.release()

    async def is_moving(self) -> bool:
        return self.state == "moving" or self.task_lock.locked()

    async def get_properties(
        self, *, timeout: Optional[float] = None, **kwargs
    ) -> Properties:
        self.logger.error("`get_properties` is not implemented")
        raise NotImplementedError()

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Mapping[str, ValueTypes]:
        self.logger.error("`do_command` is not implemented")
        raise NotImplementedError()

    async def get_geometries(
        self, *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None
    ) -> List[Geometry]:
        self.logger.error("`get_geometries` is not implemented")
        raise NotImplementedError()
