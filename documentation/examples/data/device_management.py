from soil.data import SampleTree, SampleTreeConvertible, Value, ValueConvertible


class DeviceSpec(ValueConvertible):
    """
    Device specification including manufacturer, model, and firmware version.

    This demonstrates `ValueConvertible` for storing heterogeneous data
    inside a single Value as a map.
    """

    def __init__(self, manufacturer: str, model: str, firmware: str):
        self._manufacturer = manufacturer
        self._model = model
        self._firmware = firmware

    @property
    def manufacturer(self) -> str:
        return self._manufacturer

    @property
    def model(self) -> str:
        return self._model

    @property
    def firmware(self) -> str:
        return self._firmware

    def toValue(self) -> Value:
        """Convert the specification into a single Value holding a map."""
        return Value({
            "manufacturer": Value(self._manufacturer),
            "model":        Value(self._model),
            "firmware":     Value(self._firmware),
        })

    @classmethod
    def fromValue(cls, value: Value) -> "DeviceSpec":
        """Create a DeviceSpec from a Value holding a map."""
        raw = value.value
        if not isinstance(raw, dict):
            raise ValueError("The value does not have the structure of a DeviceSpec")

        manufacturer = raw.get("manufacturer")
        model = raw.get("model")
        firmware = raw.get("firmware")
        if not all(isinstance(x, Value) for x in (manufacturer, model, firmware)):
            raise ValueError("The value does not have the structure of a DeviceSpec")

        # Type narrow: we've verified these are Value instances
        assert isinstance(manufacturer, Value)
        assert isinstance(model, Value)
        assert isinstance(firmware, Value)

        return cls(
            str(manufacturer.value),
            str(model.value),
            str(firmware.value),
        )


class Sensor(ValueConvertible):
    """
    A single sensor with kind (type), unit, and accuracy.

    This demonstrates `ValueConvertible` for storing sensor metadata
    as a map-Value.
    """

    def __init__(self, kind: str, unit: str, accuracy: float):
        self._kind = kind
        self._unit = unit
        self._accuracy = accuracy

    @property
    def kind(self) -> str:
        return self._kind

    @property
    def unit(self) -> str:
        return self._unit

    @property
    def accuracy(self) -> float:
        return self._accuracy

    def toValue(self) -> Value:
        """Convert the sensor into a single Value holding a map."""
        return Value({
            "kind":     Value(self._kind),
            "unit":     Value(self._unit),
            "accuracy": Value(self._accuracy),
        })

    @classmethod
    def fromValue(cls, value: Value) -> "Sensor":
        """Create a Sensor from a Value holding a map."""
        raw = value.value
        if not isinstance(raw, dict):
            raise ValueError("The value does not have the structure of a Sensor")

        kind = raw.get("kind")
        unit = raw.get("unit")
        accuracy = raw.get("accuracy")
        if not all(isinstance(x, Value) for x in (kind, unit, accuracy)):
            raise ValueError("The value does not have the structure of a Sensor")

        # Type narrow
        assert isinstance(kind, Value)
        assert isinstance(unit, Value)
        assert isinstance(accuracy, Value)

        acc = accuracy.value
        if not isinstance(acc, (int, float)):
            raise ValueError("The value does not have the structure of a Sensor")

        return cls(str(kind.value), str(unit.value), float(acc))


class DeviceManagement(SampleTreeConvertible):
    """
    A device management object storing device specifications, sensors, and power history.

    This demonstrates:
    - `SampleTreeConvertible` for hierarchical data
    - Map-Values for specifications
    - List-Values for storing multiple sensors
    - History samples for power measurements
    """

    def __init__(self, name: str):
        self._name = name
        self._spec: Value | None = None
        self._sensors: Value | None = None
        self._sensor_list: list[Sensor] = []
        self._history = SampleTree()
        self._power: Value | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def spec(self) -> Value | None:
        return self._spec

    @property
    def sensors(self) -> Value | None:
        return self._sensors

    @property
    def power(self) -> Value | None:
        return self._power

    @property
    def history(self) -> SampleTree:
        return self._history

    def set_spec(self, spec: DeviceSpec) -> None:
        """Set the device specification."""
        self._spec = spec.toValue()
        self._history.childWithValue("spec", self._spec)

    def add_sensor(self, sensor: Sensor) -> None:
        """Add a sensor to the device."""
        self._sensor_list.append(sensor)
        self._sensors = Value([s.toValue() for s in self._sensor_list])
        self._history.childWithValue("sensors", self._sensors)

    def get_sensor(self, index: int) -> Sensor | None:
        """Retrieve a sensor by index from the stored list."""
        if self._sensors is None or not isinstance(self._sensors.value, list):
            return None
        if index < 0 or index >= len(self._sensors.value):
            return None
        sensor_value = self._sensors.value[index]
        assert isinstance(sensor_value, Value)  # type: ignore[unreachable]
        return Sensor.fromValue(sensor_value)

    def sensor_count(self) -> int:
        """Return the number of registered sensors."""
        return len(self._sensor_list)

    def set_power(self, watts: float) -> None:
        """Record a power measurement."""
        self._power = Value(watts)
        self._history.childWithValue("power", self._power)

    def get_latest_power(self) -> float | None:
        """Get the most recent power reading."""
        node = self._history.existingChild("power")
        if node is None or node.newestSample is None:
            return None
        value = node.newestSample.value
        if value is None:
            return None
        power_value = value.value
        if not isinstance(power_value, (int, float)):
            return None
        return float(power_value)

    def toTree(self) -> SampleTree:
        """Convert the device to a SampleTree."""
        tree = SampleTree()
        tree.childWithValue("name", Value(self._name))
        tree.add(self._history, "history")
        return tree

    @classmethod
    def fromTree(cls, tree: SampleTree) -> "DeviceManagement":
        """Reconstruct a DeviceManagement from a SampleTree."""
        name_node = tree.existingChild("name")
        history_node = tree.existingChild("history")

        if name_node is None or history_node is None:
            raise ValueError("The tree does not have the structure of a DeviceManagement")

        name_sample = name_node.newestSample
        if name_sample is None:
            raise ValueError("The tree does not have the structure of a DeviceManagement")

        device = cls(str(name_sample.value.value))
        device._history = history_node

        # Restore attribute values from history
        for attribute in ("spec", "sensors", "power"):
            node = history_node.existingChild(attribute)
            if node is not None and node.newestSample is not None:
                setattr(device, f"_{attribute}", node.newestSample.value)

        # Rebuild sensor list from stored sensors Value
        if device._sensors is not None and isinstance(device._sensors.value, list):
            sensor_list: list[Sensor] = []
            for v in device._sensors.value:
                assert isinstance(v, Value)  # type: ignore[unreachable]
                sensor_list.append(Sensor.fromValue(v))
            device._sensor_list = sensor_list

        return device


def visualize(tree: SampleTree, indent: str = "", max_depth: int = -1, current_depth: int = 0) -> None:
    """
    Display a tree structure with proper formatting.

    Shows:
    - Map values with indented key-value pairs
    - List values with bracket notation
    - Multiple samples with timestamps
    """
    if max_depth >= 0 and current_depth > max_depth:
        return

    for child_name, child in tree.children.items():
        sample = child.newestSample
        value = sample.value if sample is not None else None
        value_display = _format_value(value, indent)

        print(f"{indent}|- {child_name}: {value_display}")

        # Show multiple samples if present
        if len(child.samples) > 1:
            for s in child.samples:
                ts = s.timestamp.timeIntervalSince1970 if s.timestamp else "?"
                marker = "  <- now" if s is child.newestSample else ""
                val = _format_value(s.value, indent + "|  ")
                print(f"{indent}|  |- {val}  (t={ts}){marker}")

        # Recursively show children
        if child.children:
            visualize(child, indent + "|  ", max_depth, current_depth + 1)


def _format_value(value: Value | None, indent: str = "") -> str:
    """Format a Value for display."""
    if value is None:
        return "-"

    raw = value.value

    if isinstance(raw, dict):
        if len(raw) == 0:
            return "{}"
        keys = list(raw.keys())[:3]
        if len(raw) > 3:
            return f"{{{', '.join(keys)}...}}"
        return f"{{{', '.join(keys)}}}"
    elif isinstance(raw, list):
        if len(raw) == 0:
            return "[]"
        return f"[{len(raw)} items]"
    else:
        return str(raw)


def main():
    """Demonstrate the DeviceManagement class."""
    print("=" * 60)
    print("Device Management Example")
    print("=" * 60)

    # Create a device
    device = DeviceManagement("Thermostat Living Room")

    # Set device specification
    print("\nSetting device specification...")
    device.set_spec(DeviceSpec("Ikea Home", "MT-200", "v1.4.2"))
    assert device.spec is not None, "Spec should be set"
    print(f"  Manufacturer: {DeviceSpec.fromValue(device.spec).manufacturer}")

    # Add sensors
    print("\nAdding sensors...")
    device.add_sensor(Sensor("temperature", "C", 0.5))
    device.add_sensor(Sensor("humidity", "%", 2.0))
    device.add_sensor(Sensor("presence", "bool", 0.0))
    print(f"  Added {device.sensor_count()} sensors")

    # Record power measurements (history with multiple samples)
    print("\nRecording power measurements...")
    device.set_power(12.5)
    device.set_power(13.1)
    device.set_power(11.8)
    print(f"  Latest power: {device.get_latest_power()} W")

    # Serialize to tree
    print("\n" + "=" * 60)
    print("=== toTree() - Serialized Device ===")
    tree = device.toTree()
    visualize(tree, max_depth=2)

    # Deserialize from tree
    print("\n" + "=" * 60)
    print("=== fromTree() - Restored Device ===")
    restored = DeviceManagement.fromTree(tree)

    print(f"Name:        {restored.name}")
    print(f"Sensor count: {restored.sensor_count()}")
    print(f"Latest power: {restored.get_latest_power()} W")

    # Show spec
    print("\nDevice Specification:")
    assert restored.spec is not None, "Spec should not be None"
    spec = DeviceSpec.fromValue(restored.spec)
    print(f"  Manufacturer: {spec.manufacturer}")
    print(f"  Model:        {spec.model}")
    print(f"  Firmware:     {spec.firmware}")

    # Show sensors
    print("\nSensors:")
    for i in range(restored.sensor_count()):
        sensor = restored.get_sensor(i)
        if sensor:
            print(f"  [{i}] {sensor.kind}: {sensor.unit} (accuracy: {sensor.accuracy})")



if __name__ == "__main__":
    main()