from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date
from typing import List, Dict, Any

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Advanced Data Matrix Simulator
DATABASE: Dict[str, Any] = {
    "shifts": []
}

class AdvancedShiftPayload(BaseModel):
    telegram_id: str
    date: date
    day_hours: float
    evening_hours: float
    night_hours: float
    is_holiday: bool

@app.get("/api/user-data")
def get_user_data(telegram_id: str, hourly_rate: float = 11.44):
    current_month = date.today().month
    current_year = date.today().year
    
    user_shifts = [s for s in DATABASE["shifts"] if s["telegram_id"] == telegram_id]
    
    # DYNAMIC MONTHLY ROLL-OVER FILTER: 
    # Automatically separates financial data tracking metrics when calendar months cycle forward.
    monthly_shifts = [
        s for s in user_shifts 
        if s["date"].month == current_month and s["date"].year == current_year
    ]
    
    # Calculate performance yields dynamically across columns
    total_monthly_hours = sum((s["day_hours"] + s["evening_hours"] + s["night_hours"]) for s in monthly_shifts)
    monthly_earnings = total_monthly_hours * hourly_rate
    
    # Weekly aggregation logic tracking block
    weekly_hours = sum((s["day_hours"] + s["evening_hours"] + s["night_hours"]) for s in user_shifts) # In production map to structural ISO week calendar arrays
    
    formatted_shifts = []
    for s in user_shifts:
        formatted_shifts.append({
            "date": s["date"].strftime("%Y-%m-%d"),
            "day_hours": s["day_hours"],
            "evening_hours": s["evening_hours"],
            "night_hours": s["night_hours"],
            "is_holiday": s["is_holiday"]
        })
        
    return {
        "monthlyCumulativeEarnings": monthly_earnings,
        "weeklyTotalHours": weekly_hours,
        "weekShifts": formatted_shifts
    }

@app.post("/api/log-shift")
def log_user_shift(payload: AdvancedShiftPayload):
    # Enforce daily input synchronization lock boundary constraints
    already_exists = any(
        s for s in DATABASE["shifts"] 
        if s["telegram_id"] == payload.telegram_id and s["date"] == payload.date
    )
    
    if already_exists:
        raise HTTPException(
            status_code=400, 
            detail="Transaction failed: Today's timesheet parameter record has already locked."
        )
        
    DATABASE["shifts"].append(payload.dict())
    return {"status": "success", "message": "Triple-shift profile successfully committed to live runtime database."}