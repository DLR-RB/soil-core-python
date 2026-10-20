from soil.data import Path, SampleTree, Timestamp, Value
from soil.messaging import Message, MessageType


class WeatherHub:
    """ A component that receives messages, stores data and answers requests. """

    def __init__(self):
        self.data: SampleTree = SampleTree()        # all received data
        self.subscriptions: list[Path] = list()     # included subscription paths
        self.outbox: list[Message] = list()         # responses to incoming messages


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

    print("\n=== Outbox ===")
    for message in hub.outbox:
        print(message, end="\n---\n")

if __name__ == "__main__":
    main()