

from .sync import SyncByteLengthFraming


class LoggingFraming(SyncByteLengthFraming):
    """
    Framing, das die übertragenen Bytes ins Log schreibt. (für TCP-Debugging)
    """
    async def encodeForStream(self, message: bytes) -> bytes:
        framed = await super().encodeForStream(message)
        print(f"Sende Bytes: {framed.hex()}")
        return framed

    async def processStreamBytes(self, data: bytes) -> list[bytes]:
        payloads = await super().processStreamBytes(data)
        for payload in payloads:
            print(f"Empfangene Payload: {payload.hex()}")
        return payloads
