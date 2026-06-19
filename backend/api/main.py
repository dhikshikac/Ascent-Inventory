from fastapi import FastAPI

from backend import database
from backend.api.routes import auth, computers, departments, employees, instruments

app = FastAPI(title="Ascent Inventory API")


@app.on_event("startup")
def startup():
    database.init()


app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(employees.router)
app.include_router(computers.router)
app.include_router(instruments.router)


@app.get("/health")
def health():
    return {"status": "ok"}
