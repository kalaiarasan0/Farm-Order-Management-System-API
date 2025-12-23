from sqlalchemy import Column, Integer, String, Date, Enum, Float, ForeignKey
from sqlalchemy.sql import func
from app.db import TrackingBase
import enum

class AnimalSource(enum.Enum):
    birth = "birth"
    purchase = "purchase"

class AnimalStatus(enum.Enum):
    alive = "alive"
    sold = "sold"
    dead = "dead"
    transferred = "transferred"

class Animal(TrackingBase):
    __tablename__ = "animals"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }


    id = Column(Integer, primary_key=True, index=True)
    tag_id = Column(String(50), unique=True, index=True)  # ear tag / QR
    species = Column(String(50))  # cow, goat, sheep
    breed = Column(String(50))
    gender = Column(String(10))
    birth_date = Column(Date, nullable=True)
    source = Column(Enum(AnimalSource))
    source_reference = Column(String(100))  # vendor / mother id
    purchase_price = Column(Float, nullable=True)

    status = Column(Enum(AnimalStatus), default=AnimalStatus.alive)
    created_at = Column(Date, server_default=func.current_date())


class AnimalEvent(TrackingBase):
    __tablename__ = "animal_events"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True)
    animal_id = Column(Integer, ForeignKey("animals.id"), nullable=False,index=True)
    event_type = Column(String(50))  # vaccination, weight_check, sale
    event_date = Column(Date)
    notes = Column(String(255))
