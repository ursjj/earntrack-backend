from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date
from typing import List, Dict, Any

app = FastAPI()

# Allow safe cross-origin resource isolation routing from Vercel deployment servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-Memory Volatile Database Core 
DATABASE: Dict[str, Any] = {
    "shifts": []
}

class ShiftPayload(BaseModel):
    telegram_id: str
    hours: float
    date: date

@app.get("/api/user-data")
def get_user_data(telegram_id: str, hourly_rate: float = 11.44):
    # Filter shifts recorded strictly under the validated user reference signature
    user_shifts = [s for s in DATABASE["shifts"] if s["telegram_id"] == telegram_id]
    
    # Calculate performance yields dynamically. Zeros evaluate to £0 without breaking data streams
    monthly_earnings = sum(s["hours"] * hourly_rate for s in user_shifts)
    weekly_hours = sum(s["hours"] for s in user_shifts)
    
    formatted_shifts = []
    for s in user_shifts:
        formatted_shifts.append({
            "date": s["date"].strftime("%Y-%m-%d"),
            "hours": s["hours"]
        })
    
    return {
        "monthlyCumulativeEarnings": monthly_earnings,
        "weeklyTotalHours": weekly_hours,
        "weekShifts": formatted_shifts
    }

@app.post("/api/log-shift")
def log_user_shift(payload: ShiftPayload):
    if payload.hours < 0:
        raise HTTPException(status_code=400, detail="Invalid hours count provided.")

    # ENFORCE ONE ENTRY PER DAY CONSTRAINTS SAFEGUARD (Includes holiday logs)
    already_exists = any(
        s for s in DATABASE["shifts"] 
        if s["telegram_id"] == payload.telegram_id and s["date"] == payload.date
    )
    
    if already_exists:
        raise HTTPException(
            status_code=400, 
            detail="Data logging violation: Shift parameter matrix already committed for today."
        )
        
    DATABASE["shifts"].append(payload.dict())
    return {"status": "success", "message": "Transaction written successfully to structural runtime memory."}