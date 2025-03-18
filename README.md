# Module pan-tilt-camera 

A set of components and services for controlling a DIY pan-tilt camera with Viam using servos.

## Model hipsterbrown:pan-tilt-camera:base-control

Control the direction of a camera with a single component by emulating a mobile base. Only the `set_power`, `stop`, and `is_moving` methods are supported.

### Configuration
The following attribute template can be used to configure this model:

```json
{
    "pan": <string>,
    "tilt": <string>
}
```

#### Attributes

The following attributes are available for this model:

| Name          | Type   | Inclusion | Description                |
|---------------|--------|-----------|----------------------------|
| `pan` | string  | Required  | The name of the servo component that controls the left/right direction of the camera |
| `tilt` | string | Required  | The name of the servo component that controls the up/down direction of the camera |

#### Example Configuration

```json
{
  "pan": "pan-servo",
  "tilt": "tilt-servo"
}
```

## Model hipsterbrown:pan-tilt-camera:tracker

Automatically track a detected object using an associated vision service and the base-control component.

### Configuration
The following attribute template can be used to configure this model:

```json
{
    "base_name": <string>,
    "camera_name": <string>,
    "vision_name": <string>,
    "auto_start": <boolean>,
    "confidence_level": <float>,
    "object_label": <string>
}
```

#### Attributes

The following attributes are available for this model:

| Name          | Type   | Inclusion | Description                |
|---------------|--------|-----------|----------------------------|
| `base_name` | string  | Required  | The name of the base-control component that controls the direction of the camera |
| `camera_name` | string | Required  | The name of the camera component that provides images to the vision service |
| `vision_name` | string | Required  | The name of the vision service that provides detections of the configured object label |
| `auto_start` | boolean | Optional  | Defaults to `false`, automatically start the object tracking when the module is active |
| `confidence_level` | float | Optional  | Defaults to `0.55`, the threshold from 0 to 1 for vision service when detecting objects  |
| `object_label` | string | Optional  | Defaults to "Person", the identifier used by the vision service when detecting a relevant object  |

#### Example Configuration

```json
{
    "base_name": "base-1",
    "camera_name": "camera-1",
    "vision_name": "vision-1"
}
```

## Commands

This module implements the following commands to be used by the `DoCommand` method in the Control tab of the Viam app or one of the language SDKs.

**start**

Start the control loop for tracking objects.

```json
{
    "start": []
}
```

**stop**

Stop the control loop.

```json
{
    "stop": []
}
```

