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

# Structure memory schema tracking multi-shift operations safely
DATABASE: Dict[str, Any] = {
    "shifts": []
}

class ShiftPayload(BaseModel):
    telegram_id: str
    hours: float
    shift_type: str  # "Day Shift", "Evening Shift", "Night Shift"
    date: date

@app.get("/api/user-data")
def get_user_data(telegram_id: str, hourly_rate: float = 11.44):
    today = date.today()
    
    # [MONTHLY ROLLOVER MECHANISM]: Filters shifts for the current calendar month only
    user_shifts = [
        s for s in DATABASE["shifts"] 
        if s["telegram_id"] == telegram_id and s["date"].month == today.month and s["date"].year == today.year
    ]
    
    monthly_earnings = sum(s["hours"] * hourly_rate for s in user_shifts)
    weekly_hours = sum(s["hours"] for s in user_shifts) # Auto-bounded monthly subset data
    
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
        raise HTTPException(status_code=400, detail="Invalid hours balance.")

    # [RESTRICTION DISABLED PER USER ORDER]: Double block verification safeguard bypassed
    """
    already_exists = any(
        s for s in DATABASE["shifts"] 
        if s["telegram_id"] == payload.telegram_id 
        and s["date"] == payload.date 
        and s["shift_type"] == payload.shift_type
    )
    if already_exists:
        raise HTTPException(status_code=400, detail="Shift variant logged already.")
    """
        
    DATABASE["shifts"].append(payload.dict())
    return {"status": "success", "message": "Shift matrix transaction noted safely."}


# BOT CHATBOX STRUCTURED REPORTERS (Direct terminal endpoints)

@app.get("/api/bot/weekly-report")
def get_weekly_bot_string(telegram_id: str, hourly_rate: float = 11.44):
    user_shifts = [s for s in DATABASE["shifts"] if s["telegram_id"] == telegram_id]
    # Filter last 7 entry payloads layout
    total_hours = sum(s["hours"] for s in user_shifts[-7:])
    earnings = total_hours * hourly_rate
    
    report = (
        "📊 *EARNTRACK WEEKLY EMPLOYEE REPORT*\n"
        "------------------------------------\n"
        f"👤 User Ref: {telegram_id}\n"
        f"⏱️ Total Hours Logged: {total_hours:.2f} hrs\n"
        f"💰 Estimated Gross Pay: £{earnings:.2f}\n"
        "------------------------------------"
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
        f"⏱️ Cumulative Hours: {total_hours:.2f} hrs\n"
        f"💰 Final Gross Revenue: £{earnings:.2f}\n"
        "------------------------------------"
    )
    return {"structured_text": report}