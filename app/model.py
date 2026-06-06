from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from sqlalchemy import Integer, VARCHAR, Text, Column, ForeignKey, REAL, UUID, TIMESTAMP, PrimaryKeyConstraint

Base = declarative_base()

class Event(Base):

    __tablename__ = "event"

    id = Column(Integer, primary_key=True)
    name = Column(VARCHAR(255))
    description = Column(VARCHAR(255))


class Tickets(Base):
    
    __tablename__ = "tickets"

    id = Column(Integer, nullable=False, primary_key=True)
    eventid = Column(Integer, ForeignKey("event.id"), primary_key=True)
    seat = Column(VARCHAR)
    price = Column(REAL)
    status = Column(VARCHAR, default='AVAILABLE')
    userid = Column(UUID)
    expires_at = Column(TIMESTAMP)
