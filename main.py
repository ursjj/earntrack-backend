from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, timedelta
from typing import Dict, Any

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE: Dict[str, Any] = {
    "shifts": []
}

DAYS_INDEX_MAP = {
    "Sunday": 0,
    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6
}

class ShiftPayload(BaseModel):
    telegram_id: str
    hours: float
    shift_type: str
    day_name: str

@app.get("/api/user-data")
def get_user_data(telegram_id: str, hourly_rate: float = 11.44):
    user_shifts = [s for s in DATABASE["shifts"] if s["telegram_id"] == telegram_id]
    
    monthly_earnings = sum(s["hours"] * hourly_rate for s in user_shifts if s["shift_type"] != "HOLIDAY")
    weekly_hours = sum(s["hours"] for s in user_shifts if s["shift_type"] != "HOLIDAY")
    
    formatted = []
    for s in user_shifts:
        formatted.append({
            "hours": s["hours"],
            "shift_type": s["shift_type"],
            "day_index": DAYS_INDEX_MAP.get(s["day_name"], 1)
        })
        
    return {
        "monthlyCumulativeEarnings": monthly_earnings,
        "weeklyTotalHours": weekly_hours,
        "weekShifts": formatted
    }

@app.post("/api/log-shift")
def log_user_shift(payload: ShiftPayload):
    DATABASE["shifts"].append(payload.dict())
    return {"status": "success"}

@app.get("/api/bot/weekly-report")
def get_structured_timesheet(telegram_id: str, username: str = "Joseph", hourly_rate: float = 11.44, target: float = 1500.0, limit: float = 40.0):
    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    
    days_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    days_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    lines = []
    total_weekly_hours = 0.0
    
    for i, day_full in enumerate(days_list):
        day_logs = [s for s in DATABASE["shifts"] if s["telegram_id"] == telegram_id and s["day_name"] == day_full]
        
        if any(s for s in day_logs if s["shift_type"] == "HOLIDAY"):
            lines.append(f"{days_short[i]}: [Day: 0h]   [Eve: 0h]   [Night: 0h]   -> HOLIDAY ☀️")
        else:
            day_h = sum(s["hours"] for s in day_logs if s["shift_type"] == "Day Shift")
            eve_h = sum(s["hours"] for s in day_logs if s["shift_type"] == "Evening Shift")
            night_h = sum(s["hours"] for s in day_logs if s["shift_type"] == "Night Shift")
            
            combined_h = day_h + eve_h + night_h
            total_weekly_hours += combined_h
            
            lines.append(f"{days_short[i]}: [Day: {day_h:.2f}h]  [Eve: {eve_h:.2f}h]  [Night: {night_h:.2f}h]   -> " + (f"£{combined_h * hourly_rate:.2f}" if combined_h > 0 else "£0"))

    total_weekly_gross = total_weekly_hours * hourly_rate
    overtime = max(0.0, total_weekly_hours - limit)
    overtime_str = f" (Overtime: +{overtime:.2f}h)" if overtime > 0 else ""
    monthly_accumulated = sum(s["hours"] * hourly_rate for s in DATABASE["shifts"] if s["telegram_id"] == telegram_id and s["shift_type"] != "HOLIDAY")

    return {
        "structured_text": (
            "📊 *EARNTRACK TIMESHEET STATEMENT*\n"
            "---------------------------------------------\n"
            f"User Reference: @{username}\n"
            f"Horizon: Week {today.isocalendar()[1]} ({start_week.strftime('%b %d')} - {end_week.strftime('%b %d')})\n"
            "---------------------------------------------\n"
            + "\n".join(lines) + "\n"
            "---------------------------------------------\n"
            f"Total Weekly Hours:  {total_weekly_hours:.2f} hrs{overtime_str}\n"
            f"Total Weekly Gross:  £{total_weekly_gross:.2f} 💸\n"
            f"Monthly Target Accumulation: £{monthly_accumulated:.2f} / £{target:.0f}"
        )
    }