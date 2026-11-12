# Best Practice for SOIL-CORE-PYTHON - V1.0

The following document provides best practice examples for using the `SOIL-CORE-PYTHON` library.


## Table of contents

- **[1. Introduction](#1-introduction)**

- **[2. SOIL-CORE-PYTHON](#2-soil-core-python)**
  - **[2.1 Data Handling](#21-data-handling)**
    - [2.1.1 Value & Convertibles](#211-value--convertibles)
    - [2.1.2 Sample & Timestamp](#212-sample--timestamp)
    - [2.1.3 SampleTree](#213-sampletree)
    - [2.1.4 Path](#214-path)
    - [2.1.5 Best Practices for Data Handling](#215-best-practices-for-data-handling)
  - **[2.2 Messaging](#22-messaging)**
    - [2.2.1 Message Structure](#221-message-structure)
    - [2.2.2 Creating Messages](#222-creating-messages)
    - [2.2.3 Message Transmission & Connection](#223-message-transmission--connection)
    - [2.2.4 Best Practices for Messaging](#224-best-practices-for-messaging)
  - **[2.3 Transport Stack](#23-transport-stack)**
    - [2.3.1 Framing](#231-framing)
    - [2.3.2 Choosing an Encoding](#232-choosing-an-encoding)
    - [2.3.3 Network Protocols (TCP, UDP, WebSocket)](#233-network-protocols-tcp-udp-websocket)
    - [2.3.4 Assembling a Decoded Connection](#234-assembling-a-decoded-connection)
    - [2.3.5 Connection Lifecycle](#235-connection-lifecycle)
    - [2.3.6 Best Practices for Transport Stack](#236-best-practices-for-transport-stack)
  - **[2.4 Components & Storage](#24-components--storage)**
    - [2.4.1 Component Interfaces](#241-component-interfaces)
    - [2.4.2 Provider - Reading Data](#242-provider---reading-data)
    - [2.4.3 Receiver - Accepting Data](#243-receiver---accepting-data)
    - [2.4.4 Storage - Combining Read and Write](#244-storage---combining-read-and-write)
    - [2.4.5 Observable - Notifying Receivers](#245-observable---notifying-receivers)
    - [2.4.6 Best Practices for Components & Storage](#246-best-practices-for-components--storage)
    - [2.4.7 SOIL Component Catalog](#247-soil-component-catalog)
  - **[2.5 Practical Patterns](#25-practical-patterns)**
    - [2.5.1 Request/Response over TCP](#251-pattern-requestresponse-over-tcp)
    - [2.5.2 Telemetry Streaming over UDP](#252-pattern-telemetry-streaming-over-udp)
    - [2.5.3 Pub/Sub with Observable](#253-pattern-pubsub-with-observable)
    - [2.5.4 Remote Storage](#254-pattern-remote-storage)
    - [2.5.5 Reconnection Handling](#255-pattern-reconnection-handling)

> **Note:** Click any link to jump to that section.

---

## 1. Introduction

**SOIL** is not a new protocol, it´s built upon principles you already know and use every day.

### Why SOIL feels familiar

SOIL's core concepts mirror patterns found throughout computer science and everyday technology:

| SOIL Concept | Real-World Analogy |
|--------------|-------------------|
| **SampleTree** (hierarchical data) | File explorer folder structure, DOM trees, JSON/XML documents |
| **Samples with Timestamps** | Git commits, database transactions, sensor logs |
| **Path-based addressing** | File paths (`/home/user/file.txt`), URLs (`https://.../path/to/resource`), MQTT topics |
| **Publish/Subscribe** | MQTT topics, RSS feeds, event emitters, React state |
| **Message-based communication** | HTTP requests, CoAP, WebSockets, microservices |
| **Layered architecture** | OSI model, TCP/IP stack, middleware patterns |

### Design goals

1. **Intuitive**: If you've ever used a file explorer, you understand SampleTree. If you've ever sent an HTTP request, you understand SOIL messages.

2. **Protocol-agnostic**: SOIL is **not** a protocol. It's a layer **above** protocols. 

3. **Composable**: Components follow consistent interfaces (`Provider`, `Receiver`, `Storage`, `Observable`). Swap implementations without changing your application logic.

4. **Time-aware**: Every sample carries a timestamp. History queries, time-range subscriptions, and temporal data operations are built-in.

5. **Modular**: SOIL is built from independent, single-purpose layers. Each layer has a narrow interface and can be swapped without affecting others:
   - Swap the **transport** (TCP -> UDP -> WebSocket) without changing your message handling. 
   - Swap the **encoding** (JSON -> Binary -> Protobuf) without changing your application logic.
   - Swap the **storage** (in-memory -> database -> remote) without changing your data access code.

   This modularity means you can optimize each layer independently, depending what your usecase requires.
   And if your specific use case needs a custom encoding- or transport-layer; just implement the interface - all layers are agnostic, so as long as you follow the contract, it works out of the box.

### XKCD 927

![](https://imgs.xkcd.com/comics/standards.png)

SOIL is **not** trying to replace MQTT, CoAP, HTTP, or any other protocol. Instead, it provides a **unified data model** that works **with** these protocols. Think of SOIL as the **common language** your components speak, regardless of which transport they use.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│     App      │───>│   SOIL       │───>│   TCP/UDP/   │
│  (business   │    │  (data model │    │   WebSocket  │
│   logic)     │    │ + messaging) │    |  (transport) │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 2. SOIL-CORE-PYTHON

### 2.1. Data handling

The `soil.data` package provides the fundamental data types of `SOIL`. They all work together according to one principle:

**SampleTree** is a hierarchical, time-indexed store. Each node can hold **Samples** (which consist of **Values** with a **Timestamp**) and named child nodes. It is as simple as that.

```python
SampleTree (node "station")
├─ name: Sample(Value("Station-01"))
├─ history
│  ├─ temperature: Sample(21.5, t₁), Sample(23.8, t₂)   ← multiple samples = history
│  └─ humidity:    Sample(63, t₃)
```

#### 2.1.1 Value & Convertibles

`Value` is the universal container for a single piece of data. It can hold so called `Value.Type`s (`none`, `int`, `str`, `double`, `bytes`) as well as complex types (`Path`, `list[Value]`, `dict[str, Value]`). As this has previously caused some confusion: there is NO `bool` DataType. But `bool` can be easily done via `int` (0,1) or `str` ("False","True").

```python
from soil.data import Value, ValueType

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
location["city"].value      # -> "Berlin"
"name" in location          # -> False
list(location)              # -> ["city", "lat"]
```

`Convertibles` are there to bridge between your own classes and these containers, `SOIL` has two types:

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

A `Timestamp` represents a point in time.`
```python
now = Timestamp.current()

specific = Timestamp(2026, 10, 9, 16, 10, 45)
seconds = specific.timeIntervalSince1970    # seconds = 1,791,562,245 [s]
```

#### 2.1.3 SampleTree

A `SampleTree` is a tree of nodes. Each node holds a list of `Samples` and named children.

```python
from soil.data import Path, Sample, SampleTree, Timestamp, Value

# Create a tree with samples
tree = SampleTree.ofValue(Value(21.5), timestamp=Timestamp.current())

# Add a child with a value (returns the child node)
child = tree.childWithValue("city", Value("Berlin"))

# Attach an existing tree as a child (replaces any existing child)
location_tree = SampleTree.ofValue(Value(52.5200), Timestamp.current())
tree.add(location_tree, "location")

# Merge another tree into this one
other_tree = SampleTree.ofValue(Value(13.4050), Timestamp.current())
tree.merge(other_tree)

# Access nodes
node = tree.existingNode(Path.of("city"))  # child or None

print(tree)                                         # built-in multi-line description
```    
```python
#--Output--#
samples:
  21.5 (11.11.2026 08:31:23)
  13.4049999999999994 (11.11.2026 08:31:23)
children:
  city:
    samples:
      'Berlin' (11.11.2026 08:31:23)
  location:
    samples:
      52.5200000000000031 (11.11.2026 08:31:23)
```                              

#### 2.1.4 Path

A `Path` is an array of strings identifying a state, input or output inside a tree. Each component addresses one level of the tree. Paths are used for navigation and for read/write/delete operations on specific nodes.

```python
from soil.data import Path

# Create a path
path = Path.of("history", "temperature")   # ["history", "temperature"]
path = Path(["history", "temperature"])    # equivalent construction

print(path)                                # "history > temperature"
print("Size:", path.size)                  # 2
print("Is empty:", path.isEmpty)           # False

longer = path.appending("max")             # ["history", "temperature", "max"]
prefix = Path.of("history")

print("Has prefix 'history':", path.hasPrefix(prefix))           # True
print("Removing prefix:", path.removingPrefix(prefix))           # ["temperature"]
print("Common prefix:", Path.of("a", "b").commonPrefix(Path.of("a", "c")))   # ["a"]
```
```python
#--Output--#
OUTPUT:
history > temperature
Size: 2
Is empty: False
Has prefix 'history': True
Removing prefix: temperature
Common prefix: a
```      


#### 2.1.5 Best Practices for Data handling

##### 2.1.5.1 Weather Station

Minimal example showing `SampleTreeConvertible`:

```python
from soil.data import SampleTree, SampleTreeConvertible, Value

class WeatherStation(SampleTreeConvertible):
    def __init__(self, name: str):
        self.name = name
        self.history = SampleTree()

    def set_temperature(self, value: Value):
        self.history.childWithValue("temperature", value)

    def toTree(self) -> SampleTree:
        tree = SampleTree()
        tree.childWithValue("name", Value(self.name))
        tree.add(self.history, "history")
        return tree

    @classmethod
    def fromTree(cls, tree: SampleTree) -> "WeatherStation":
        name = str(tree.existingChild("name").newestSample.value.value)
        station = cls(name)
        station.history = tree.existingChild("history")
        return station

# Usage
station = WeatherStation("Station-01")
station.set_temperature(Value(21.5))
tree = station.toTree()
restored = WeatherStation.fromTree(tree)

print(tree)
```
```python
#--Output--#
children:
  name:
    samples:
      'Station-01' (11.11.2026 08:36:36)
  history:
    children:
      temperature:
        samples:
          21.5 (11.11.2026 08:36:36)
```     

> **Full example:** See [`examples/data/weather_station.py`](examples\data\weather_station.py) for a complete implementation with location data, humidity, and assertions.

##### 2.1.5.2 Library with Books

Minimal example showing `ValueConvertible` and `SampleTreeConvertible`:

```python
from soil.data import SampleTree, SampleTreeConvertible, Value, ValueConvertible

class Book(ValueConvertible):
    def __init__(self, isbn: str, title: str, author: str):
        self.isbn, self.title, self.author = isbn, title, author

    def toValue(self) -> Value:
        return Value(f"{self.isbn}|{self.title}|{self.author}")

    @classmethod
    def fromValue(cls, value: Value) -> "Book":
        parts = value.value.split("|")
        return cls(parts[0], parts[1], parts[2])

class Library(SampleTreeConvertible):
    def __init__(self, name: str):
        self.name = name
        self.books = SampleTree()

    def add_book(self, book: Book):
        self.books.childWithValue(book.isbn, book.toValue())

    def toTree(self) -> SampleTree:
        tree = SampleTree()
        tree.childWithValue("name", Value(self.name))
        tree.add(self.books, "books")
        return tree

    @classmethod
    def fromTree(cls, tree: SampleTree) -> "Library":
        lib = cls(str(tree.existingChild("name").newestSample.value.value))
        lib.books = tree.existingChild("books")
        return lib

# Usage
library = Library("City Library")
library.add_book(Book("978-0-123456-78-9", "Example Book", "Author Name"))
tree = library.toTree()
```

> **Full example:** See [`examples/data/library.py`](examples/data/library.py) for complete implementation with visitor count history and assertions.

##### 2.1.5.3 Device Management

Minimal example showing map-Values and list-Values:

```python
from soil.data import SampleTree, SampleTreeConvertible, Value, ValueConvertible

class DeviceSpec(ValueConvertible):
    def __init__(self, manufacturer: str, model: str, firmware: str):
        self.manufacturer, self.model, self.firmware = manufacturer, model, firmware

    def toValue(self) -> Value:
        return Value({
            "manufacturer": Value(self.manufacturer),
            "model": Value(self.model),
            "firmware": Value(self.firmware),
        })

    @classmethod
    def fromValue(cls, value: Value) -> "DeviceSpec":
        d = value.value
        return cls(d["manufacturer"].value, d["model"].value, d["firmware"].value)

class Device(SampleTreeConvertible):
    def __init__(self, name: str):
        self.name = name
        self.history = SampleTree()

    def set_spec(self, spec: DeviceSpec):
        self.history.childWithValue("spec", spec.toValue())

    def toTree(self) -> SampleTree:
        tree = SampleTree()
        tree.childWithValue("name", Value(self.name))
        tree.add(self.history, "history")
        return tree

    @classmethod
    def fromTree(cls, tree: SampleTree) -> "Device":
        device = cls(str(tree.existingChild("name").newestSample.value.value))
        device.history = tree.existingChild("history")
        return device

# Usage
device = Device("Thermostat")
device.set_spec(DeviceSpec("Ikea Home", "MT-200", "v1.4.2"))
tree = device.toTree()
```

> **Full example:** See [`examples/data/device_management.py`](examples/data/device_management.py) for complete implementation with sensors list and power history.

##### 2.1.5.4 Visualizer

These are not needed for fuctionality but are nice to have for debugging or visualization purposes.
`SOIL-CORE-PYTHON` also delivers a built-in unctionality with the normal `print()`-Statement which which shows all samples per node with formatted timestamps, but is less compact and does not render maps and lists structurally.

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
from soil.messaging import Message, MessageType, Value, SampleTree, Path

message = Message(
    type=MessageType.DATA,
    path=Path.of("history", "temperature"),
    data=SampleTree.ofValue(Value(21.5)),
)
```

#### 2.2.2 Creating Messages

`Message` provides factory methods for each message type. Prefer them over manual construction – they set the correct `MessageType` automatically:

```python
from soil.messaging import Message, MessageType
from soil.data import Path, Sample, SampleTree, Timestamp, Value


# -- Data messages --
Message.value(Value(21.5), Path.of("history", "temperature"))
# a single sample (timestamp defaults to now)

samples = [Sample(Value(1)), Sample(Value(2))]
Message.samples(samples, Path.of("history", "temperature"))
# a list of samples

# Create a simple library tree for the tree() example
class Library(SampleTree):
    def toTree(self) -> SampleTree:
        tree = SampleTree()
        tree.childWithValue("name", Value("My Library"))
        return tree

library = Library()
Message.tree(library.toTree(), Path.of("library"))
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

# Print a few examples to verify they work
print("Data message:")
print(Message.value(Value(21.5), Path.of("history", "temperature")))
print()

print("Request message:")
print(Message.request(Path.of("history", "temperature"), limit=100, id=42))
print()

print("Subscription include:")
print(Message.include(Path.of("device"), depth=2))
```
```python
#--Output--#
Data message:
type: data
path: history > temperature
data:
  samples:
    21.5 (now)

Request message:
type: read
path: history > temperature
count: 100
id: 42

Subscription include:
type: include
path: device
depth: 2
```     

#### 2.2.3 Message Transmission & Connection

Messages are exchanged over a transport layer through four building blocks:

```
Message  ──encode──>  msg_encoded  ──FrameConnection──>  msg_encoded  ──decode──>  Message
```

**`MessageEncoding`** is the abstract interface for encoding algorithms. It defines the two directions of the conversion between messages and transport data. 

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

##### 2.2.4.1 Use Factory Methods

The `Message` class provides factory methods for each message type. Prefer them over manual construction - they set the correct `MessageType` automatically:

| Factory Method | Use Case |
|----------------|----------|
| `Message.value(value, path)` | Send a single sample |
| `Message.samples(samples, path)` | Send multiple samples |
| `Message.tree(tree, path)` | Send a complete `SampleTree` |
| `Message.acknowledge(request, path)` | Acknowledge a request |
| `Message.request(path, ...)` | Query data (read request) |
| `Message.delete(path, ...)` | Delete data |
| `Message.include(path, depth)` | Add subscription inclusion rule |
| `Message.exclude(path, depth)` | Add subscription exclusion rule |
| `Message.deleteRules(path)` | Remove subscription rules |

##### 2.2.4.2 Basic Example

```python
from soil.data import Path, Sample, SampleTree, Value
from soil.messaging import Message

# Create a data message for a single value
msg = Message.value(Value(21.5), Path.of("weather", "temperature"))

# Create a request message
msg = Message.request(
    Path.of("history", "temperature"),
    limit=100,
    id=42
)

# Create subscription messages
include = Message.include(Path.of("device"), depth=2)
exclude = Message.exclude(Path.of("device", "power"))
```

> **Full example:** See [`examples/messaging/messaging.py`](examples\messaging\messaging.py) for a complete working example with output.

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

#### 2.3.1 Framing

A TCP connection is a raw byte stream. It carries no information about where one message ends and the next one begins - if a component sends two messages back to back, the peer cannot split them apart. Framing adds these boundaries: it wraps a raw stream connection into a ``FrameConnection`` whose units are complete, self-delimiting frames.

``SyncByteLengthFraming``  is SOIL's synchronous framing algorithm. Each frame is prefixed with a configurable sync sequence (default 0xAA 0x55) followed by a 2-byte big-endian length field, so the receiver can extract frames of arbitrary size from the stream without ambiguity. The maximum payload is 65,535 bytes (the largest value that fits the length field); a larger payload raises a ``FramingError`` on encoding.

Framing is defined by the StreamFraming interface - two async directions:
- ``encodeForStream(message: bytes) -> bytes`` - add framing information to an encoded message
- ``processStreamBytes(data: bytes) -> list[bytes]`` - extract every complete frame from newly received stream bytes; incomplete frames stay in an internal ring buffer until the rest arrives


````
framing = SyncByteLengthFraming(
    syncBytes=b"\xAA\x55",       # identifies the start of each frame
    maxPayloadLength=65_535,     # 0 < length <= 65,535
)
````


#### 2.3.2 Choosing an Encoding

All encodings implement the same `MessageEncoding` interface (see 2.2.3) and are therefore interchangeable - switching never touches the surrounding components.
   Encoding | Size / Speed | Human-Readability | Recommended for |
 |---|---|---|---|
 | `BINARY` | best | none | production, high message rates |
 | `JSON` | larger / slower | fully human-readable | development & debugging |
 | `COMPACT JSON` | in between | reduced | JSON with a minimized footprint |
 | `Protobuf` (optional library) | compact | none | schema-driven integrations |

Both sides of a connection **must** use the same encoding.

**Recommendation:** develop and debug with `JSON` - you can inspect live frames with any standard tool, which makes wire-level problems immediately visible. Switch to `BINARY` when message size or encoding speed matter; it is a one-line change at stack construction.

If you are interested in a performance-comparison of these, have a look at the SOIL-PERFORMANCE-PYTHON Repository.


#### 2.3.3 Network Protocols (TCP, UDP, WebSocket)
The bottom layer of the stack is the network transport. SOIL provides interfaces for the common protocols - TCP, UDP and WebSocket. All of them sit behind the same connection interface, so the layers above (encoding, message layer) remain unchanged. What differs per protocol is whether framing is needed and which lifecycle guarantees exist.

| Property | TCP | UDP | WebSocket |
| --- | --- | --- | --- |
| Delivery & ordering | guaranteed | neither | guaranteed |
| Message boundaries | no -> framing required | yes (datagrams) | yes |
| Connection lifecycle | yes (EOF / shutdown) | none | yes (open / close) |
| Framing needed | `SyncByteLengthFraming` | not required | not required |
|
    
````python
# TCP - stream connection, framing required (2.3.1)
client = TcpSocketClient(host, port)
stream = await client.connect()
connection = await stream.apply(SyncByteLengthFraming())

# UDP - datagram connection, self-delimiting frames
socket = UdpSocket(localPort, maximumPayloadLength=65_535)
connection = socket.connect(host, port)

# WebSocket - message-based stream, HTTP handshake
client = WebSocketClient(host="localhost", port=8080, path=None)
connection = await client.connect()
````

Encoding still applies everywhere. Whichever transport is chosen, messages are encoded exactly as before (2.3.2) - the encoding neither knows nor cares which transport carries its bytes.

As said before: If you are interested in a performance-comparison of these, have a look at the SOIL-PERFORMANCE-PYTHON Repository.

#### 2.3.4 Assembling a Decoded Connection

The three layers above are combined through a single method that every connection interface offers: `apply()`. Each call wraps the connection into the next layer of the stack and returns the wrapped connection. Over a TCP connection the full assembly takes two hops:

```python
from soil.framing import SyncByteLengthFraming
from soil.encoding.json import JsonEncoding

client = TcpSocketClient(host, port)
stream = await client.connect()                      # StreamConnection

frames = await stream.apply(SyncByteLengthFraming()) # -> FrameConnection
connection = await frames.apply(JsonEncoding())      # -> MessageConnection
```

- `StreamConnection.apply(framing)` applies the framing to the raw stream and
  returns a `FrameConnection` (`DecodedStream`). This hop exists only for
  stream transports - TCP. UDP and WebSocket connections are already
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

**Delivery is not guaranteed.** `send()` returns a request handle that
completes once the message was handed to the transport layer - not once the
peer received it (see 2.3.0). Failures during encoding or transmission are
reported through the optional logger passed to `apply()`, not raised to the
caller; a failed `send()` therefore does not stop your application, but it
also does not retry. If delivery matters, build acknowledgment into your
protocol on the message layer.

#### 2.3.5 Connection Lifecycle

The connection-oriented transports - TCP and WebSocket - have a visible
lifecycle: connect, open, close. This section collects how SOIL exposes that
lifecycle, and where it stays silent. UDP has no lifecycle at all (2.3.3):
a dead peer is simply quiet.

**Closing: `close()`.** Every connection offers `close()` - it closes
the message layer and the underlying transport connection. Call it on every
shutdown path of your application; connections do not close themselves:

```python
try:
    ...     # application logic
finally:
    await connection.close()
```

**Being notified: `onClose()`.** To react after a connection closed - from
either side - register an async callback:

```python
async def handle_close() -> None:
    print("connection lost")

await connection.onClose(handle_close)
```

#### 2.3.6 Best Practices for Transport Stack

The two examples below stay at the frame level on purpose: it keeps them
minimal and isolates the transport concerns of this chapter. Full
message-level flows - subscriptions, reconnect with re-subscription -
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
from soil.requests import CompletedRequest, Request


class PrintFrame:
    """Prints every frame that arrives over the connection."""

    def acceptFrame(self, frame: bytes) -> Request:
        print(f"received: {frame.decode()}")
        return CompletedRequest()


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

SOIL components are the building blocks of applications. They follow consistent patterns for data flow, state management, and inter-component communication.

#### 2.4.1 Component Interfaces

SOIL defines several core component interfaces:

| Interface | Purpose | Key Methods |
|-----------|---------|-------------|
| `Provider` | Read data from a source | `tree()`, `samples()`, `currentValue()` |
| `Receiver` | Accept incoming data | `acceptMessage()`, `accept()` |
| `Storage` | Store and retrieve data | Combines `Provider` + `Receiver` + `delete()` |
| `Observable` | Notify receivers of changes | `setReceiver()`, `notifyReceivers()` |
| `Connection` | Send and receive messages | `send()`, `setReceiver()` |

**Design Principle:** Components are *actors* - each runs in its own async task and processes work independently. This means:

- Components must be constructed where an event loop is running (inside `async def` code)
- Accessing a component after it was shut down raises `ActorClosedError`
- Communication between components happens via messages or direct method calls

#### 2.4.2 Provider - Reading Data

A `Provider` is a component that can provide values. It does not send data by itself but makes data available when requested. The central method is `tree()` - all other read methods are convenience wrappers:

```python
@abstractmethod
async def tree(
    self,
    path: Path,
    start: Timestamp | None,
    end: Timestamp | None,
    depth: int | None,
    limitPerNode: int | None
) -> SampleTree:
    """Read a data tree for a given path within a given interval."""
```

**Parameters:**
- `path`: The root path to read
- `start`: Exclusive start of the time interval (`None` = beginning of time)
- `end`: Inclusive end of the time interval (`None` = end of time)
- `depth`: Number of levels below the path to include (`0` = no children)
- `limitPerNode`: Maximum samples per node (`None` = no limit)

**Sort order:**
- Ascending, if `end = nil`
- Descending, if `end != nil` and `start = nil`
- Ascending, if `start < end`
- Descending, if `start > end`

**Convenience methods:**

```python
# Get current value at a path
value = await provider.currentValue(Path.of("sensor", "temperature"))

# Get current sample (with timestamp)
sample = await provider.currentSample(Path.of("sensor", "temperature"))

# Get entire current tree up to depth=2
tree = await provider.currentTree(Path.of("sensor"), depth=2)

# Get samples in a time range
samples = await provider.samples(
    Path.of("history", "temperature"),
    start=Timestamp(2026, 1, 1),
    end=Timestamp.current(),
    limit=100
)

# Get value at a specific point in time
tree = await provider.treeAtTime(
    Path.of("sensor"),
    time=Timestamp(2026, 10, 9, 16, 10, 45),
    depth=1
)
```

#### 2.4.3 Receiver - Accepting Data

A `Receiver` accepts incoming data via messages or direct sample trees:

```python
@abstractmethod
def accept(self, tree: SampleTree, path: Path) -> Request:
    """
    Receive a tree for a path.
    
    Returns a Request handle that can be awaited to wait for completion.
    """

async def acceptMessage(self, message: Message) -> None:
    """Process an incoming message (default implementation wraps in accept())."""
```

**Important:** `accept()` is **synchronous** - it returns immediately with a `Request` handle. The actual ingestion happens asynchronously in the background.

**Example: Logging Receiver**

```python
from soil.components import Receiver
from soil.messaging import Message

class LoggingReceiver(Receiver):
    """Logs all incoming messages."""

    async def acceptMessage(self, message: Message) -> None:
        print(f"Received: {message.type} at {message.path}")
        if message.data:
            print(f"  Data: {message.data}")
```

#### 2.4.4 Storage - Combining Read and Write

A `Storage` combines `Provider` and `Receiver` with the ability to delete data:

```python
class Storage(Provider, Receiver):
    @abstractmethod
    def delete(
        self,
        path: Path = Path(),
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        depth: int | None = None
    ) -> Request:
        """Delete data from the storage."""
```

**Example: In-Memory Storage**

```python
import asyncio

from soil.data import Path, SampleTree, Value
from soil.messaging import Message, MessageType
from soil.storage import InMemoryStorage


async def main():
    storage = InMemoryStorage()

    # Store data using accept() from Receiver interface
    # This returns a Request that can be handled in three ways

    # Option 1: Fire and forget (data will be ingested in background)
    tree = SampleTree.ofValue(Value(21.5), timestamp=None)
    storage.accept(tree, Path.of("weather", "temperature"))
    print("Option 1: Fire and forget - accepted without waiting")

    # Option 2: Await the request directly
    tree = SampleTree.ofValue(Value(23.8), timestamp=None)
    request = storage.accept(tree, Path.of("weather", "temperature"))
    await request
    print("Option 2: Await request - storage accepted value")

    # Option 3: Await request.wait() explicitly
    tree = SampleTree.ofValue(Value(25.2), timestamp=None)
    request = storage.accept(tree, Path.of("weather", "temperature"))
    await request.wait()
    print("Option 3: Await request.wait() - storage accepted value")

    # Read current value using Provider interface
    current = await storage.currentValue(Path.of("weather", "temperature"))
    print(f"Current temperature: {current.value if current else 'None'}")

    # Read history using Provider interface
    samples = await storage.samples(
        Path.of("weather", "temperature"),
        limit=10
    )
    print(f"Temperature history: {[s.value.value for s in samples]}")

    # Delete data using Storage interface
    request = storage.delete(Path.of("weather", "temperature"))
    await request
    print("After deletion:")
    samples = await storage.samples(Path.of("weather", "temperature"), limit=10)
    print(f"Temperature history: {[s.value.value for s in samples]}")
    print("Delete completed")

    await storage.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```
```python
#--Output--#
Option 1: Fire and forget - accepted without waiting
Option 2: Await request - storage accepted value
Option 3: Await request.wait() - storage accepted value
Current temperature: 25.2
Temperature history: [21.5, 23.8, 25.2]
After deletion
Temperature history: []
Delete completed
```

#### 2.4.5 Observable - Notifying Receivers

An `Observable` manages subscriptions and filters data trees based on subscription rules before forwarding to receivers.

```python
class Observable(Distributor):
    # Subscription management
    def include(self, path: Path, depth: int | None) -> Request: ...
    def exclude(self, path: Path, depth: int | None) -> Request: ...
    def deleteRules(self, path: Path, depth: int | None = None) -> Request: ...
    
    # Check if path is covered by subscription
    async def isSubscribed(self, path: Path) -> bool: ...
    
    # Filter tree based on subscription rules
    async def reduce(self, tree: SampleTree, path: Path) -> SampleTree | None: ...
    
    # Distribute data to receiver (if subscribed)
    async def distribute(self, tree: SampleTree, path: Path) -> None: ...
```

**Key concept:** `Observable` doesn't broadcast to "all receivers" - it has **one receiver** (set via `setReceiver()`), and only sends data that matches the subscription rules.


#### 2.4.6 Best Practices for Components & Storage

##### 2.4.6.1 Component Lifecycle

Components are actors that run in their own async tasks. Always:

1. **Construct inside async code** - Components need a running event loop
2. **Shutdown on exit** - Call `shutdown()` on every exit path
3. **Handle `ActorClosedError`** - Accessing a shut-down component raises this

```python
async def main():
    storage = InMemoryStorage()  # Spawns a task internally

    try:
        # Use the component
        await storage.acceptMessage(message)
    finally:
        # Always shut down
        await storage.shutdown()
```

##### 2.4.6.2 Combining Components

Components can be combined to build complex behaviors:

```
┌─────────────┐     ┌─────────────┐     ┌────────────┐
│  Observable │ ──> │   Storage   │ ──> │  Provider  │
│  (notifies) │     │  (stores)   │     │  (reads)   │
└─────────────┘     └─────────────┘     └────────────┘
```

```python
class ObservableStorage(Storage):
    """Storage that notifies receivers on every write."""

    def __init__(self):
        super().__init__()
        self._data = SampleTree()
        self._receivers = []

    async def acceptMessage(self, message: Message) -> None:
        if message.type == MessageType.DATA:
            self._data.mergeAtPath(message.data, message.path)
            await self.notifyReceivers(message)

    # ... implement Provider and delete() ...
```

**Prefer plain `await`** unless you deliberately want to ignore failures - `wait()` turns errors into silence.

---

### 2.4.7 SOIL Component Catalog

#### Extract of current implementations

| Component | Purpose | Location |
|-----------|---------|----------|
| **Storage** | In-memory or remote data storage | `soil.components.storage` |
| **ObservableStorage** | Storage with subscription support | `soil.components.observable_storage` |
| **HostedStorage** | Storage that hosts data locally | `soil.connection.hosted_storage` |
| **RemoteStorage** | Proxy to remote storage | `soil.connection.remote_storage` |
| **RemoteObservable** | Observable over network | `soil.connection.remote_observable` |
| **RemoteTransmitter** | Forwards data to remote | `soil.connection.remote_transmitter` |
| **DataMessageSplitter** | Splits large trees into chunks | `soil.connection.data_message_splitter` |
| **ReconnectingConnection** | Auto-reconnect wrapper | `soil.connection.re_connection` |

#### Encoding Implementations

| Encoding | Use Case | Location |
|----------|----------|----------|
| **BinaryEncoding** | Production, minimal overhead | `soil.encoding.binary` |
| **JsonEncoding** | Debugging, human-readable | `soil.encoding.json` |
| **CompactJsonEncoding** | Balance between size & readability | `soil.encoding.json.min` |

#### Transport Implementations

| Transport | Protocol | Location |
|-----------|----------|----------|
| **TcpSocketClient/Server** | Reliable stream | `soil.interfaces.tcp` |
| **UdpSocket** | Connectionless datagrams | `soil.interfaces.udp` |
| **WebSocketClient/Server** | Message-based over HTTP | `soil.interfaces.websocket` |

#### Framing Implementations

| Framing | Purpose | Location |
|---------|---------|----------|
| **SyncByteLengthFraming** | Sync bytes + length prefix | `soil.framing.sync` |
| **LoggingFraming** | Debug framing with logging | `soil.framing.logger` |

### Building Your Own Components

SOIL's modularity means you can create custom components by implementing the interfaces. Eg. for a storage component:

```python
from soil.components import Storage
from soil.data import Path, SampleTree, Timestamp

class MyCustomStorage(Storage):
    """Example: Database-backed storage."""
    
    def __init__(self, db_connection):
        self._db = db_connection
    
    async def tree(self, path, start, end, depth, limitPerNode):
        # Query database and return SampleTree
        ...
    
    async def acceptMessage(self, message: Message) -> None:
        # Store incoming message in database
        ...
    
    def delete(self, path, start, end, depth):
        # Delete from database
        ...
```
---

### 2.5. Practical Patterns

This section shows **how to combine SOIL components** for real-world use cases — pulling together the transports, encodings and components from the previous sections into complete, runnable flows.

#### 2.5.1 Pattern: Request/Response over TCP

**Use case:** Commands, configuration, queries — when you need guaranteed delivery.

```python
import asyncio

from soil.data import Path, SampleTree, Value
from soil.encoding.json import JsonEncoding
from soil.framing import SyncByteLengthFraming
from soil.interfaces.tcp import TcpSocketClient, TcpSocketServer
from soil.messaging import Message, MessageReceiver, MessageType
from soil.requests import CompletedRequest


# -- Server: remember received values, reply to read requests -- #
class WeatherServer(MessageReceiver):
    def __init__(self):
        self.data = SampleTree()

    def acceptMessage(self, message: Message) -> CompletedRequest:
        if message.type == MessageType.REQUEST:
            node = self.data.existingNode(message.path)
            samples = node.getSamples(message.time, message.end, message.count) if node else []
            asyncio.ensure_future(
                self.connection.send(
                    Message.samples(samples, message.path, request=message.id, totalMessages=1)
                )
            )
        elif message.type == MessageType.DATA:
            self.data.mergeAtPath(message.data, message.path)
        return CompletedRequest()


# -- Client: remember only the response whose id matches the request -- #
class ResponseCollector(MessageReceiver):
    def __init__(self, request_id: int):
        self.request_id = request_id
        self.response = None

    async def acceptMessage(self, message: Message) -> CompletedRequest:
        if message.type == MessageType.DATA and message.id == self.request_id:
            self.response = message
        return CompletedRequest()


async def main():
    server = TcpSocketServer(port=0)

    async def handle_connection(connection):
        framed = await connection.apply(SyncByteLengthFraming())
        decoded = await framed.apply(JsonEncoding())
        server_obj = WeatherServer()
        server_obj.connection = decoded
        await decoded.setReceiver(server_obj)

    server.onConnection(handle_connection)
    assert await server.start()
    port = await server.waitForPort()

    client = TcpSocketClient("localhost", port)
    stream = await client.connect()
    framed = await stream.apply(SyncByteLengthFraming())
    connection = await framed.apply(JsonEncoding())

    collector = ResponseCollector(request_id=1)
    await connection.setReceiver(collector)

    # Seed the server with values (DATA messages are stored by path).
    await connection.send(Message.value(Value(21.5), Path.of("temperature")))
    await connection.send(Message.value(Value(63), Path.of("humidity")))

    # Read a value back from the server.
    await connection.send(Message.request(Path.of("temperature"), id=1))
    await asyncio.sleep(0.2)  # give the round-trip time to complete

    if collector.response:
        # The response carries the requested samples at its root,
        # and the requested path in `message.path`.
        sample = collector.response.data.newestSample
        value = str(sample.value.value) if sample else "n/a"
        print(f"Received value: {value}")
    else:
        print("No response received")

    await connection.shutdown()
    assert await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
```
```python
#--Output--#
Received value: 21.5
```


#### 2.5.2 Pattern: Telemetry Streaming over UDP

**Use case:** High-rate sensor data — newest value matters, occasional loss is acceptable.

```python
import asyncio

from soil.data import Path, SampleTree, Value
from soil.encoding.json import JsonEncoding
from soil.interfaces.udp import UdpSocket
from soil.messaging import Message, MessageType, MessageReceiver


class TelemetryCollector(MessageReceiver):
    """Stores the newest sample seen at each path."""

    def __init__(self):
        self.data = SampleTree()
        self.seen = 0

    async def acceptMessage(self, message: Message) -> None:
        if message.type == MessageType.DATA:
            self.data.mergeAtPath(message.data, message.path)
            self.seen += 1
            print(f"Telemetry: {message.path} = {message.data.newestSample.value.value}")


async def main():
    # UDP has no server — just a socket that both sides share.
    # The receiver answers any inbound datagram, so it uses onConnection()
    # to wrap a fresh connection and install its decoder + receiver.
    collector = TelemetryCollector()

    async def handle_incoming(connection):
        decoded = await connection.apply(JsonEncoding())
        await decoded.setReceiver(collector)

    receiver = UdpSocket(localPort=8080)
    receiver.onConnection(handle_incoming)
    await receiver.ready()

    # The sender (on this or another machine).
    sender = UdpSocket(localPort=0)
    await sender.ready()
    sender_conn = sender.connect("127.0.0.1", 8080)
    encoded = await sender_conn.apply(JsonEncoding())

    for value in [21.5, 22.1, 23.0]:
        await encoded.send(Message.value(Value(value), Path.of("sensor", "temperature")))
        await asyncio.sleep(0.05)

    # Wait until the collector has seen all values (UDP is lossy, so poll).
    for _ in range(50):
        if collector.seen >= 3:
            break
        await asyncio.sleep(0.05)

    print(f"Received {collector.seen} telemetry messages")

    receiver.close()
    sender.close()


if __name__ == "__main__":
    asyncio.run(main())
```
```python
#--Output--#
Telemetry: sensor > temperature = 21.5
Telemetry: sensor > temperature = 22.1
Telemetry: sensor > temperature = 23.0
Received 3 telemetry messages
```

#### 2.5.3 Pattern: Pub/Sub with Observable

**Use case:** Subscription-based updates — clients choose which data they want.

```python
import asyncio

from soil.components.receiver import Receiver
from soil.connection import HostedObservableStorage, RemoteObservableStorage
from soil.data import Path, SampleTree, Value
from soil.encoding.json import JsonEncoding
from soil.framing import SyncByteLengthFraming
from soil.interfaces.tcp import TcpSocketClient, TcpSocketServer
from soil.messaging import Message
from soil.requests import CompletedRequest, Request
from soil.storage import InMemoryStorage, ObservingStorage


# -- Server: a storage that can be subscribed to -- #
async def handle_server_connection(connection):
    framed = await connection.apply(SyncByteLengthFraming())
    decoded = await framed.apply(JsonEncoding())
    storage = ObservingStorage(InMemoryStorage())
    await HostedObservableStorage.create(storage, decoded)
    # Publish a value now that clients can subscribe to it.
    await asyncio.sleep(0.2)
    await decoded.send(Message.value(Value(25.0), Path.of("weather", "temperature")))
    return storage


# -- Client: collect updates that match the subscription -- #
class UpdateCollector(Receiver):
    def __init__(self):
        self.values = []

    def accept(self, tree: SampleTree, path: Path = Path()) -> Request:
        node = tree.existingNode(Path.of("weather", "temperature"))
        sample = node.newestSample if node is not None else tree.newestSample
        if sample is None:
            return CompletedRequest()
        self.values.append(str(sample.value.value))
        print(f"Subscribed update: {sample.value.value}")
        return CompletedRequest()


async def main():
    server = TcpSocketServer(port=0)

    async def handle_connection(connection):
        await handle_server_connection(connection)

    server.onConnection(handle_connection)
    assert await server.start()
    port = await server.waitForPort()

    client = TcpSocketClient("localhost", port)
    stream = await client.connect()
    framed = await stream.apply(SyncByteLengthFraming())
    decoded = await framed.apply(JsonEncoding())

    remote = await RemoteObservableStorage.create(decoded)

    collector = UpdateCollector()
    await remote.setReceiver(collector)

    # Choose which data to receive.
    await remote.include(Path.of("weather"), depth=2)
    await remote.exclude(Path.of("weather", "humidity"), depth=1)

    await asyncio.sleep(0.5)  # wait for the published update to arrive
    print(f"Collected {len(collector.values)} updates")
    await decoded.close()
    assert await server.stop()


if __name__ == "__main__":
    asyncio.run(main())

```
```python
#--Output--#
Subscribed update: 25.0
Collected 1 updates
```


#### 2.5.4 Pattern: Remote Storage

**Use case:** Client-server data storage — central repository accessible over network.

```python
import asyncio

from soil.connection import HostedStorage, RemoteStorage
from soil.data import Path, SampleTree, Value
from soil.encoding.json import JsonEncoding
from soil.framing import SyncByteLengthFraming
from soil.interfaces.tcp import TcpSocketClient, TcpSocketServer
from soil.storage import InMemoryStorage


async def main():
    server = TcpSocketServer(port=0)

    async def handle_connection(connection):
        framed = await connection.apply(SyncByteLengthFraming())
        decoded = await framed.apply(JsonEncoding())
        # Expose a local storage over the connection.
        await HostedStorage.create(InMemoryStorage(), decoded)

    server.onConnection(handle_connection)
    assert await server.start()
    port = await server.waitForPort()

    client = TcpSocketClient("localhost", port)
    stream = await client.connect()
    framed = await stream.apply(SyncByteLengthFraming())
    decoded = await framed.apply(JsonEncoding())

    remote = await RemoteStorage.create(decoded)

    # Write a value to the remote storage.
    await remote.accept(SampleTree.ofValue(Value(21.5), timestamp=None), Path.of("weather", "temperature"))
    await asyncio.sleep(0.1)

    # Read it back. Request the exact path, so the sample is returned at the tree root.
    tree = await remote.tree(Path.of("weather", "temperature"), start=None, end=None, depth=None, limitPerNode=None)
    sample = tree.newestSample
    value = str(sample.value.value) if sample else "n/a"
    print(f"Remote value: {value}")

    await decoded.close()
    assert await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
```
```python
#--Output--#
Remote value: 21.5
```


#### 2.5.5 Pattern: Reconnection Handling

**Use case:** Resilient connections — auto-reconnect after failures.

```python
import asyncio

from soil.connection import ReconnectingConnection
from soil.data import Path, SampleTree, Value
from soil.encoding.json import JsonEncoding
from soil.framing import SyncByteLengthFraming
from soil.interfaces.tcp import TcpSocketClient, TcpSocketServer
from soil.messaging import Message, MessageReceiver, MessageType


async def make_connect(port: int):
    """Factory: build a fresh decoded connection to the server at a given port."""
    async def connect():
        client = TcpSocketClient("127.0.0.1", port)
        stream = await client.connect()
        framed = await stream.apply(SyncByteLengthFraming())
        return await framed.apply(JsonEncoding())
    return connect


# -- Server side: print whatever arrives over each new connection -- #
class PrintReceiver(MessageReceiver):
    async def acceptMessage(self, message: Message):
        if message.type == MessageType.DATA:
            sample = message.data.newestSample
            value = str(sample.value.value) if sample else "n/a"
            print(f"Server received [{message.path}] = {value}")


async def main():
    server = TcpSocketServer(port=0)

    async def handle_connection(connection):
        framed = await connection.apply(SyncByteLengthFraming())
        decoded = await framed.apply(JsonEncoding())
        await decoded.setReceiver(PrintReceiver())

    server.onConnection(handle_connection)
    assert await server.start()

    # The server starts on port 0, so we set the real port before connecting.
    port = await server.waitForPort()

    connect = await make_connect(port)
    reconnection = ReconnectingConnection(connect, retryInterval=0.1)
    reconnection.start()

    # Send through the reconnection wrapper.
    message = Message.tree(SampleTree.ofValue(Value(42)), Path.of("data"))
    reconnection.send(message)

    await asyncio.sleep(0.3)

    reconnection.stop()
    assert await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
```
```python
#--Output--#
Server received [data] = 42
```

---

