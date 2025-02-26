from pydantic import BaseModel


class AccelerationNumbers(BaseModel):
    x: float
    y: float
    z: float
    m: int

class TotalAcceleration(BaseModel):
    accTotal: float