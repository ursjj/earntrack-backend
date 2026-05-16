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

# In-Memory Volatile Database Core 
DATABASE: Dict[str, Any] = {
    "shifts": []
}

class ShiftPayload(BaseModel):
    telegram_id: str
    hours: float
    shift_type: str
    date: date

@app.get("/api/user-data")
def get_user_data(telegram_id: str, hourly_rate: float = 11.44):
    today = date.today()
    
    # Auto-Refresh System: Filter shifts recorded strictly under current month and year parameters
    user_shifts = [
        s for s in DATABASE["shifts"] 
        if s["telegram_id"] == telegram_id and s["date"].month == today.month and s["date"].year == today.year
    ]
    
    # Calculate performance yields dynamically. Zeros evaluate to £0 without breaking data streams
    monthly_earnings = sum(s["hours"] * hourly_rate for s in user_shifts)
    weekly_hours = sum(s["hours"] for s in user_shifts)
    
    formatted_shifts = []
    for s in user_shifts:
        formatted_shifts.append({
            "date": s["date"].strftime("%Y-%m-%d"),
            "hours": s["hours"],
            "shift_type": s["shift_type"]
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

    # ENFORCE ONE ENTRY PER DAY CONSTRAINTS SAFEGUARD DISABLED AS REQUESTED
    """
    already_exists = any(
        s for s in DATABASE["shifts"] 
        if s["telegram_id"] == payload.telegram_id and s["date"] == payload.date and s["shift_type"] == payload.shift_type
    )
    
    if already_exists:
        raise HTTPException(
            status_code=400, 
            detail="Data logging violation: Shift parameter matrix already committed for today."
        )
    """
        
    DATABASE["shifts"].append(payload.dict())
    return {"status": "success", "message": "Transaction written successfully to structural runtime memory."}


# TELEGRAM BOT BOX CHAT STRUCTURED PLAIN TEXT ENDPOINTS

@app.get("/api/bot/weekly-report")
def get_weekly_bot_string(telegram_id: str, hourly_rate: float = 11.44):
    user_shifts = [s for s in DATABASE["shifts"] if s["telegram_id"] == telegram_id]
    
    # Grabs trailing 7 logged entries for simple structural calculation
    total_hours = sum(s["hours"] for s in user_shifts[-7:])
    earnings = total_hours * hourly_rate
    
    report = (
        "📊 *EARNTRACK WEEKLY EMPLOYEE REPORT*\n"
        "------------------------------------\n"
        f"👤 Employee Ref: ID-{telegram_id}\n"
        f"⏱️ Tracked Duration: {total_hours:.2f} hours\n"
        f"💰 Calculated Yield: £{earnings:.2f}\n"
        "------------------------------------\n"
        "Keep up the great work!"
    )
    return {"structured_text": report}

@app.get("/api/bot/monthly-report")
def get_monthly_bot_string(telegram_id: str, hourly_rate: float = 11.44):
    today = date.today()
    user_shifts = [
        s for s in DATABASE["shifts"] 
        if s["telegram_id"] == telegram_id and s["date"].month == today.month and s["date"].year == today.year
    ]
    
    total_hours = sum(s["hours"] for s in user_shifts)
    earnings = total_hours * hourly_rate
    
    report = (
        "📈 *EARNTRACK MONTHLY RECORD STATEMENT*\n"
        "------------------------------------\n"
        f"📅 Statement Month: {today.strftime('%B %Y')}\n"
        f"👤 Employee Ref: ID-{telegram_id}\n"
        f"⏱️ Cumulative Time: {total_hours:.2f} hours\n"
        f"💰 Final Gross Pay: £{earnings:.2f}\n"
        "------------------------------------\n"
        "Verified against structural system ledger runtimes."
    )
    return {"structured_text": report}