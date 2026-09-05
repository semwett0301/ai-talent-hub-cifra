"""HttpNpaGateway — NpaGateway over npa_service's HTTP API (httpx)."""

import uuid

import httpx
from domain.core.logging import get_logger
from domain.entities.npa import NpaDTO

from news_service.application.errors import NpaConflictError, NpaGatewayError
from news_service.application.ports import NpaGateway

# npa_service mounts its create endpoint at the root of its own API.
CREATE_PATH = "/"
REQUEST_TIMEOUT_SECONDS = 10.0

logger = get_logger(__name__)


class HttpNpaGateway(NpaGateway):
    def __init__(self, base_url: str) -> None:
        self.__base_url = base_url

    async def create(self, act: NpaDTO) -> uuid.UUID:
        payload = act.model_dump(mode="json")

        try:
            async with httpx.AsyncClient(
                base_url=self.__base_url, timeout=REQUEST_TIMEOUT_SECONDS
            ) as client:
                response = await client.post(CREATE_PATH, json=payload)
        except httpx.HTTPError as error:
            logger.warning("npa create failed: url=%s error=%s", act.url, error)
            raise NpaGatewayError(f"npa_service unreachable: {error}") from error

        return self.__created_id(response, act)

    def __created_id(self, response: httpx.Response, act: NpaDTO) -> uuid.UUID:
        """The new act's id from a 201; a 409 or any other error is raised as its port error."""
        if response.status_code == httpx.codes.CONFLICT:
            logger.warning("npa create refused: url=%s (already exists)", act.url)
            raise NpaConflictError(str(act.url))

        if response.is_error:
            logger.warning("npa create failed: url=%s status=%s", act.url, response.status_code)
            raise NpaGatewayError(f"npa_service replied {response.status_code}")

        return uuid.UUID(response.json()["id"])
