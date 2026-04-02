from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sensor_reader import Sensor_reader
import time

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from DataBase.schema import read_data,list_serial
from DataBase.models import data


uri = "mongodb://localhost:27017/"
client  = MongoClient(uri, server_api = ServerApi('1'))
db = client.Ground_station

collection = db["gound_station_data"]


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

router = APIRouter()

app.include_router(router)


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


@router.get("/read_data")
async def read_all_data():
    try:
        # collection.find() gets EVERY document in the 'ground_station_data' collection
        # We sort by _id (1) to ensure the timeline goes from start of flight to end
        cursor = collection.find()
        
        # Convert the cursor into a clean list of dictionaries
        full_dataset = list_serial(cursor)
        
        return full_dataset
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve full dataset: {e}")


@router.post("/post_data")
async def post_to_db():
    try:
        DataStream._tick()
        
        # Build the payload from your DataStream object
        new_entry = {
            "altitude": {
                "values": DataStream.altitude_data,
                "timestamps": DataStream.alt_time_data
            },
            "temperature": {
                "values": DataStream.temp_data if DataStream.temp_data else [],
                "timestamps": DataStream.temp_time_data
            },
            "gps": {
                "x": DataStream.x_data,
                "y": DataStream.y_data
            },

        }
        
        result = collection.insert_one(new_entry)
        return {"status": "success", "id": str(result.inserted_id)}
    except Exception as e:
        # Note: Detail must be a string, not a set/dict
        raise HTTPException(status_code=500, detail=f"Error: {e}")
"""
@app.post("/reset")
async def reset_sensor_data():
    #Trigger a reset of all sensor arrays and timers.
    DataStream.reset_data()
    return {"message": "All data arrays have been cleared", "status": "success"}
"""

