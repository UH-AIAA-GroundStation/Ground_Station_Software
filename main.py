from fastapi import FastAPI
from sensor_reader import Sensor_reader

app = FastAPI()


@app.get("/read_data")
async def root():
    return {"altitude": {},
            "temperature": {},
            "gps":{},
            "lcd":{}
            }