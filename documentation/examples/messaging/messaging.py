"""
Comprehensive Messaging Example

This example demonstrates SOIL-CORE-PYTHON's Message API with a realistic
messaging implementation that includes:

- `Message.value()` for sending single values
- `Message.samples()` for sending multiple samples
- `Message.tree()` for sending entire sample trees
- `Message.request()` for requesting history data
- `Message.include()` and `Message.exclude()` for subscription management
- `Message.delete()` and `Message.deleteRules()` for deletion requests
- `Message.acknowledge()` for response acknowledgements
- Complete round-trip message processing
- Comprehensive verification of message content
"""

from soil.data import Path, Sample, SampleTree, Timestamp, Value
from soil.messaging import Message, MessageType


def create_data_messages():
    """Demonstrate creating data messages with various content types."""
    print("=" * 60)
    print("1. DATA MESSAGES")
    print("=" * 60)

    # Single value message
    print("\n--- Single Value Message ---")
    msg = Message.value(
        value=Value(21.5),
        path=Path.of("weather", "temperature"),
    )
    print(msg)
    assert msg.type == MessageType.DATA
    assert msg.path == Path.of("weather", "temperature")
    assert msg.count is None
    assert msg.depth is None
    assert msg.id is None

    # Single value with timestamp and request ID
    print("\n--- Value with Timestamp and Request ID ---")
    ts = Timestamp.current()
    msg = Message.value(
        value=Value(22.3),
        path=Path.of("weather", "temperature"),
        timestamp=ts,
        request=42,
        totalMessages=5,
    )
    print(msg)
    assert msg.type == MessageType.DATA
    assert msg.id == 42
    assert msg.count == 5

    # Multiple samples message
    print("\n--- Multiple Samples Message ---")
    samples = [
        Sample(Value(20.1)),
        Sample(Value(21.5)),
        Sample(Value(22.8)),
    ]
    msg = Message.samples(
        samples=samples,
        path=Path.of("history", "temperature"),
        request=100,
        totalMessages=1,
    )
    print(msg)
    assert msg.type == MessageType.DATA
    assert len(msg.data.samples) == 3  # Samples stored at the tree root
    assert msg.id == 100

    # Complete sample tree message
    print("\n--- Complete Tree Message ---")
    tree = SampleTree()
    tree.childWithValue("temperature", Value(21.5))
    tree.childWithValue("humidity", Value(63))
    tree.childWithValue("pressure", Value(1013))

    msg = Message.tree(
        tree=tree,
        path=Path.of("weather", "station", "living_room"),
    )
    print(msg)
    assert msg.type == MessageType.DATA
    assert not msg.data.isEmpty
    assert "temperature" in str(msg.data)
    assert "humidity" in str(msg.data)
    assert "pressure" in str(msg.data)

    print("\nOK All data message types created successfully")


def create_request_messages():
    """Demonstrate creating request messages for history data."""
    print("\n" + "=" * 60)
    print("2. REQUEST MESSAGES")
    print("=" * 60)

    # Basic request
    print("\n--- Basic History Request ---")
    msg = Message.request(
        path=Path.of("weather", "temperature"),
    )
    print(msg)
    assert msg.type == MessageType.REQUEST
    assert msg.path == Path.of("weather", "temperature")

    # Request with time range
    print("\n--- Request with Time Range ---")
    start = Timestamp.fromTimeIntervalSince1970(1700000000)
    end = Timestamp.fromTimeIntervalSince1970(1700003600)

    msg = Message.request(
        path=Path.of("history", "temperature"),
        start=start,
        end=end,
    )
    print(msg)
    assert msg.type == MessageType.REQUEST
    assert msg.time == start
    assert msg.end == end

    # Request with limit and depth
    print("\n--- Request with Limit and Depth ---")
    msg = Message.request(
        path=Path.of("weather"),
        limit=100,
        depth=2,
        id=42,
    )
    print(msg)
    assert msg.type == MessageType.REQUEST
    assert msg.count == 100  # limit
    assert msg.depth == 2
    assert msg.id == 42

    # Complete request with all options
    print("\n--- Complete Request ---")
    msg = Message.request(
        path=Path.of("sensors", "Living Room"),
        start=start,
        end=end,
        limit=50,
        depth=3,
        id=999,
    )
    print(msg)
    assert msg.count == 50
    assert msg.depth == 3
    assert msg.id == 999

    print("\nOK All request message types created successfully")


def create_subscription_messages():
    """Demonstrate creating subscription messages for data filtering."""
    print("\n" + "=" * 60)
    print("3. SUBSCRIPTION MESSAGES")
    print("=" * 60)

    # Include subscription
    print("\n--- Include Subscription ---")
    msg = Message.include(
        path=Path.of("device"),
        depth=2,
    )
    print(msg)
    assert msg.type == MessageType.SUBSCRIPTION_INCLUSION
    assert msg.path == Path.of("device")
    assert msg.depth == 2

    # Include without depth (unlimited)
    print("\n--- Include Without Depth ---")
    msg = Message.include(
        path=Path.of("weather"),
    )
    print(msg)
    assert msg.type == MessageType.SUBSCRIPTION_INCLUSION
    assert msg.depth is None

    # Exclude subscription
    print("\n--- Exclude Subscription ---")
    msg = Message.exclude(
        path=Path.of("device", "power"),
        depth=1,
    )
    print(msg)
    assert msg.type == MessageType.SUBSCRIPTION_EXCLUSION
    assert msg.path == Path.of("device", "power")
    assert msg.depth == 1

    # Delete subscription rules
    print("\n--- Delete Subscription Rules ---")
    msg = Message.deleteRules(
        path=Path.of("weather"),
        depth=2,
    )
    print(msg)
    assert msg.type == MessageType.SUBSCRIPTION_DELETION
    assert msg.path == Path.of("weather")
    assert msg.depth == 2

    print("\nOK All subscription message types created successfully")


def create_deletion_messages():
    """Demonstrate creating deletion messages."""
    print("\n" + "=" * 60)
    print("4. DELETION MESSAGES")
    print("=" * 60)

    # Basic deletion
    print("\n--- Basic Deletion ---")
    msg = Message.delete(
        path=Path.of("old", "data"),
    )
    print(msg)
    assert msg.type == MessageType.DELETION
    assert msg.path == Path.of("old", "data")

    # Deletion with time range
    print("\n--- Deletion with Time Range ---")
    start = Timestamp.fromTimeIntervalSince1970(1699999999)
    end = Timestamp.fromTimeIntervalSince1970(1700003600)

    msg = Message.delete(
        path=Path.of("weather", "temperature"),
        start=start,
        end=end,
        depth=1,
        id=123,
    )
    print(msg)
    assert msg.type == MessageType.DELETION
    assert msg.time == start
    assert msg.end == end
    assert msg.depth == 1
    assert msg.id == 123

    print("\nOK Deletion message created successfully")


def create_acknowledgement_messages():
    """Demonstrate creating acknowledgement messages."""
    print("\n" + "=" * 60)
    print("5. ACKNOWLEDGEMENT MESSAGES")
    print("=" * 60)

    # Basic acknowledge
    print("\n--- Basic Acknowledgement ---")
    msg = Message.acknowledge(
        request=42,
        path=Path.of("weather", "temperature"),
    )
    print(msg)
    assert msg.type == MessageType.DATA
    assert msg.id == 42
    assert msg.path == Path.of("weather", "temperature")

    # Acknowledge with timestamp
    print("\n--- Acknowledgement with Timestamp ---")
    ts = Timestamp.current()
    msg = Message.acknowledge(
        request=99,
        path=Path.of("sensors", "Living Room"),
        timestamp=ts,
    )
    print(msg)
    assert msg.type == MessageType.DATA
    assert msg.id == 99
    assert msg.time == ts

    print("\nOK Acknowledgement messages created successfully")


def test_message_equality():
    """Demonstrate message equality comparisons."""
    print("\n" + "=" * 60)
    print("6. MESSAGE EQUALITY")
    print("=" * 60)

    # Equal messages
    print("\n--- Equal Messages ---")
    a = Message.include(Path.of("device"), depth=2)
    b = Message.include(Path.of("device"), depth=2)
    print(f"Message A: {a.type} on {a.path}")
    print(f"Message B: {b.type} on {b.path}")
    assert a == b
    print("OK Messages are equal")

    # Different types
    print("\n--- Different Types ---")
    a = Message.include(Path.of("device"))
    b = Message.exclude(Path.of("device"))
    assert a != b
    print("OK Different message types are not equal")

    # Different paths
    print("\n--- Different Paths ---")
    a = Message.include(Path.of("device", "temperature"))
    b = Message.include(Path.of("device", "humidity"))
    assert a != b
    print("OK Different paths are not equal")

    # Different timestamps
    print("\n--- Different Timestamps ---")
    ts1 = Timestamp.fromTimeIntervalSince1970(1700000000)
    ts2 = Timestamp.fromTimeIntervalSince1970(1700000001)
    a = Message.request(Path.of("data"), start=ts1)
    b = Message.request(Path.of("data"), start=ts2)
    assert a != b
    print("OK Different timestamps are not equal")

    # Tolerant timestamp comparison (within 1ms)
    print("\n--- Timestamp Tolerance (within 1ms) ---")
    ts1 = Timestamp.fromTimeIntervalSince1970(1700000000)
    ts2 = Timestamp.fromTimeIntervalSince1970(1700000000.0005)  # 0.5ms difference
    a = Message.request(Path.of("data"), start=ts1)
    b = Message.request(Path.of("data"), start=ts2)
    assert a == b
    print("OK Timestamps within 1ms tolerance are equal")

    print("\nOK All equality comparisons work correctly")


def test_message_string_representation():
    """Demonstrate message string formatting."""
    print("\n" + "=" * 60)
    print("7. STRING REPRESENTATION")
    print("=" * 60)

    # Request with all fields
    print("\n--- Complete Message String ---")
    ts = Timestamp.fromTimeIntervalSince1970(1700000000)
    msg = Message.request(
        path=Path.of("weather", "temperature"),
        start=ts,
        end=Timestamp.fromTimeIntervalSince1970(1700003600),
        limit=100,
        depth=2,
        id=42,
    )
    print(msg)

    # Empty/default message
    print("\n--- Default Message String ---")
    msg = Message()
    print(msg)
    assert "type: data" in str(msg)
    assert "path:" not in str(msg)  # Empty path is omitted

    # Message with data
    print("\n--- Message with Data ---")
    msg = Message.value(Value(42), Path.of("test"))
    print(msg)
    assert "data:" in str(msg)

    print("\nOK String representation works correctly")


def message_processing_workflow():
    """Demonstrate a complete message processing workflow."""
    print("\n" + "=" * 60)
    print("8. COMPLETE WORKFLOW")
    print("=" * 60)

    class SimpleHub:
        """A simplified message hub for demonstration."""

        def __init__(self):
            self.data = SampleTree()
            self.subscriptions: list[Path] = []
            self.responses: list[Message] = []

        def send(self, message: Message) -> None:
            """Send a message and collect responses."""
            response = None

            match message.type:
                case MessageType.DATA:
                    # Merge data into our store
                    self.data.mergeAtPath(message.data, message.path)
                    if message.id is not None:
                        response = Message.acknowledge(
                            request=message.id,
                            path=message.path,
                        )

                case MessageType.REQUEST:
                    # Find data at the requested path
                    node = self.data.existingNode(message.path)
                    if node:
                        samples = node.getSamples(
                            message.time,
                            message.end,
                            message.count,
                        )
                    else:
                        samples = []

                    response = Message.samples(
                        samples,
                        message.path,
                        request=message.id,
                        totalMessages=1,
                    )

                case MessageType.SUBSCRIPTION_INCLUSION:
                    self.subscriptions.append(message.path)

                case MessageType.SUBSCRIPTION_EXCLUSION:
                    self.subscriptions = [
                        p for p in self.subscriptions
                        if not p.hasPrefix(message.path)
                    ]

            if response:
                self.responses.append(response)

        def print_state(self) -> None:
            print("Stored Data:")
            print(self.data)
            print(f"\nSubscriptions ({len(self.subscriptions)}):")
            for sub in self.subscriptions:
                print(f"  - {sub}")
            print(f"\nResponses ({len(self.responses)}):")
            for resp in self.responses:
                print(f"  {resp.type} for {resp.path}")

    # Create hub and process messages
    hub = SimpleHub()

    # Send some data. Each carries a `request` id so the hub replies with an ack.
    print("\n--- Sending Temperature Data ---")
    hub.send(Message.value(Value(21.5), Path.of("weather", "temperature"), request=1))
    hub.send(Message.value(Value(22.8), Path.of("weather", "temperature"), request=2))

    # Send humidity data
    print("\n--- Sending Humidity Data ---")
    hub.send(Message.value(Value(63), Path.of("weather", "humidity"), request=3))

    # Request the data
    print("\n--- Requesting Temperature History ---")
    hub.send(Message.request(
        Path.of("weather", "temperature"),
        limit=10,
        id=1,
    ))

    # Set up subscriptions
    print("\n--- Setting Up Subscriptions ---")
    hub.send(Message.include(Path.of("weather")))
    hub.send(Message.exclude(Path.of("weather", "humidity")))

    # Print final state
    print("\n" + "-" * 40)
    hub.print_state()

    # Verify results. The nested paths `weather > temperature` and
    # `weather > humidity` collapse into a single top-level node `weather`,
    # so the store holds one child node. The three data messages each carry a
    # `request` id, so the hub answers each with an ack, plus one reply to the
    # request message: four responses in total.
    assert len(hub.data.children) == 1  # just the `weather` node
    assert len(hub.subscriptions) == 1  # Only weather (humidity was excluded)
    assert len(hub.responses) == 4  # 3 acks + 1 request reply

    print("\nOK Complete workflow executed successfully")


def main():
    """Run all messaging examples."""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE MESSAGING EXAMPLE")
    print("=" * 60)
    print("\nThis example demonstrates the SOIL-CORE-PYTHON Message API")
    print("with various message types and use cases.")

    create_data_messages()
    create_request_messages()
    create_subscription_messages()
    create_deletion_messages()
    create_acknowledgement_messages()
    test_message_equality()
    test_message_string_representation()
    message_processing_workflow()

    print("\n" + "=" * 60)
    print("ALL MESSAGING EXAMPLES COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()