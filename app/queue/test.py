import asyncio
import asyncpg
from ..config.db import engine, session
from ..model import Event, Tickets

def add_data():

    db = session()
    db.add(Tickets(id=102, eventid = 101, seat='west-tier', price = 5000))
    db.commit()


def fetch_data():

    db = session()
    res = db.query(Event).all()
    for row in res:
        print(row.id, row.name, row.description)


# fetch_data()

add_data()