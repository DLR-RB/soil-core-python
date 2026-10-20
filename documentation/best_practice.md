# Best Practice

The following document provides best practice examples for using the `SOIL-CORE-PYTHON` library.


## 1. Introduction

...

## 2. SOIL-CORE

### 2.1. Data handling

The `soil.data` package provides the fundamental data types of `SOIL`. They all work together according to one principle:

**SampleTree** is a hierarchical, time-indexed store. Each node can hold **Samples** (which consist of **Values** with a **Timestamp**) and named child nodes.

```python
SampleTree (node "station")
├─ name: Sample(Value("Station-01"))
├─ history
│  ├─ temperature: Sample(21.5, t₁), Sample(23.8, t₂)   ← multiple samples = history
│  └─ humidity:    Sample(63, t₃)
```

#### 2.1.1 Value & Convertibles

`Value` is the universal container for a single piece of data. It can hold simple types (`int`, `str`, `float`, `bytes`) as well as complex types (`Path`, `list[Value]`, `dict[str, Value]`).

```python
value = Value(42)
value = Value("Berlin")
value = Value([Value("temperature"), Value("humidity")])
value = Value({"city": Value("Berlin"), "lat": Value(52.52)})

value = Value(52.52)

value.type          # ValueType.DOUBLE
value.value         # 52.52 (the raw wrapped value)
value.doubleValue   # 52.52
value.stringValue   # None (not a string)
value.isNull        # False

location = Value({"city": Value("Berlin"), "lat": Value(52.52)})
location["city"]            # -> Value("Berlin")
"name" in location          # -> False
list(location)              # -> ["city", "lat"]
```

`Convertibles` are there to bridge between your own classes and these containers, `SOIL` needs two types:

- `ValueConvertible`: convert a type from and to a single `Value`. Implement `toValue()` and `fromValue()`.
- `SampleTreeConvertible`: convert a type from and to a `SampleTree`. Implement `toTree()` and `fromTree()`.

The methods are implemented on your own class. `Value` itself implements `ValueConvertible` (`toValue()` returns the value itself, `fromValue()` validates the argument):

```python
class Temperature(ValueConvertible):
    """ One object <-> one Value """

    def __init__(self, celsius: float):
        self.celsius = celsius

    def toValue(self) -> Value:
        return Value(self.celsius)

    @classmethod
    def fromValue(cls, value: Value) -> "Temperature":
        return cls(float(value.value))


class WeatherLog(SampleTreeConvertible):
    """ One object <-> one SampleTree (uses Temperature as a Value) """

    def __init__(self, station: str):
        self.station = station
        self.history = SampleTree()

    def record(self, temperature: Temperature):
        self.history.childWithValue("temperature", temperature.toValue()) 

    def toTree(self) -> SampleTree:
        tree = SampleTree()
        tree.childWithValue("station", Value(self.station))
        tree.add(self.history, "history")
        return tree

    @classmethod
    def fromTree(cls, tree: SampleTree) -> "WeatherLog":
        log = cls(str(tree.existingChild("station").newestSample.value.value))
        log.history = tree.existingChild("history")
        return log

log = WeatherLog("Station-01")               # create a SampleTreeConvertible object
log.record(Temperature(23.8))                # ValueConvertible: Temperature -> Value -> history sample

tree = log.toTree()                          # convert the whole log into a SampleTree
restored = WeatherLog.fromTree(tree)         # and back into a WeatherLog object
```



#### 2.1.2 Sample & Timestamp

A `Sample` is a `Value` together with a `Timestamp`. Often samples are created implicitly: `childWithValue(name, value)` automatically attaches `Timestamp.current()`.

```python
sample = Sample(Value(23.8), Timestamp.current())
sample.value
sample.timestamp
```

A `Timestamp` represents a point in time (seconds since 1970, similar to a UTC `datetime`).`

```python
now = Timestamp.current()

specific = Timestamp(2026, 10, 9, 16, 10, 45)
seconds = specific.timeIntervalSince1970
```

#### 2.1.3 SampleTree

A `SampleTree` is a tree of nodes. Each node holds a list of `Samples` and named children.

```python
from soil.data import SampleTree

tree = SampleTree()

tree.childWithValue("city", Value("Berlin"))     # write a sample (current timestamp)
child = tree.child("history")                    # get or create a child node
tree.add(subtree, "location")                    # attach an existing tree as child (replaces)
tree.merge(other_tree)                           # merge samples & children in (appends)

tree.children                                    # dict[str, SampleTree]
node = tree.existingChild("city")                # child or None
node.newestSample                                # latest sample (even if in the future)
node.currentSample                               # latest sample NOT in the future
node.samples                                     # all samples (sorted history)

tree.isEmpty                                     # no samples anywhere?
tree.totalNumberOfSamples                        # count across the subtree
print(tree)                                      # built-in multi-line description
```                                  

#### 2.1.4 Path

A `Path` is an array of strings identifying a state, input or output inside a tree. Each component addresses one level of the tree. Paths are used for navigation and for read/write/delete operations on specific nodes.

```python
from soil.data import Path

path = Path.of("history", "temperature")   # ["history", "temperature"]
path = Path(["history", "temperature"])    # equivalent construction

print(path)                                # "history > temperature"
path.size                                  # 2
path.isEmpty                               # False

longer = path.appending("max")             # ["history", "temperature", "max"]
prefix = Path.of("history")

path.hasPrefix(prefix)                     # True
path.removingPrefix(prefix)                # ["temperature"]
Path.of("a", "b").commonPrefix(Path.of("a", "c"))   # ["a"]

node = tree.existingNode(path)             # node at the path, or None
node = tree.findOrCreateNode(path)         # node at the path, created if missing
tree.insert(samples, path)                 # insert samples at the path
tree.mergeAtPath(subtree, path)            # merge a tree in at the path
```


#### 2.1.5 Best Practices for Data handling

##### 2.1.5.1 Weather Station

```python
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
    visualize(tree) # only for visualization purposes -> see below


    restored = WeatherStation.fromTree(tree)
    print("\n=== fromTree() ===")
    print(f"name        = {restored.name}")
    print(f"temperature = {float(restored.temperature.value):.1f}")
    print(f"humidity    = {restored.humidity}")

    assert restored.name == station.name

    temperature = restored.temperature
    assert temperature is not None and temperature.value is not None
    assert float(temperature.value) == 23.8

    humidity = restored.humidity
    assert humidity is not None and humidity.value is not None
    assert float(humidity.value) == 63

    assert restored.history is tree.existingChild("history")

#--Output--#
"""
=== toTree() ===
├─ name: Station-01
├─ location: –
│  ├─ city: Berlin
│  ├─ lat: 52.52
│  ├─ lon: 13.405
├─ history: –
│  ├─ temperature: 23.8
│  │  ├─ 21.5  (t=1791786478.282746)
│  │  ├─ 23.8  (t=1791786478.282751)  ← now
│  ├─ humidity: 63

=== fromTree() ===
name        = Station-01
temperature = 23.8
humidity    = 63
"""
```

##### 2.1.5.2 Library with Books

```python
from soil.data import SampleTree, SampleTreeConvertible, Value, ValueConvertible


class Book(ValueConvertible):
    """ An object which is convertible into a single value. """

    def __init__(self, isbn: str, title: str, author: str):
        self._isbn: str = isbn
        self._title: str = title
        self._author: str = author

    @property
    def isbn(self) -> str:
        return self._isbn

    @property
    def title(self) -> str:
        return self._title

    @property
    def author(self) -> str:
        return self._author

    def toValue(self) -> Value:
        """ Convert the book into a single Value """
        return Value(f"{self._isbn}|{self._title}|{self._author}")

    @classmethod
    def fromValue(cls, value: Value) -> "Book":
        """ Create a book from a single Value """
        raw = value.value
        if not isinstance(raw, str):
            raise ValueError("The value does not have the structure of a Book")

        parts = raw.split("|")
        if len(parts) != 3:
            raise ValueError("The value does not have the structure of a Book")

        isbn, title, author = parts
        return cls(isbn, title, author)


class Library(SampleTreeConvertible):
    """ A structured object which stores the books in a SampleTree. """

    def __init__(self, name: str):
        self._name: str = name
        self._books: SampleTree = SampleTree()
        self.history: SampleTree = SampleTree()
        self._visitor_count: Value | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def books(self) -> SampleTree:
        return self._books

    @property
    def visitor_count(self) -> Value | None:
        return self._visitor_count

    def add_book(self, book: Book):
        book_value = book.toValue()
        self._books.childWithValue(book.isbn, book_value)

    def set_visitor_count(self, value: Value):
        self._visitor_count = value
        self.history.childWithValue("visitor_count", value)

    def toTree(self) -> SampleTree:
        """ Convert the library into a SampleTree """
        tree = SampleTree()

        tree.childWithValue("name", Value(self._name))

        tree.add(self._books, "books")
        tree.add(self.history, "history")

        return tree

    @classmethod
    def fromTree(cls, tree: SampleTree) -> "Library":
        """ Create a library from a SampleTree """
        nameNode = tree.existingChild("name")
        booksNode = tree.existingChild("books")
        historyNode = tree.existingChild("history")

        if nameNode is None or booksNode is None or historyNode is None:
            raise ValueError("The tree does not have the structure of a Library")

        nameSample = nameNode.newestSample
        if nameSample is None:
            raise ValueError("The tree does not have the structure of a Library")

        name = str(nameSample.value.value)

        library = cls(name)
        library._books = booksNode
        library.history = historyNode

        visitorNode = historyNode.existingChild("visitor_count")
        if visitorNode is not None and visitorNode.newestSample is not None:
            library._visitor_count = visitorNode.newestSample.value

        return library

    def get_book(self, isbn: str) -> Book | None:
        bookNode = self._books.existingChild(isbn)
        if bookNode is None or bookNode.newestSample is None:
            return None
        return Book.fromValue(bookNode.newestSample.value)

def main():
    library = Library("Münchner Stadtbibliothek")

    library.add_book(Book("978-3-16-148410-0", "Der Prozess", "Franz Kafka"))
    library.add_book(Book("978-3-499-13550-2", "Der Alchimist", "Paulo Coelho"))
    library.add_book(Book("978-3-15-009958-4", "Faust I", "Johann W. Goethe"))

    library.set_visitor_count(Value(1200))
    library.set_visitor_count(Value(1350))

    tree = library.toTree()
    print("=== toTree() ===")
    visualize(tree) # only for visualization purposes -> see below

    restored = Library.fromTree(tree)
    print("\n=== fromTree() ===")
    print(f"name          = {restored.name}")
    print(f"visitor_count = {restored.visitor_count}")

    book = restored.get_book("978-3-16-148410-0")
    print(f"book          = {book.title} von {book.author} ({book.isbn})")

    assert restored.name == library.name

    visitors = restored.visitor_count
    assert visitors is not None and visitors.value is not None

    assert book is not None
    assert book.title == "Der Prozess"
    assert book.author == "Franz Kafka"

    assert restored.history is tree.existingChild("history")

#--Output--#
"""
=== toTree() ===
├─ name: Münchner Stadtbibliothek
├─ books: –
│  ├─ 978-3-16-148410-0: 978-3-16-148410-0|Der Prozess|Franz Kafka
│  ├─ 978-3-499-13550-2: 978-3-499-13550-2|Der Alchimist|Paulo Coelho
│  ├─ 978-3-15-009958-4: 978-3-15-009958-4|Faust I|Johann W. Goethe
├─ history: –
│  ├─ visitor_count: (2 Samples)
│  │  ├─ 1200  (t=1791786222.003431)
│  │  ├─ 1350  (t=1791786222.003434)  ← now

=== fromTree() ===
name          = Münchner Stadtbibliothek
visitor_count = 1350
book          = Der Prozess von Franz Kafka (978-3-16-148410-0)
"""
```

##### 2.1.5.3 Device Management

```python
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
            raise ValueError("The tree does not have the structure of DeviceManagement")

        nameSample = nameNode.newestSample
        if nameSample is None:
            raise ValueError("The tree does not have the structure of DeviceManagement")

        device = cls(str(nameSample.value.value))
        device.history = historyNode

        for attribute in ("spec", "sensors", "power"):
            node = historyNode.existingChild(attribute)
            if node is not None and node.newestSample is not None:
                setattr(device, f"_{attribute}", node.newestSample.value)

        return device


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

#--Output--#
"""
=== toTree() ===
├─ name: Thermostat Living Room
├─ history: –
│  ├─ spec: {
│  │  ├─ manufacturer: Ikea Home
│  │  ├─ model: MT-200
│  │  ├─ firmware: v1.4.2
│  │  }
│  ├─ sensors: [
│  │  ├─ Sensor(kind=temperature, unit=°C, accuracy=0.5)
│  │  ├─ Sensor(kind=humidity, unit=%, accuracy=2.0)
│  │  ├─ Sensor(kind=presence, unit=bool, accuracy=0.0)
│  │  ]
│  ├─ power: (2 Samples)
│  │  ├─ 12.5  (t=1791788839.263524)
│  │  ├─ 13.1  (t=1791788839.263526)  ← now

=== fromTree() ===
name  = Thermostat Living Room
power = 13.10
spec  = Ikea Home MT-200 (v1.4.2)
"""
```

##### 2.1.5.4 Visualizer

These are not needed for fuctionality but are nice to have for debugging or visualization purposes.
`SOIL-CORE-PYTHON` also delivers a built-in unctionality with the normal `print()`-Statement which which shows all samples per node with formatted timestamps, but is less compact and does not render maps and lists structurally.
An example for a simple SampleTree-Visualizer (used in 3.1 & 3.2) is shown below:

```python
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
```

Another more complex visualizer (used in 3.3) which also uses SampleTree is specialized on the specific task.

```python
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
```

Depending on the implementation there a different need and fucntions which each visualizer has to achieve.

Comparison between visualizer and normal print:

##### visualize(tree)
```python
├─ name: Thermostat Living Room
├─ history: –
│  ├─ spec: {
│  │  ├─ manufacturer: Ikea Home
│  │  ├─ model: MT-200
│  │  ├─ firmware: v1.4.2
│  │  }
│  ├─ sensors: [
│  │  ├─ Sensor(kind=temperature, unit=°C, accuracy=0.5)
│  │  ├─ Sensor(kind=humidity, unit=%, accuracy=2.0)
│  │  ├─ Sensor(kind=presence, unit=bool, accuracy=0.0)
│  │  ]
│  ├─ power: (2 Samples)
│  │  ├─ 12.5  (t=1791790210.661743)
│  │  ├─ 13.1  (t=1791790210.661747)  ← now
```
##### print(tree)
```python
children:
  name:
    samples:
      `Thermostat Living Room` (12.10.2026 07:30:10)
  history:
    children:
      spec:
        samples:
          manufacturer = `Ikea Home`, model = `MT-200`, firmware = `v1.4.2` (12.10.2026 07:30:10)
      sensors:
        samples:
          kind = `temperature`, unit = `°C`, accuracy = 0.5 (12.10.2026 07:30:10)
          kind = `temperature`, unit = `°C`, accuracy = 0.5, kind = `humidity`, unit = `%`, accuracy = 2.0 (12.10.2026 07:30:10)
          kind = `temperature`, unit = `°C`, accuracy = 0.5, kind = `humidity`, unit = `%`, accuracy = 2.0, kind = `presence`, unit = `bool`, accuracy = 0.0 (12.10.2026 07:30:10)
      power:
        samples:
          12.5 (12.10.2026 07:30:10)
          13.0999999999999996 (12.10.2026 07:30:10)
```



### 2.2. Messaging

Components in SOIL exchange data via **Messages**. A single `Message` class covers all message types (data, requests, deletions, subscriptions) through optional fields – the `type` field determines how the other fields are interpreted.

#### 2.2.1 Message Structure

The `MessageType` enum defines the kind of a message used to exchange data between components:

```python
from enum import StrEnum


class MessageType(StrEnum):
    """The type of a message used to exchange data between components."""

    # A message containing one or more samples
    DATA = "data"

    # A request to receive data
    REQUEST = "read"

    # A request to delete data
    DELETION = "delete"

    # A request to include a path in a subscription
    SUBSCRIPTION_INCLUSION = "include"

    # A request to exclude a path in a subscription
    SUBSCRIPTION_EXCLUSION = "exclude"

    # A request to delete a subscription
    SUBSCRIPTION_DELETION = "clear"
```

A `Message` is an immutable dataclass. All types share the same structure – the optional fields are interpreted depending on the message type:
   Field | Type | Usage |
 |---|---|---|
 | `type` | `MessageType` | The message type (defaults to `DATA`) |
 | `path` | `Path` | *Data message:* path of the samples or *Request:* the requested path or *Subscription:* the path to include/exclude/delete |
 | `data` | `SampleTree` | *Data message:* the tree associated with the path |
 | `count` | `int \| None` | *Data message:* total number of response messages or *Request:* maximum number of samples |
 | `depth` | `int \| None` | *Request:* maximum depth or *Subscription:* depth of the inclusion/exclusion |
 | `time` | `Timestamp \| None` | *Request:* exclusive start date (`None` = beginning of time) |
 | `end` | `Timestamp \| None` | *Request:* inclusive end date (`None` = end of time) |
 | `id` | `int \| None` | *Request/subscription identifier* or *Data message:* the request this message corresponds to |

```python
from soil.message import Message, MessageType

message = Message(
    type=MessageType.DATA,
    path=Path.of("history", "temperature"),
    data=SampleTree.ofValue(Value(21.5)),
)
```

#### 2.2.2 Creating Messages

`Message` provides factory methods for each message type. Prefer them over manual construction – they set the correct `MessageType` automatically:

```python
from soil.message import Message
from soil.data import Path, Sample, SampleTree, Timestamp, Value

# -- Data messages --
Message.value(Value(21.5), Path.of("history", "temperature"))
# a single sample (timestamp defaults to now)

samples = [Sample(Value(1)), Sample(Value(2))]
Message.samples(samples, Path.of("history", "temperature"))
# a list of samples

tree = library.toTree()
Message.tree(tree, Path.of("library"))
# a complete SampleTree, e.g. from a SampleTreeConvertible -> example Library

Message.acknowledge(request=1, path=Path.of("history", "temperature"))
# an empty data message acknowledging a request

# -- History request --
Message.request(
    Path.of("history", "temperature"),
    start=Timestamp.current(),   # exclusive start (None = beginning of time)
    end=None,                    # inclusive end (None = end of time)
    limit=100,                   # maximum number of samples
    depth=1,                     # levels below the path to include
    id=42,                       # identifier to match the response
)

# -- Deletion request --
Message.delete(Path.of("history", "temperature"), depth=None)

# -- Subscription rules --
Message.include(Path.of("device"), depth=2)      # subscribe to a path with depth=2
Message.exclude(Path.of("device", "power"))      # exclude a sub-path
Message.deleteRules(Path.of("device"))           # remove all rules for a path
```


#### 2.2.3 Message Transmission & Connection

Messages are exchanged over a transport layer through four building blocks:

```
Message  ──encode──>  msg_encoded  ──FrameConnection──>  msg_encoded  ──decode──>  Message
```

**`MessageEncoding`** is the abstract interface for encoding algorithms. It defines the two directions of the conversion between messages and transport data:

- `encode(message)` – convert a message into encoded data for transmission
- `decode(data)` – extract a message from encoded data

Currently there are 3 supported encoding types in SOIL-CORE-PYTHON:
- `BINARY`: Messages are serialized into a fixed byte structure, which makes it the most efficient encoding regarding size and encoding speed.
- `JSON`: Is a readable JSON representation of the message fields. The content of a transmitted message remains human-readable and easily inspectable with any standard tool.
- `COMPACT JSON`: A compact JSON variant with a minimized footprint.
There is also an optional library for `Protobuf` support. 

All encodings implement the same `MessageEncoding` interface, making them fully interchangeable – an encoding can be replaced at any time without any changes to the surrounding components.

**`MessageDistributor`** is implemented by every component that transmits messages without being prompted. It defines who receives the messages the component produces:

- `setReceiver(receiver)`: sets the receiver
- `getReceiver()`: gets the currently set receiver, if any

**`MessageReceiver`** is the counterpart to the distributor: a component that accepts incoming messages via `acceptMessage(message)`.

**`MessageConnection`** is the connection interface of a component. It combines the `Receiver`, `MessageDistributor` and `Connection` interfaces and adds its central method:

- `send(message)`: sends a message; returns a request handle that can be awaited until the message is *transmitted*.

Because `MessageConnection` also implements the `Receiver` interface, it accepts plain sample data as well: `accept(tree, path)` wraps any `SampleTree` into a data message (`Message.tree`) and sends it. A message connection can therefore be used wherever a `Receiver` is expected.

**`DecodedConnection`** is the standard implementation that combines all building blocks above. It wraps a binary `FrameConnection` with a `MessageEncoding` and turns it into a ready-to-use message connection:

- `DecodedConnection.create(connection, encoding)`: creates and initializes the connection 
- Incoming frames are decoded and forwarded to the receiver set via `setReceiver()`
- Frames arriving before a receiver is set are buffered and delivered once a receiver is available
- `shutdown()`: closes the encoding and the underlying connection
 

#### 2.2.4 Best Practices for Messaging

##### 2.2.4.1 WeatherHub

```python
from soil.data import Path, SampleTree, Timestamp, Value
from soil.message import Message, MessageType


class WeatherHub:
    """ A component that receives messages, stores data and answers requests. """

    def __init__(self):
        self.data: SampleTree = SampleTree()
        self.subscriptions: list[Path] = list()
        self.outbox: list[Message] = list()


    def acceptMessage(self, message: Message) -> None:
        """ Process an incoming message. """
        match message.type:

            case MessageType.DATA:
                self.data.mergeAtPath(message.data, message.path)

                if message.id is not None:
                    self.outbox.append(
                        Message.acknowledge(request=message.id, path=message.path)
                    )

            case MessageType.REQUEST:
                node = self.data.existingNode(message.path)
                if node is not None:
                    samples = node.getSamples(message.time, message.end, message.count)
                else:
                    samples = list()

                self.outbox.append(
                    Message.samples(samples, message.path, request=message.id, totalMessages=1)
                )

            case MessageType.DELETION:
                node = self.data.existingNode(message.path)
                if node is not None:
                    node.deleteSamples(message.time, message.end)

            case MessageType.SUBSCRIPTION_INCLUSION:
                self.subscriptions.append(message.path)

            case MessageType.SUBSCRIPTION_EXCLUSION:
                self.subscriptions = [p for p in self.subscriptions if not p.hasPrefix(message.path)]

            case MessageType.SUBSCRIPTION_DELETION:
                self.subscriptions = [p for p in self.subscriptions if not p.hasPrefix(message.path)]


def main():
    hub = WeatherHub()

    hub.acceptMessage(Message.value(Value(21.5), Path.of("weather", "temperature")))
    hub.acceptMessage(Message.value(Value(23.8), Path.of("weather", "temperature")))

    station = SampleTree()
    station.childWithValue("humidity", Value(63))
    hub.acceptMessage(Message.tree(station, Path.of("weather"), request=42))

    hub.acceptMessage(Message.request(Path.of("weather", "temperature"), id=1, limit=10))

    hub.acceptMessage(Message.include(Path.of("weather")))
    hub.acceptMessage(Message.exclude(Path.of("weather", "humidity")))
    hub.acceptMessage(Message.deleteRules(Path.of("weather")))

    print("=== Stored data ===")
    print(hub.data)

    print("=== Outbox ===")
    for message in hub.outbox:
        print(message, end="\n---\n")

#--Output--#
=== Stored data ===
children:
  weather:
    children:
      temperature:
        samples:
          21.5 (now)
          23.8000000000000007 (now)
      humidity:
        samples:
          63 (12.10.2026 09:30:40)

=== Outbox ===
type: data
path: weather
id: 42
---
type: data
path: weather > temperature
count: 1
id: 1
data:
  samples:
    21.5 (now)
    23.8000000000000007 (now)
---
```
##### 2.2.4.1 Connection with PrintReceiver

```python

class LoopbackConnection(MessageConnection):
    """ A minimal in-memory connection: sent messages go directly to the receiver. """

    def __init__(self):
        self._receiver: MessageReceiver | None = None

    async def send(self, message: Message) -> None:
        if self._receiver is not None:
            await self._receiver.acceptMessage(message)

    async def setReceiver(self, receiver: MessageReceiver | None) -> None:
        self._receiver = receiver

    async def getReceiver(self) -> MessageReceiver | None:
        return self._receiver


class PrintReceiver:
    """ A minimal receiver: prints every incoming message. """

    async def acceptMessage(self, message: Message) -> None:
        print(f"received: {message.type} for {message.path}")

def main():
    connection = LoopbackConnection()

    await connection.setReceiver(PrintReceiver())
    receiver = await connection.getReceiver()

    await connection.send(
        Message.value(Value(21.5), Path.of("weather", "temperature"))
    )

    await connection.accept(
        SampleTree.ofValue(Value(63)), Path.of("weather", "humidity")
    )

#--Output--#
received: MessageType.DATA for weather > temperature
received: MessageType.DATA for weather > humidity
```


### 2.3. Transport Stack

Section 2.2 described how a single message is structured and passed to a connection. This section covers the full transport stack: how messages are framed, encoded and carried over a physical connection.

Each layer has a single responsibility and a narrow interface, so the layers can be combined and exchanged freely:
```
Application             your component / a SOIL storage device
    │  
    │  accept(tree, path) / send(message)
    │
Message layer           MessageEncoding.encode / decode
    │  
    │  encoded bytes
    │
Framing                 adds message boundaries to the byte stream
    │  
    │  frames
    │
Transport               a raw byte stream (e.g. a TCP socket)
```

### 2.3.0 Synchronous and Asynchronous Usage

SOIL is built on Python's `asyncio`. The data model (2.1) is mostly synchronous — but as soon as components exchange data (2.2) or connections come into play (2.3), asynchronous execution becomes the norm. This section explains the model once, so the rest of the chapter can use it freely.

**Event loop and tasks.** A SOIL application runs an event loop (`asyncio.run(main())`). Concurrent work happens in tasks; SOIL components are Actors — each one processes its work in its own background task, created in its constructor. Two consequences:

- Actors (framing, connections, storages, …) must be constructed where a loop is running — inside `async def` code (e.g. your `connect()`), never in synchronous constructors.
- Accessing an Actor after it was shut down raises `ActorClosedError`.


**Two flavors of methods.**

```python
client = TcpSocketClient(host, port)     # synchronous: stores host/port, no I/O yet
stream = await client.connect()          # asynchronous: waits for the TCP handshake

socket = UdpSocket(localPort)            # spawns a task -> needs a running loop
conn   = socket.connect(host, port)      # synchronous: UDP has no handshake to wait for
```

The pattern is consistent: setup that can succeed immediately is synchronous; setup that has to wait for the outside world is `async`.

**Requests — awaiting is opt-in.** Operations that hand data over (e.g. `send()`) do not block your code: they return a request handle you may either ignore or await:

```python
connection.send(message)         # fire and forget — transmission happens in the background
await connection.send(message)  # continue once the message was transmitted
```

Awaiting a transmission means the message was handed to the transport, **not** that the peer received it.

**Failures: `await` vs `.wait()`.**  

A request handle can be consumed in two ways with different consequences:

- `await request` — re-raises the exception if the operation failed.
- `request.wait()` — swallows the exception and simply returns.

Prefer plain `await` unless you deliberately ignore failures — `wait()` turns errors into silence.

**Back-to-back operations.** 

Multiple sends in a row without an `await` in between can lose the second message **and** jam the component so that even incoming data is no longer processed. Yield between rapid consecutive operations:

```python
param.set(1.0)
await asyncio.sleep(0)   # yield to the event loop
param.set(2.0)
```


#### 2.3.1 Framing

A TCP connection is a raw byte stream. It carries no information about where one message ends and the next one begins — if a component sends two messages back to back, the peer cannot split them apart. Framing adds these boundaries: it wraps a raw stream connection into a ``FrameConnection`` whose units are complete, self-delimiting frames.

``SyncByteLengthFraming``  is SOIL's synchronous framing algorithm. Each frame is prefixed with a configurable sync sequence (default 0xAA 0x55) followed by a 2-byte big-endian length field, so the receiver can extract frames of arbitrary size from the stream without ambiguity. The maximum payload is 65,535 bytes (the largest value that fits the length field); a larger payload raises a ``FramingError`` on encoding.

Framing is defined by the StreamFraming interface — two async directions:
- ``encodeForStream(message: bytes) -> bytes`` — add framing information to an encoded message
- ``processStreamBytes(data: bytes) -> list[bytes]`` — extract every complete frame from newly received stream bytes; incomplete frames stay in an internal ring buffer until the rest arrives


````
framing = SyncByteLengthFraming(
    syncBytes=b"\xAA\x55",       # identifies the start of each frame
    maxPayloadLength=65_535,     # 0 < length <= 65,535
)
````


#### 2.3.2 Choosing an Encoding

All encodings implement the same `MessageEncoding` interface (see 2.2.3) and are therefore interchangeable — switching never touches the surrounding components.
   Encoding | Size / Speed | Human-Readability | Recommended for |
 |---|---|---|---|
 | `BINARY` | best | none | production, high message rates |
 | `JSON` | larger / slower | fully human-readable | development & debugging |
 | `COMPACT JSON` | in between | reduced | JSON with a minimized footprint |
 | `Protobuf` (optional library) | compact | none | schema-driven integrations |

Both sides of a connection **must** use the same encoding.

**Recommendation:** develop and debug with `JSON` — you can inspect live frames with any standard tool, which makes wire-level problems immediately visible. Switch to `BINARY` when message size or encoding speed matter; it is a one-line change at stack construction.

If you are interested in a performance-comparison of these, have a look at the SOIL-PERFORMANCE-PYTHON Repository.


#### 2.3.3 Network Protocols (TCP, UDP, WebSocket)
The bottom layer of the stack is the network transport. SOIL provides interfaces for the common protocols — TCP, UDP and WebSocket. All of them sit behind the same connection interface, so the layers above (encoding, message layer) remain unchanged. What differs per protocol is whether framing is needed and which lifecycle guarantees exist.

**TCP — reliable, ordered byte stream.**

- Guaranteed delivery and ordering; connection-oriented lifecycle (connect, EOF, shutdown).
- The stream carries no message boundaries → framing is required (2.3.1).
- The default choice for request/response traffic and whenever every single message matters. 

**UDP — connectionless datagrams.**

- Each datagram is self-delimiting → no framing needed; one datagram = one frame.
- No delivery guarantee, no ordering, no connection lifecycle — a dead peer is simply silent (there is no EOF).
- Well suited for high-rate telemetry where the newest value matters and occasional loss is acceptable.
- Datagram size is bounded (practical MTU limit ≈ 1.4 kB) — keep individual messages small. Note (source): incoming datagrams are silently truncated to the socket's maximumPayloadLength — choose that limit deliberately.
- UdpSocket covers both roles (UDP has no client/server distinction): connect(host, port) is synchronous and sends nothing — no handshake exists — while onConnection(consumer) receives incoming remotes. There is one connection per remote address.
- Like the Actors above, UdpSocket(...) spawns a task in its constructor → needs a running event loop (2.3.0).

**WebSocket — message-based stream over HTTP.**

- Message boundaries are part of the protocol → no additional framing needed; one WebSocket message = one frame. 
- Delivery and ordering are guaranteed by the underlying TCP stream; lifecycle (open/close) is visible.
- HTTP-based handshake and URL addressing → fits web integrations and environments where only HTTP(S) ports are reachable.

| Property | TCP | UDP | WebSocket |
| --- | --- | --- | --- |
| Delivery & ordering | guaranteed | neither | guaranteed |
| Message boundaries | no → framing required | yes (datagrams) | yes |
| Connection lifecycle | yes (EOF / shutdown) | none | yes (open / close) |
| Framing needed | `SyncByteLengthFraming` | not required ⚠ | not required ⚠ |
| Typical use | commands, models, responses | high-rate telemetry | web & HTTP integration |
    
````python
# TCP — stream connection, framing required (2.3.1)
client = TcpSocketClient(host, port)
connection = await client.connect(logger=None)

# UDP — datagram connection, self-delimiting frames
socket = UdpSocket(localPort, maximumPayloadLength=65_535)
connection = socket.connect(host, port)

# WebSocket — message-based stream, HTTP handshake
client = WebSocketClient(host="localhost", port=8080, path=None)
connection = await client.connect(receiver=None, logger=None)
````

Encoding still applies everywhere. Whichever transport is chosen, messages are encoded exactly as before (2.3.2) — the encoding neither knows nor cares which transport carries its bytes.
Out-of-order delivery is largely absorbed by the data model. UDP may deliver datagrams out of order — but every Sample carries its own Timestamp, and a SampleTree keeps samples in timestamp order (see 2.1). A late-arriving sample is therefore placed into the history correctly instead of overwriting the newer value.

As said before: If you are interested in a performance-comparison of these, have a look at the SOIL-PERFORMANCE-PYTHON Repository.

#### 2.3.4 Assembling a Decoded Connection

The three layers above are combined through a single method that every
connection interface offers: `apply()`. Each call wraps the connection into
the next layer of the stack and returns the wrapped connection. Over a TCP
connection the full assembly takes two hops:

```python
from soil.framing import SyncByteLengthFraming
from soil.messaging import JsonEncoding

client = TcpSocketClient(host, port)
stream = await client.connect()                      # StreamConnection

frames = await stream.apply(SyncByteLengthFraming()) # -> FrameConnection
connection = await frames.apply(JsonEncoding())      # -> MessageConnection
```

- `StreamConnection.apply(framing)` applies the framing to the raw stream and
  returns a `FrameConnection` (`DecodedStream`). This hop exists only for
  stream transports — TCP. UDP and WebSocket connections are already
  frame-based and start at the second hop:
  ```python
  socket = UdpSocket(localPort)
  frames = socket.connect(host, port)                # already a FrameConnection
  connection = await frames.apply(JsonEncoding())    # -> MessageConnection
  ```
- `FrameConnection.apply(encoding)` applies the message encoding and returns
  a ready-to-use `MessageConnection` (`DecodedConnection`).

The same wrapping happens symmetrically on the server side: a server hands
you the incoming transport connection, and you apply framing (for TCP) and
encoding exactly as above.

**Buffers.** Until a receiver is set, the layers buffer incoming data — but
not all of them do. `DecodedConnection` keeps undecoded frames in an internal
buffer and delivers them as soon as a message receiver is registered via
`setReceiver()`. The framing layer below it, however, silently drops frames
that arrive before a frame receiver is set. When you assemble a stack
yourself with the building blocks of this chapter, attach the receivers
before data starts flowing — the convenience method `apply()` covers this
for the standard stack, hand-built stacks do not get this guarantee
automatically.

**Delivery is not guaranteed.** `send()` returns a request handle that
completes once the message was handed to the transport layer — not once the
peer received it (see 2.3.0). Failures during encoding or transmission are
reported through the optional logger passed to `apply()`, not raised to the
caller; a failed `send()` therefore does not stop your application, but it
also does not retry. If delivery matters, build acknowledgment into your
protocol on the message layer.

#### 2.3.5 Connection Lifecycle

The connection-oriented transports — TCP and WebSocket — have a visible
lifecycle: connect, open, close. This section collects how SOIL exposes that
lifecycle, and where it stays silent. UDP has no lifecycle at all (2.3.3):
a dead peer is simply quiet.

**Closing: `shutdown()`.** Every connection offers `shutdown()` — it closes
the message layer and the underlying transport connection. Call it on every
shutdown path of your application; connections do not close themselves:

```python
try:
    ...                                  # application logic
finally:
    await connection.shutdown()
```

**Being notified: `onClose()`.** To react after a connection closed — from
either side — register an async callback:

```python
async def handle_close() -> None:
    print("connection lost")

await connection.onClose(handle_close)
```

#### 2.3.6 Best Practices for Transport Stack

The two examples below stay at the frame level on purpose: it keeps them
minimal and isolates the transport concerns of this chapter. Full
message-level flows — subscriptions, reconnect with re-subscription —
are the topic of 2.5.

##### 2.3.6.1 A Minimal TCP Frame Exchange

A server that wraps every incoming client connection with framing, and a
client that builds the same stack and sends one frame. It shows the three
rules that matter in practice:

- build the stack **inside async code** (Actors need a running event loop, 2.3.0),
- attach the receiver **before** data starts flowing (2.3.4),
- shut the stack down **on every exit path** (2.3.5).

```python
import asyncio

from soil.framing import SyncByteLengthFraming
from soil.interfaces.tcp.client import TcpSocketClient
from soil.interfaces.tcp.server import TcpSocketServer


class PrintFrame:
    """Prints every frame that arrives over the connection."""

    async def acceptFrame(self, frame: bytes) -> None:
        print(f"received: {frame.decode()}")


async def main() -> None:
    # -- server side: one raw stream connection per client -- #
    server = TcpSocketServer(port=0)          # port 0: OS picks a free port

    async def handle(stream) -> None:
        frames = await stream.apply(SyncByteLengthFraming())   # raw -> frames
        await frames.setReceiver(PrintFrame())                 # before data flows

    server.onConnection(handle)
    assert await server.start()

    # -- client side: the same stack, built where the loop runs -- #
    port = await server.waitForPort()
    client = TcpSocketClient("localhost", port)
    stream = await client.connect()
    frames = await stream.apply(SyncByteLengthFraming())

    await frames.send(b"hello frame")         # one frame over the wire
    await asyncio.sleep(0.1)                   # let the server print it

    await frames.shutdown()                   # closes the whole stack
    assert await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

```python
#--Output--#
received: hello frame
```

### 2.4. Components & Storage

#### 2.4.1 Component A

#### 2.4.1 Component B

#### 2.4.5 Best Practices for Components & Storage



### 2.5. Networking

#### 2.5.1 Component A

#### 2.5.1 Component B

#### 2.5.5 Best Practices for Networking
