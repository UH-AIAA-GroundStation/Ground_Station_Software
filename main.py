from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sensor_reader import Sensor_reader
import threading
import time

app = FastAPI()

DataStream = Sensor_reader()

DataStream._setup_serial()


# Background task to keep the data flowing
def background_reader():
    while True:
        DataStream._tick()
        time.sleep(0.01) # Small sleep to save CPU

threading.Thread(target=background_reader, daemon=True).start()
# Allow your Web App (Frontend) to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace "*" with your app's URL
    allow_methods=["*"],
)


@app.get("/read_data")
async def root():
    return {
        "altitude": {
            "values": DataStream.altitude_data[-20:], # Send last 20 points
            "timestamps": DataStream.alt_time_data[-20:]
        },
        "temperature": DataStream.temp_data[-1:] if DataStream.temp_data else 0,
        "gps": {
            "x": DataStream.x_data[-20:],
            "y": DataStream.y_data[-20:]
        }
    }