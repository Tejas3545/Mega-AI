from pydantic import BaseModel, ConfigDict


class ROIOut(BaseModel):
    id: int
    stream_id: str
    frame_number: int
    x: int
    y: int
    width: int
    height: int
    confidence: float
    timestamp_ms: int

    model_config = ConfigDict(from_attributes=True)
