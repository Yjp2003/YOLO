"""
YOLO Vision Dashboard - Vercel Serverless Entry Point
This file is auto-detected by Vercel's Python runtime.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth import router as auth_router
from routes.records import router as records_router
from routes.users import router as users_router

app = FastAPI(
    title="YOLO Vision Dashboard API",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(records_router, prefix="/api/records", tags=["Detection Records"])
app.include_router(users_router, prefix="/api/users", tags=["User Management"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "YOLO Vision API (Vercel Serverless)"}
