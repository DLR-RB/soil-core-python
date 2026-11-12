from datetime import datetime

from soil.data import SampleTree, SampleTreeConvertible, Value, ValueConvertible


class SensorValue(ValueConvertible):
    """
    A sensor value with a numeric reading and a unit.

    This demonstrates `ValueConvertible` for a heterogeneous data type
    that needs to preserve both the value and its unit of measurement.
    """

    def __init__(self, value: float, unit: str):
        self._value = float(value)
        self._unit = unit

    @property
    def value(self) -> float:
        return self._value

    @property
    def unit(self) -> str:
        return self._unit

    def toValue(self) -> Value:
        """Convert to a map-Value with 'value' and 'unit' keys."""
        return Value({
            "value": Value(self._value),
            "unit":  Value(self._unit),
        })

    @classmethod
    def fromValue(cls, value: Value) -> "SensorValue":
        """Create from a map-Value."""
        raw = value.value
        if not isinstance(raw, dict):
            raise ValueError("Value must be a map with 'value' and 'unit' keys")

        val = raw.get("value")
        unit = raw.get("unit")
        if not isinstance(val, Value) or not isinstance(unit, Value):
            raise ValueError("Value must contain Value instances")

        return cls(float(val.value), str(unit.value))


class Location(ValueConvertible):
    """
    Geographic location with latitude, longitude, and altitude.

    Demonstrates nested map structures and type safety.
    """

    def __init__(self, city: str, latitude: float, longitude: float, altitude_m: int | None = None):
        self._city = city
        self._latitude = float(latitude)
        self._longitude = float(longitude)
        self._altitude_m = altitude_m

    @property
    def city(self) -> str:
        return self._city

    @property
    def latitude(self) -> float:
        return self._latitude

    @property
    def longitude(self) -> float:
        return self._longitude

    @property
    def altitude_m(self) -> int | None:
        return self._altitude_m

    def toValue(self) -> Value:
        """Convert to a nested map-Value."""
        result: dict[str, Value] = {
            "city":     Value(self._city),
            "latitude": Value(self._latitude),
            "longitude": Value(self._longitude),
        }
        if self._altitude_m is not None:
            result["altitude_m"] = Value(self._altitude_m)
        return Value(result)

    @classmethod
    def fromValue(cls, value: Value) -> "Location":
        """Create from a nested map-Value."""
        raw = value.value
        if not isinstance(raw, dict):
            raise ValueError("Value must be a map with location data")

        city_val = raw.get("city")
        lat_val = raw.get("latitude")
        lon_val = raw.get("longitude")

        if not all(isinstance(v, Value) for v in (city_val, lat_val, lon_val)):
            raise ValueError("Location map must contain city, latitude, longitude as Values")

        altitude = None
        if "altitude_m" in raw:
            alt_val = raw["altitude_m"]
            if isinstance(alt_val, Value):
                altitude = int(alt_val.value)

        return cls(
            city=str(city_val.value),
            latitude=float(lat_val.value),
            longitude=float(lon_val.value),
            altitude_m=altitude,
        )


class WeatherStation(SampleTreeConvertible):
    """
    A weather station that monitors multiple environmental sensors.

    This demonstrates:
    - `SampleTreeConvertible` for hierarchical data
    - Multiple sensor types stored in a history tree
    - Location metadata as a nested SampleTree
    - Historical tracking with multiple samples per sensor
    """

    def __init__(self, name: str, location: SampleTree):
        self._name = name
        self._location = location
        self._history = SampleTree()

    @property
    def name(self) -> str:
        return self._name

    @property
    def location(self) -> SampleTree:
        return self._location

    @property
    def history(self) -> SampleTree:
        return self._history

    def record_temperature(self, celsius: float, timestamp: datetime | None = None) -> None:
        """Record a temperature reading with optional custom timestamp."""
        reading = SensorValue(celsius, "C")
        sample = Value(reading.toValue())
        if timestamp:
            from soil.data import Sample, Timestamp
            self._history.add(Sample(sample, Timestamp(timestamp)), "temperature")
        else:
            self._history.childWithValue("temperature", sample)

    def record_humidity(self, relative_humidity: float) -> None:
        """Record a humidity reading (percentage)."""
        reading = SensorValue(relative_humidity, "%")
        self._history.childWithValue("humidity", Value(reading.toValue()))

    def record_pressure(self, hpa: float) -> None:
        """Record atmospheric pressure in hectopascals."""
        reading = SensorValue(hpa, "hPa")
        self._history.childWithValue("pressure", Value(reading.toValue()))

    def record_wind(self, speed_kmh: float, direction_deg: int) -> None:
        """
        Record wind data with speed and direction.

        Direction is stored as degrees (0-360), where 0 = North.
        """
        reading = SensorValue(speed_kmh, "km/h")
        self._history.childWithValue("wind_speed", Value(reading.toValue()))
        self._history.childWithValue("wind_direction", Value(direction_deg))

    def record_precipitation(self, mm: float) -> None:
        """Record precipitation in millimeters."""
        reading = SensorValue(mm, "mm")
        self._history.childWithValue("precipitation", Value(reading.toValue()))

    def get_latest_temperature(self) -> SensorValue | None:
        """Get the most recent temperature reading."""
        return self._get_latest_sensor_value("temperature")

    def get_latest_humidity(self) -> SensorValue | None:
        """Get the most recent humidity reading."""
        return self._get_latest_sensor_value("humidity")

    def get_latest_pressure(self) -> SensorValue | None:
        """Get the most recent pressure reading."""
        return self._get_latest_sensor_value("pressure")

    def _get_latest_sensor_value(self, sensor_name: str) -> SensorValue | None:
        """Helper to extract a SensorValue from history."""
        node = self._history.existingChild(sensor_name)
        if node is None or node.newestSample is None:
            return None
        value = node.newestSample.value
        if value is None:
            return None
        return SensorValue.fromValue(value.value)

    def toTree(self) -> SampleTree:
        """Convert the weather station to a SampleTree."""
        tree = SampleTree()

        # Store station name
        tree.childWithValue("name", Value(self._name))

        # Store location as a nested SampleTree
        tree.add(self._location, "location")

        # Add the history tree
        tree.add(self._history, "history")

        return tree

    @classmethod
    def fromTree(cls, tree: SampleTree) -> "WeatherStation":
        """Reconstruct a WeatherStation from a SampleTree."""
        # Extract name
        name_node = tree.existingChild("name")
        if name_node is None or name_node.newestSample is None:
            raise ValueError("Tree missing 'name' in root")
        name = str(name_node.newestSample.value.value)

        # Extract location (it's a SampleTree, not a Value)
        location_node = tree.existingChild("location")
        if location_node is None:
            raise ValueError("Tree missing 'location' node")

        # Extract history
        history_node = tree.existingChild("history")
        if history_node is None:
            raise ValueError("Tree missing 'history' node")

        # Create station with location node (it will be used as the location tree)
        station = cls(name, location_node)
        station._history = history_node

        return station


def visualize(tree: SampleTree, indent: str = "", max_depth: int = -1, current_depth: int = 0) -> None:
    """
    Display a tree structure with proper formatting.

    Shows:
    - Map values with indented key-value pairs
    - List values with bracket notation
    - Multiple samples with timestamps
    - Current value markers
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
        # Map: show first few keys
        if len(raw) == 0:
            return "{}"
        keys = list(raw.keys())[:3]
        if len(raw) > 3:
            return f"{{{', '.join(keys)}...}}"
        return f"{{{', '.join(keys)}}}"
    elif isinstance(raw, list):
        # List: show count
        if len(raw) == 0:
            return "[]"
        return f"[{len(raw)} items]"
    else:
        # Primitive: show raw value
        return str(raw)


def main():
    """Demonstrate the WeatherStation class."""
    print("=" * 60)
    print("Weather Station Example")
    print("=" * 60)

    # Create a location SampleTree (like the original example)
    location = SampleTree()
    location.childWithValue("city", Value("Berlin"))
    location.childWithValue("lat", Value(52.52))
    location.childWithValue("lon", Value(13.405))
    location.childWithValue("altitude_m", Value(34))

    # Create a weather station
    station = WeatherStation("Berlin-Central", location)

    # Record multiple readings over time
    print("\nRecording weather readings...")
    station.record_temperature(21.5)
    station.record_humidity(63.0)
    station.record_pressure(1013.25)

    # Record more readings (simulating time passing)
    import time
    time.sleep(0.1)  # Small delay to ensure different timestamps

    station.record_temperature(22.1)
    station.record_wind(12.5, 180)  # 12.5 km/h from South
    station.record_precipitation(0.0)

    time.sleep(0.1)
    station.record_temperature(23.8)
    station.record_humidity(60.5)
    station.record_pressure(1012.80)
    station.record_precipitation(1.5)

    # Serialize to tree
    print("\n" + "=" * 60)
    print("=== toTree() - Serialized Weather Station ===")
    tree = station.toTree()
    visualize(tree, max_depth=2)

    # Deserialize from tree
    print("\n" + "=" * 60)
    print("=== fromTree() - Restored Weather Station ===")
    restored = WeatherStation.fromTree(tree)

    print(f"Name:        {restored.name}")

    # Extract location values from the SampleTree
    print("Location:")
    for child_name, child in restored.location.children.items():
        sample = child.newestSample
        if sample and sample.value:
            print(f"  {child_name}: {sample.value.value}")

    # Show latest readings
    print("\nLatest Readings:")
    temp = restored.get_latest_temperature()
    if temp:
        print(f"  Temperature: {temp.value} deg{temp.unit}")

    humidity = restored.get_latest_humidity()
    if humidity:
        print(f"  Humidity:    {humidity.value}%")

    pressure = restored.get_latest_pressure()
    if pressure:
        print(f"  Pressure:    {pressure.value} {pressure.unit}")

if __name__ == "__main__":
    main()