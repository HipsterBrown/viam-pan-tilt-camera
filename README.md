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
