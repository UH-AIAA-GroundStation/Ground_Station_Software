from pydantic import BaseModel
from typing import List

class altitude_stream(BaseModel):
    a_values: List[float]      # Altitide readings
    a_timestamps: List[str]    # Time of readings

class temperature_stream(BaseModel):
    t_values: List[float]      # Temperature readings
    t_timestamps: List[str]    # Time of readings

class gps_stream(BaseModel):
    g_x: List[float]  # X coords
    g_y: List[str]    # Y coords


class data(BaseModel):  # combines the data streams
    altitude: altitude_stream
    temperature: temperature_stream
    gps: gps_stream