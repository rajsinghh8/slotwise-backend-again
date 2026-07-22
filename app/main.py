# FastAPI application entry point for SlotWise booking backend
import os
from dotenv import load_dotenv
load_dotenv('.env_3698610c-0a42-47f4-8734-fc3a8dd320bd', override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, locations, services, staff, availability, appointments, slots, waitlist, dashboard

app = FastAPI(
    title="SlotWise API",
    description="Appointment booking system for multi-location businesses",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

# Include routers
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(locations.router, prefix=API_PREFIX)
app.include_router(services.router, prefix=API_PREFIX)
app.include_router(staff.router, prefix=API_PREFIX)
app.include_router(availability.router, prefix=API_PREFIX)
app.include_router(appointments.router, prefix=API_PREFIX)
app.include_router(slots.router, prefix=API_PREFIX)
app.include_router(waitlist.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "slotwise"}


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {"message": "SlotWise API", "docs": "/docs"}
