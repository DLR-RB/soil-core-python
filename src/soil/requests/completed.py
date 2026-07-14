from typing import Any, Generator, override
from .request import Request

class CompletedRequest(Request):
    """ A request that is already completed """

    def __init__(self) -> None:
        pass

    @override
    async def wait(self) -> None:
        pass

    @override
    def __await__(self) -> Generator[Any, Any, None]:
        if False:
            yield
        return None
