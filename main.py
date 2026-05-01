from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sensor_reader import Sensor_reader
import time

# from folder_name.file_name import class_or_function
from database.database import SessionLocal, Altitude, Temperature, GPS,SystemSettings



DataStream = Sensor_reader()
# Use a lifespan to manage the connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Open the port
    DataStream._setup_serial() 
    yield
    # Shutdown: Close the port
    DataStream.ser.close()

app = FastAPI(lifespan=lifespan)




# Allow your Web App (Frontend) to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"], # Allow your frontend
    allow_credentials=True,
    allow_methods=["*"], # Allows POST, GET, etc.
    allow_headers=["*"], # Allows all headers
)


@app.get("/read_data")
async def root():
    

    DataStream._tick()

    db = SessionLocal()

    # Save Altitude
    if DataStream.altitude_data:
        db.add(Altitude(
            time=DataStream.alt_time_data[-1], 
            measurement=DataStream.altitude_data[-1]
        ))

    # Save Temperature
    if DataStream.temp_data:
        db.add(Temperature(
            time=DataStream.temp_time_data[-1],
            measurement=DataStream.temp_data[-1]
        ))

    # Save GPS
    if DataStream.x_data:
        db.add(GPS(
            x_data=DataStream.x_data[-1], 
            y_data=DataStream.y_data[-1]
        ))

    db.commit()

    db.close()



    '''return {
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
    }'''
    return {
        "message":"Data Successfully read and added to DataBase"
    
    }

@app.get("/history")
async def get_history(limit: int = 200):
    """Consumption endpoint: All clients call this to update their graphs."""
    db = SessionLocal()
    try:
        # Query the latest rows from the database
        alt_rows = db.query(Altitude).order_by(Altitude.id.desc()).limit(limit).all()
        temp_rows = db.query(Temperature).order_by(Temperature.id.desc()).limit(limit).all()
        gps_rows = db.query(GPS).order_by(GPS.id.desc()).limit(limit).all()

        # Reverse the results so they appear in chronological order for D3 (left-to-right)
        return {
            "altitude": {"timestamps": [float(r.time) for r in alt_rows][::-1], 
                         "values": [float(r.measurement) for r in alt_rows][::-1]},
            "temperature": {"timestamps": [float(r.time) for r in temp_rows][::-1], 
                            "values": [float(r.measurement) for r in temp_rows][::-1]},
            "gps": {"x": [float(r.x_data) for r in gps_rows][::-1], 
                    "y": [float(r.y_data) for r in gps_rows][::-1]}
        }
    finally:
        db.close()


@app.post("/toggle_recording")
async def toggle_recording():
    # 1. Fetch the current status
    db = SessionLocal()
    status = db.query(SystemSettings).filter(SystemSettings.key == "is_recording").first()
    
    if not status:
        # Fallback if the row doesn't exist yet
        status = SystemSettings(key="is_recording", value=True)
        db.add(status)
    else:
        # 2. Flip the boolean (True becomes False, False becomes True)
        status.value = not status.value
    
    db.commit()
    db.refresh(status)
    
    return {"is_recording": status.value}


@app.post("/reset")
async def reset_sensor_data():
    """Clears both the local sensor arrays and the PostgreSQL database."""
    # 1. Clear local RAM arrays (from your existing sensor_reader.py logic)
    DataStream.reset_data()

    # 2. Clear the Database
    db = SessionLocal()
    try:
        # TRUNCATE is faster than DELETE for clearing entire tables
        # Using synchronize_session=False is efficient for bulk deletes
        db.query(Altitude).delete(synchronize_session=False)
        db.query(Temperature).delete(synchronize_session=False)
        db.query(GPS).delete(synchronize_session=False)
        
        db.commit()
        return {"message": "Local arrays and database tables cleared", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Database reset failed: {str(e)}", "status": "error"}
    finally:
        db.close()


