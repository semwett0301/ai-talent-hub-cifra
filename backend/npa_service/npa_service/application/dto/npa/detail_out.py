"""Current NPA state plus its immutable version history."""

from pydantic import Field

from npa_service.application.dto.npa.out import NpaOut
from npa_service.application.dto.npa.version_out import NpaVersionOut


class NpaDetailOut(NpaOut):
    versions: list[NpaVersionOut] = Field(default_factory=list)
