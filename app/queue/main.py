import asyncio
import uuid
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from ..middlewares.ratelimiter import RateLimiter
from ..middlewares.booking import BookingMiddleware
from ..middlewares.auth import AuthMiddleware, get_current_user_id, create_token
from ..config.redis import r
from ..config.db import session
from ..model import Event, Tickets

load_dotenv()

q = "VirtualQueue"

# Request Models
class JoinRequest(BaseModel):
    name: str

class UpdateRequest(BaseModel):
    offset: int

class Book(BaseModel):
    eventID: int
    seatID: int

class UpdateNameRequest(BaseModel):
    name: str

app = FastAPI()

app.add_middleware(RateLimiter)
app.add_middleware(AuthMiddleware)

@app.middleware("http")
async def booking_http_middleware(request: Request, call_next):
    return await BookingMiddleware(request, call_next)


# Dependency Injection for DB session
def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()


# Endpoints

# Queue endpoints
@app.post('/queue/join')
async def start(req: Request, join_req: JoinRequest):
    user_id = req.state.user_id
    score = datetime.now().timestamp()

    await r.zadd(q, {user_id: score}) # Add to the sorted set
    
    token = create_token(user_id, join_req.name)
    response = Response(content='{"msg": "Inserted Successfully", "user_id": "' + user_id + '"}', media_type="application/json")
    response.set_cookie(
        key="session_token",
        value=token,
        max_age=60 * 60 * 24 * 7, # 7 days, more than enough
        httponly=True,
    )
    return response


@app.get('/queue/ranks')
async def ranks():

    # Returns the ranks from the virtual queue
    res = await r.zrange(q, 0, -1, withscores=True)
    return {"response": res}


@app.get('/queue/getrank')
async def get_rank(req: Request):
    try:
        user_id = req.state.user_id
        rank = await r.zrank(q, user_id)

        if rank is None:
            return {"message": "You aren't in the queue!!"}

        res = await r.hget(f'user:{user_id}', 'IP')

        if res is not None:
            return {"message": "Should be redirected to Arena"}

    except Exception as e:
        print("Exception occured!!")
        print(e)

    return {"rank": rank, "result": res}

# Dev endpoint 
@app.post('/queue/update')
async def update(req: UpdateRequest):
    val = req.offset
    await r.zremrangebyrank(q, 0, max(val-1, 0))
    res = await r.zrange(q, 0, -1, withscores=True)
    return {"response": res}

# Dev endpoint
@app.get('/queue/arenausers')
async def get_arenausers():
    res = await r.keys("user*")
    return {"users": res}


# Booking endpoints

@app.post("/booking/reserve-seat/")
async def reserve_seat(req: Book, request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user_id
    try:
        res = db.query(Tickets).filter(
                    Tickets.id == req.seatID,
                    Tickets.eventid == req.eventID,
                    Tickets.status == "AVAILABLE"
                ).update({
                    Tickets.status: "RESERVED",
                    Tickets.userid: uuid.UUID(user_id),
                    Tickets.expires_at: datetime.now() + timedelta(minutes=5),
                })
        db.commit()

        if res == 1:
            return Response(content="Successful Reservation")
        else:
            return Response(content="Unsuccessful Reservation", status_code=400)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/booking/getseats/{eventID}")
async def getSeatsForEventId(eventID: int, db: Session = Depends(get_db)):
    try:
        res = db.query(Tickets).filter(
                Tickets.eventid == eventID
            ).all()
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/booking/book")
async def bookseat(req: Book, request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user_id
    try:
        res = db.query(Tickets).filter(
                    Tickets.id == req.seatID,
                    Tickets.eventid == req.eventID,
                    Tickets.status == "RESERVED",
                    Tickets.userid == uuid.UUID(user_id)
                ).update({
                    Tickets.status: "BOOKED"
                })
        db.commit()

        if res == 1:
            return Response(content="Booked and Updated Successful")
        else:
            return Response(content="Unsuccessful Booking!", status_code=400)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events")
async def get_events(req: Request, db: Session = Depends(get_db)):
    try:
        res = db.query(Event).all()
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))