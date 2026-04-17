from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

DATABASE_URL = "sqlite:///./aqi_details.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class LiveQuery(Base):
    __tablename__ = "live_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    lat = Column(Float, index=True)
    lon = Column(Float, index=True)
    current_aqi = Column(Float)
    current_pm10 = Column(Float)
    current_pm2_5 = Column(Float)
    current_no2 = Column(Float)
    
# Note: historical_aqi table will be created automatically by pandas to_sql
# but we can optionally define it here for schema consistency.
class HistoricalAQI(Base):
    __tablename__ = "historical_aqi"
    
    id = Column(Integer, primary_key=True, index=True)
    time = Column(DateTime, index=True)
    us_aqi = Column(Float)
    lat = Column(Float, index=True)
    lon = Column(Float, index=True)

Base.metadata.create_all(bind=engine)
