from typing import List, Optional

from pydantic import BaseModel, Field


class ModelDetails(BaseModel):
    format: Optional[str] = None
    family: Optional[str] = None
    families: Optional[List[str]] = None
    parameter_size: Optional[str] = None
    quantization_level: Optional[str] = None


class ModelInfo(BaseModel):
    name: str
    modified_at: Optional[str] = None
    size: Optional[int] = None
    digest: Optional[str] = None
    details: Optional[ModelDetails] = None


class ModelListResponse(BaseModel):
    models: List[ModelInfo]


class ModelPullRequest(BaseModel):
    name: str = Field(..., description="Model name to pull, e.g. 'llama3' or 'codellama:7b'")
    insecure: bool = Field(False, description="Allow insecure connections when pulling")


class ModelPullResponse(BaseModel):
    status: str
    detail: Optional[str] = None


class ModelDeleteResponse(BaseModel):
    status: str
