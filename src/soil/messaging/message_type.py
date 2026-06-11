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