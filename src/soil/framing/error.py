from enum import Enum


class FramingError(Exception):
    """
    An error occurring during framing of a message for the stream.
    """

    class Code(Enum):
        """
        Error codes reported by the framing implementation.
        """

        # The message is too large to fit in a frame.
        payloadTooLarge = "payloadTooLarge"

    def __init__(self, code: "FramingError.Code"):
        self.code = code
        super().__init__(str(code.value))
