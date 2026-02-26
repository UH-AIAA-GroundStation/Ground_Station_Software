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
            "values": DataStream.altitude_data, # Send last 20 points
            "timestamps": DataStream.alt_time_data
        },
        "temperature":{
            "values": DataStream.temp_data if DataStream.temp_data else 0,
            "timestamps": DataStream.temp_time_data
        }, 
        "gps": {
            "x": DataStream.x_data,
            "y": DataStream.y_data
        }
    }

@app.post("/reset")
async def reset_sensor_data():
    """Trigger a reset of all sensor arrays and timers."""
    DataStream.reset_data()
    return {"message": "All data arrays have been cleared", "status": "success"}


