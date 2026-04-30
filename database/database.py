from sqlalchemy import create_engine, Column, Integer, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# Format: postgresql://user:password@host/database_name
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:142893@localhost/flight_data"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Altitude(Base):
    __tablename__ = "altitude"
    
    # primary_key=True tells SQLAlchemy this is your unique identifier
    id = Column(Integer, primary_key=True) 
    
    # Matches your numeric(10,2) columns
    time = Column(Numeric(10, 2)) 
    measurement = Column(Numeric(10, 2))

class Temperature(Base):
    __tablename__ = "temperature"
    
    # primary_key=True tells SQLAlchemy this is your unique identifier
    id = Column(Integer, primary_key=True) 
    
    # Matches your numeric(10,2) columns
    time = Column(Numeric(10, 2)) 
    measurement = Column(Numeric(10, 2))

class GPS(Base):
    __tablename__ = "gps"
    
    # primary_key=True tells SQLAlchemy this is your unique identifier
    id = Column(Integer, primary_key=True) 
    
    # Matches your numeric(10,2) columns
    x_data = Column(Numeric(10, 2)) 
    y_data = Column(Numeric(10, 2))