# VirtualQ-Engine

A virtual queue and event ticketing system built with FastAPI, Redis, and PostgreSQL. The system is designed to manage queue admission, arena access, seat reservation, and booking while preventing race conditions and keeping hot-path operations fast.

## Overview

The application separates queue state from persistent booking state.

- Redis holds the live queue and per-user arena metadata.
- PostgreSQL stores event definitions and ticket state.
- A background worker moves users from queue to arena on a fixed schedule.
- Middleware enforces arena access before booking operations.

## Getting Started

1. Copy `.env.example` to `.env` and configure PostgreSQL and Redis.
2. Start Redis and PostgreSQL with Docker:
   - `docker-compose up -d`
3. Install dependencies:
   - `python -m pip install -r requirements.txt`
4. Start the application:
   - `uvicorn app.queue.main:app --reload`
5. Open `http://127.0.0.1:8000/docs` to view the API.

## API Endpoints

### Queue

- `POST /queue/join`
  - Join the virtual queue and receive a session cookie.
  - Body: `{"name": "<username>"}`
- `GET /queue/ranks`
  - Return the full queue order.
- `GET /queue/getrank`
  - Return the current user rank and arena eligibility.
- `POST /queue/update`
  - Developer endpoint to remove the first N queue entries.
- `GET /queue/arenausers`
  - Developer endpoint to inspect current arena users.

### Booking

- `POST /booking/reserve-seat/`
  - Reserve an available seat.
  - Body: `{"eventID": <id>, "seatID": <id>}`
- `POST /booking/book`
  - Confirm a reserved seat.
  - Body: `{"eventID": <id>, "seatID": <id>}`
- `GET /booking/getseats/{eventID}`
  - List tickets for an event.

### Events

- `GET /events`
  - Return all events.

## Runtime State and Storage

The application stores live queue state in Redis.

### Redis data model

- `VirtualQueue` sorted set
  - Member: `user_id`
  - Score: join timestamp
  - Used to maintain FIFO queue order.
- `user:{user_id}` hash
  - Stores metadata such as `in_arena` and `IP`.
  - Updated by the background worker when the user enters the arena.
  - TTL is set to 720 seconds for arena users.

Per-user storage is minimal: one sorted-set entry plus one hash key containing a few metadata fields using less memory storage.

### Time complexity

- `ZADD` — O(log N)
- `ZRANK` — O(log N)
- `ZPOPMIN` — O(log N)
- `ZREMRANGEBYRANK` — O(log N + M)
- `ZRANGE` — O(log N + M)
- `HSET` / `HGET` / `HEXISTS` — O(1)
- `EXPIRE` — O(1)
- `KEYS` — O(N) (developer-only endpoint)

## Race Conditions and Concurrency Control

The system uses atomic state transitions and conditional updates to prevent races.

### Queue operations

Queue admission and promotion are handled by Redis sorted-set commands. Redis executes each command atomically(Single Threaded), so concurrent queue inserts and removals remain consistent.

### Arena access

Booking requests are gated by the booking middleware, which checks `HEXISTS user:{user_id} in_arena` before allowing access.

### Ticket reservation, booking and Race conditions

Booking state changes use conditional SQL updates:

- Reserve only when `status = 'AVAILABLE'`.
- Book only when `status = 'RESERVED'` and `userid` matches.

If another process changes the ticket first, the update affects zero rows and the request fails safely.

### Locks and distributed coordination

There is no explicit distributed lock for queue or booking operations. Instead, the design relies on:

- Redis command atomicity for queue state changes
- SQL update filters for row-level concurrency control
- Middleware validation for arena membership

## Performance Considerations

- Redis keeps queue operations lightweight and avoids repeated database reads.
- PostgreSQL is used only for persistent ticket and event state.
- Background worker processing is decoupled from request handling.
- Rate limiting protects the service from request floods.
- The queue and booking workflows are separated to reduce contention and better performance by In-memory Database.

## Contributing

- Fork the repository and create a feature branch.
- Update the README for new endpoints or architecture changes.

## Future Enhancements

- Add a frontend for queue entry, arena status, and booking.
- Improve API error handling with structured responses.
- Add workers for real-time WebSocket updates.
- Provide dashboards for queue and booking operations.
- Add observability for Redis and database performance.

