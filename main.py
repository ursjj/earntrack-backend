from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Dict, Any
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# YOUR BOT TOKEN EXTRACTED FROM BOTFATHER FOR SENDING OUTBOUND MESSAGES
BOT_TOKEN = "YOUR_SAVED_BOTFATHER_TOKEN"

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

class ReportPayload(BaseModel):
    telegram_id: str
    report_type: str
    username: str

@app.get("/api/user-data")
def get_user_data(telegram_id: str, hourly_rate: float = 11.44):
    user_shifts = [s for s in DATABASE["shifts"] if s["telegram_id"] == telegram_id]
    
    # Target May 2026 for simulated data calculations
    may_shifts = [s for s in user_shifts if s["date"].month == 5 and s["date"].year == 2026]
    
    total_hours = sum((s["day_hours"] + s["evening_hours"] + s["night_hours"]) for s in may_shifts)
    monthly_earnings = total_hours * hourly_rate
    
    return {
        "monthlyCumulativeEarnings": monthly_earnings,
        "weekShifts": [
            {
                "date": s["date"].strftime("%Y-%m-%d"),
                "day_hours": s["day_hours"],
                "evening_hours": s["evening_hours"],
                "night_hours": s["night_hours"],
                "is_holiday": s["is_holiday"]
            } for s in user_shifts
        ]
    }

@app.post("/api/log-shift")
def log_user_shift(payload: AdvancedShiftPayload):
    # RESTRICTION REMOVED FOR TESTING: 
    # Overwrites structural metrics dynamically if double logging occurs, allowing rapid user entry execution
    DATABASE["shifts"] = [s for s in DATABASE["shifts"] if not (s["telegram_id"] == payload.telegram_id and s["date"] == payload.date)]
    
    DATABASE["shifts"].append(payload.dict())
    return {"status": "success", "message": "Sandbox data payload written."}

@app.post("/api/trigger-bot-report")
def trigger_bot_report(payload: ReportPayload):
    user_shifts = [s for s in DATABASE["shifts"] if s["telegram_id"] == payload.telegram_id]
    # Sort chronologically by log target parameters
    user_shifts.sort(key=lambda x: x["date"])
    
    hourly_rate = 11.44
    total_hours = 0
    total_gross = 0
    
    report_lines = []
    report_lines.append("📊 EARNTRACK TIMESHEET STATEMENT")
    report_lines.append("---------------------------------------------")
    report_lines.append(f"Employee Account: @{payload.username}")
    report_lines.append(f"Horizon Scope: {payload.report_type.upper()} REPORT (May 2026)")
    report_lines.append("---------------------------------------------")
    
    # Filter bounds based on tester request configuration toggles
    shifts_to_process = user_shifts if payload.report_type == "monthly" else user_shifts[:7]
    
    for s in shifts_to_process:
        s_date_str = s["date"].strftime("%a, %b %d")
        if s["is_holiday"]:
            report_lines.append(f"📅 {s_date_str} -> ☀️ HOLIDAY / REST DAY")
        else:
            day_total = s["day_hours"] + s["evening_hours"] + s["night_hours"]
            day_cash = day_total * hourly_rate
            total_hours += day_total
            total_gross += day_cash
            report_lines.append(
                f"📅 {s_date_str} -> [Day: {s['day_hours']:.1f}h] [Eve: {s['evening_hours']:.1f}h] [Night: {s['night_hours']:.1f}h] -> Earned: £{day_cash:.2f}"
            )
            
    report_lines.append("---------------------------------------------")
    report_lines.append(f"Cumulative Tracked Hours: {total_hours:.2f} hrs")
    report_lines.append(f"Gross Earnings Balance: £{total_gross:.2f} 💸")
    report_lines.append("---------------------------------------------")
    report_lines.append("Status: Verification Sandbox Execution Concluded.")
    
    final_text_message = "\n".join(report_lines)
    
    # Forward processed string straight to user conversation thread using Telegram API
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(telegram_url, json={"chat_id": payload.telegram_id, "text": final_text_message})
    
    return {"status": "dispatched"}