# Hospital Support Request System

A REST-first support system for hospital equipment, maintenance, IT and facility requests. The backend is FastAPI with MongoDB; the frontend is React/Vite.

## Start with Docker Desktop

1. Copy `.env.example` to `.env` and replace `JWT_SECRET`.
2. Start Docker Desktop.
3. In this folder, run `docker compose up --build`.
4. Open the frontend at `http://localhost:5173`.
5. Open interactive REST documentation at `http://localhost:8000/docs`.

The first start seeds a development administrator:

```text
email: admin@hospital.local
password: Admin123!
```

Change or remove this account before any real deployment.

## REST workflow

1. An admin creates agents and departments using `/api/v1/users` and `/api/v1/departments`.
2. A requester registers, signs in, and submits a ticket.
3. An agent/admin assigns the ticket and changes its status.
4. Staff and requesters exchange comments in the ticket timeline.
5. An agent resolves with a resolution note; requester may reopen when needed.

## Key API routes

| Function | Route |
| --- | --- |
| Login | `POST /api/v1/auth/login` |
| Current user | `GET /api/v1/auth/me` |
| Tickets | `GET, POST /api/v1/tickets` |
| Ticket detail | `GET, PATCH /api/v1/tickets/{ticket_id}` |
| Assignment | `PATCH /api/v1/tickets/{ticket_id}/assign` |
| Status | `PATCH /api/v1/tickets/{ticket_id}/status` |
| Comments | `POST /api/v1/tickets/{ticket_id}/comments` |
| Reports | `GET /api/v1/reports/summary` |

## Local development

Backend needs Python 3.11+ and frontend needs Node 20+.

```text
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

cd frontend
npm install
npm run dev
```

## Important production work still required

- Replace local development credentials with secret management and an administrator setup flow.
- Add file storage (S3/Azure Blob or secured volume) for attachments.
- Add email or in-app notifications.
- Add automated unit/integration tests and CI.
- Put the services behind HTTPS and restrict CORS to the production frontend URL.
