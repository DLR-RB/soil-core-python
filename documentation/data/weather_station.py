from soil.data import SampleTree, SampleTreeConvertible, Value


class WeatherStation(SampleTreeConvertible):
    
    def __init__(self, name: str, location: SampleTree):
        self._name: str = name
        self._temperature: Value | None = None
        self._humidity: Value | None = None
        self._location: SampleTree = location
        self.history: SampleTree = SampleTree()

    @property
    def name(self) -> str:
        return self._name

    @property
    def temperature(self) -> Value | None:
        return self._temperature

    @property
    def humidity(self) -> Value | None:
        return self._humidity

    @property
    def location(self) -> SampleTree | None:
        return self._location

    def set_temperature(self, value: Value):
        self._temperature = value
        self.history.childWithValue("temperature", value)

    def set_humidity(self, value: Value):
        self._humidity = value
        self.history.childWithValue("humidity", value)

    def toTree(self) -> SampleTree:
        """ Convert the station into a SampleTree """
        tree = SampleTree()

        tree.childWithValue("name", Value(self._name))

        tree.add(self._location, "location")
        tree.add(self.history, "history")

        return tree

    @classmethod
    def fromTree(cls, tree: SampleTree) -> "WeatherStation":
        """ Create a station from a SampleTree """
        nameNode = tree.existingChild("name")
        locationNode = tree.existingChild("location")
        historyNode = tree.existingChild("history")

        if nameNode is None or locationNode is None or historyNode is None:
            raise ValueError("The tree does not have the structure of a WeatherStation")

        nameSample = nameNode.newestSample
        if nameSample is None:
            raise ValueError("The tree does not have the structure of a WeatherStation")
        
        name = str(nameSample.value.value)

        station = cls(name, locationNode)
        station.history = historyNode

        temperatureNode = historyNode.existingChild("temperature")
        if temperatureNode is not None and temperatureNode.newestSample is not None:
            station._temperature = temperatureNode.newestSample.value

        humidityNode = historyNode.existingChild("humidity")
        if humidityNode is not None and humidityNode.newestSample is not None:
            station._humidity = humidityNode.newestSample.value

        return station


def visualize(tree: SampleTree, indent: str = "") -> None:
    for cname, child in tree.children.items():
        sample = child.newestSample
        value = sample.value.value if sample is not None else "–"
        print(f"{indent}├─ {cname}: {value}")

        if len(child.samples) > 1:
            for s in child.samples:
                ts = s.timestamp.timeIntervalSince1970 if s.timestamp is not None else "?"
                marker = "  ← now" if s is child.newestSample else ""
                print(f"{indent}│  ├─ {s.value.value}  (t={ts}){marker}")

        visualize(child, indent + "│  ")


def main():

    location = SampleTree()
    location.childWithValue("city", Value("Berlin"))
    location.childWithValue("lat", Value(52.52))
    location.childWithValue("lon", Value(13.405))

    station = WeatherStation("Station-01", location)
    station.set_temperature(Value(21.5))
    station.set_humidity(Value(63))
    station.set_temperature(Value(23.8))

    tree = station.toTree()
    print("=== toTree() ===")
    visualize(tree)

    restored = WeatherStation.fromTree(tree)
    print("\n=== fromTree() ===")
    print(f"name        = {restored.name}")
    print(f"temperature = {float(restored.temperature.value):.2f}")
    print(f"humidity    = {restored.humidity}")

    assert restored.name == station.name

    temperature = restored.temperature
    assert temperature is not None and temperature.value is not None
    assert float(temperature.value) == 23.8

    humidity = restored.humidity
    assert humidity is not None and humidity.value is not None
    assert float(humidity.value) == 63

    assert restored.history is tree.existingChild("history")


if __name__ == "__main__":
    main()