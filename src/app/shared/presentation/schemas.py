"""Base Pydantic model for HTTP request/response schemas.

Pydantic lives here and in `application/read_models.py` only — never in
`domain/`. See `app/shared/domain/entity.py` for why.
"""

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
