from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sensor_reader import Sensor_reader
import time


DataStream = Sensor_reader()
# Use a lifespan to manage the connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Open the port
    #DataStream._setup_serial() 
    yield
    # Shutdown: Close the port
    DataStream.ser.close()

app = FastAPI(lifespan=lifespan)


# Background task to keep the data flowing
def background_reader():
    while True:
        DataStream._tick()
        time.sleep(0.01) # Small sleep to save CPU

# Allow your Web App (Frontend) to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace "*" with your app's URL
    allow_methods=["*"],
)


@app.get("/read_data")
async def root():
    DataStream._tick()
    return {
        "altitude": {
            "values": DataStream.altitude_data[-20:], # Send last 20 points
            "timestamps": DataStream.alt_time_data[-20:]
        },
        "temperature":{
            "values": DataStream.temp_data[-1:] if DataStream.temp_data else 0,
            "timestamps": DataStream.temp_time_data[-20:]
        }, 
        "gps": {
            "x": DataStream.x_data[-20:],
            "y": DataStream.y_data[-20:]
        }
    }