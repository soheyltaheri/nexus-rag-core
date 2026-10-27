from pydantic import BaseModel


class ComponentStatus(BaseModel):
    status: str
    latency_ms: float | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    environment: str
    database: ComponentStatus
    redis: ComponentStatus
    version: str
