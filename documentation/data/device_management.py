from soil.data import SampleTree, SampleTreeConvertible, Value, ValueConvertible

class DeviceSpec(ValueConvertible):
    """ A convertible which stores heterogeneous data inside a single Value (a map). """

    def __init__(self, manufacturer: str, model: str, firmware: str):
        self._manufacturer: str = manufacturer
        self._model: str = model
        self._firmware: str = firmware

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
        """ Convert the specification into a single Value holding a map """
        return Value({
            "manufacturer": Value(self._manufacturer),
            "model":       Value(self._model),
            "firmware":    Value(self._firmware),
        })

    @classmethod
    def fromValue(cls, value: Value) -> "DeviceSpec":
        """ Create a specification from a Value holding a map """
        raw = value.value
        if not isinstance(raw, dict):
            raise ValueError("The value does not have the structure of a DeviceSpec")

        manufacturer = raw.get("manufacturer")
        model = raw.get("model")
        firmware = raw.get("firmware")
        if not all(isinstance(x, Value) for x in (manufacturer, model, firmware)):
            raise ValueError("The value does not have the structure of a DeviceSpec")

        return cls(
            str(manufacturer.value),
            str(model.value),
            str(firmware.value),
        )


class Sensor(ValueConvertible):
    """ A single sensor, convertible into a map-Value. """

    def __init__(self, kind: str, unit: str, accuracy: float):
        self._kind: str = kind
        self._unit: str = unit
        self._accuracy: float = accuracy

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
        """ Convert the sensor into a single Value holding a map """
        return Value({
            "kind":     Value(self._kind),
            "unit":     Value(self._unit),
            "accuracy": Value(self._accuracy),
        })

    @classmethod
    def fromValue(cls, value: Value) -> "Sensor":
        """ Create a sensor from a Value holding a map """
        raw = value.value
        if not isinstance(raw, dict):
            raise ValueError("The value does not have the structure of a Sensor")

        kind = raw.get("kind")
        unit = raw.get("unit")
        accuracy = raw.get("accuracy")
        if not all(isinstance(x, Value) for x in (kind, unit, accuracy)):
            raise ValueError("The value does not have the structure of a Sensor")

        acc = accuracy.value
        if not isinstance(acc, (int, float)):
            raise ValueError("The value does not have the structure of a Sensor")

        return cls(str(kind.value), str(unit.value), float(acc))


class DeviceManagement(SampleTreeConvertible):
    """ A structured object which combines maps, lists and samples in one tree. """

    def __init__(self, name: str):
        self._name: str = name
        self._spec: Value | None = None
        self._sensors: Value | None = None
        self._sensor_list: list[Sensor] = list()
        self.history: SampleTree = SampleTree()
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

    def set_spec(self, spec: DeviceSpec):
        """ A complex object becomes a map-Value inside the tree """
        self._spec = spec.toValue()
        self.history.childWithValue("spec", self._spec)

    def add_sensor(self, sensor: Sensor):
        """ Add a sensor object; it is stored as a map-Value inside the list """
        self._sensor_list.append(sensor)
        self._sensors = Value([s.toValue() for s in self._sensor_list])
        self.history.childWithValue("sensors", self._sensors)

    def get_sensor(self, index: int) -> Sensor | None:
        """ Read a sensor back from the stored list-Value """
        if self._sensors is None or not isinstance(self._sensors.value, list):
            return None
        if index >= len(self._sensors.value):
            return None
        return Sensor.fromValue(self._sensors.value[index])

    def set_power(self, watts: float):
        """ A measurement becomes a history sample (auto timestamp) """
        self._power = Value(watts)
        self.history.childWithValue("power", self._power)

    def toTree(self) -> SampleTree:
        """ Convert the device into a SampleTree """
        tree = SampleTree()

        tree.childWithValue("name", Value(self._name))
        tree.add(self.history, "history")

        return tree

    @classmethod
    def fromTree(cls, tree: SampleTree) -> "DeviceManagement":
        """ Create a device from a SampleTree """
        nameNode = tree.existingChild("name")
        historyNode = tree.existingChild("history")

        if nameNode is None or historyNode is None:
            raise ValueError("The tree does not have the structure of a DeviceManagement")

        nameSample = nameNode.newestSample
        if nameSample is None:
            raise ValueError("The tree does not have the structure of a DeviceManagement")

        device = cls(str(nameSample.value.value))
        device.history = historyNode

        for attribute in ("spec", "sensors", "power"):
            node = historyNode.existingChild(attribute)
            if node is not None and node.newestSample is not None:
                setattr(device, f"_{attribute}", node.newestSample.value)

        return device


def visualize(tree: SampleTree, indent: str = "") -> None:
    for cname, child in tree.children.items():
        sample = child.newestSample
        value = sample.value.value if sample is not None else "–"

        if isinstance(value, dict):
            print(f"{indent}├─ {cname}: {{")
            for key, item in value.items():
                inner = item.value if isinstance(item, Value) else item
                print(f"{indent}│  ├─ {key}: {inner}")
            print(f"{indent}│  }}")
        elif isinstance(value, list):
            print(f"{indent}├─ {cname}: [")
            for item in value:
                if isinstance(item, Value) and isinstance(item.value, dict):
                    inner = ", ".join(
                        f"{k}={v.value if isinstance(v, Value) else v}"
                        for k, v in item.value.items()
                    )
                    print(f"{indent}│  ├─ Sensor({inner})")
                else:
                    print(f"{indent}│  ├─ {item.value if isinstance(item, Value) else item}")
            print(f"{indent}│  ]")
        elif len(child.samples) > 1:
            print(f"{indent}├─ {cname}: ({len(child.samples)} Samples)")
            for s in child.samples:
                ts = s.timestamp.timeIntervalSince1970 if s.timestamp is not None else "?"
                marker = "  ← now" if s is child.newestSample else ""
                print(f"{indent}│  ├─ {s.value.value}  (t={ts}){marker}")
        else:
            print(f"{indent}├─ {cname}: {value}")

        visualize(child, indent + "│  ")


def main():
    device = DeviceManagement("Thermostat Living Room")

    device.set_spec(DeviceSpec("Ikea Home", "MT-200", "v1.4.2"))

    device.add_sensor(Sensor("temperature", "°C", 0.5))
    device.add_sensor(Sensor("humidity", "%", 2.0))
    device.add_sensor(Sensor("presence", "bool", 0.0))

    device.set_power(12.5)
    device.set_power(13.1)

    tree = device.toTree()
    print("=== toTree() ===")
    visualize(tree) # only for visualization purposes -> see below

    restored = DeviceManagement.fromTree(tree)
    print("\n=== fromTree() ===")
    print(f"name  = {restored.name}")
    print(f"power = {restored.power.value:.2f}")

    spec = DeviceSpec.fromValue(restored.spec)
    print(f"spec  = {spec.manufacturer} {spec.model} ({spec.firmware})")

    assert restored.name == device.name

    power = restored.power
    assert power is not None and power.value is not None

    assert restored.spec is not None
    spec2 = DeviceSpec.fromValue(restored.spec)
    assert spec2.manufacturer == "Ikea Home"
    assert spec2.model == "MT-200"
    assert spec2.firmware == "v1.4.2"

    sensors = restored.sensors
    assert sensors is not None
    assert isinstance(sensors.value, list)
    assert len(sensors.value) == 3

    sensor = restored.get_sensor(0)
    assert sensor is not None
    assert sensor.kind == "temperature"
    assert sensor.unit == "°C"

    sensor2 = restored.get_sensor(1)
    assert sensor2 is not None
    assert sensor2.kind == "humidity"

    assert restored.history is tree.existingChild("history")

if __name__ == "__main__":
    main()