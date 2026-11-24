# SOIL Python Examples

Runnable examples that show how the SOIL core library works.
Each example lives under a folder that matches its topic and can be run on its own.

## Requirements

- Python 3.12 or newer
- The project installed in development mode (see the root `Readme.md`)
  so that `import soil` works, and the dependencies from `uv.lock` are installed.

## Running an example

Every example is a self-contained script. Run it directly:

```bash
python documentation/examples/<folder>/<name>.py
```

For example:

```bash
python documentation/examples/data/weather_station.py
```

## Example list

### `data/` — the data model

| Example | Shows |
|---------|-------|
| [`weather_station.py`](data/weather_station.py) | `SampleTreeConvertible` with location, humidity, and history. |
| [`library.py`](data/library.py) | `ValueConvertible` for a simple record plus a visitor-count history. |
| [`device_management.py`](data/device_management.py) | Map- and list-valued specs (sensors, power). |

### `messaging/` — the message API

| Example | Shows |
|---------|-------|
| [`messaging.py`](messaging.py) | Every `Message` factory, message equality, and a full hub workflow. |

### `networking/` — real end-to-end connections

| Example | Shows |
|---------|-------|
| [`pattern_request_response.py`](networking/pattern_request_response.py) | Request/response over TCP. |
| [`pattern_udp_tm.py`](networking/pattern_udp_tm.py) | Telemetry streaming over UDP. |
| [`pattern_pub_sub.py`](networking/pattern_pub_sub.py) | Pub/Sub with observable subscriptions. |
| [`pattern_remote_storage.py`](networking/pattern_remote_storage.py) | Remote storage access over TCP. |
| [`pattern_reconnection.py`](networking/pattern_reconnection.py) | Auto-reconnect after failures. |

### `components/` — component patterns

| Example | Shows |
|---------|-------|
| [`storage_component.py`](components/storage_component.py) | `InMemoryStorage`: store, read, and delete through the storage interface. |
| [`observable_component.py`](components/observable_component.py) | The `Observable` pattern: forward only subscribed data to receivers. |

## Note on the library

These examples run against the current API. They import the project
(`import soil`); make sure the project and its dependencies are installed
before running them.
