from fastapi import FastAPI, HTTPException
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

class ShiftPayload(BaseModel):
    telegram_id: str
    hours: float
    shift_type: str
    date: date

@app.get("/api/user-data")
def get_user_data(telegram_id: str, hourly_rate: float = 11.44):
    today = date.today()
    user_shifts = [
        s for s in DATABASE["shifts"] 
        if s["telegram_id"] == telegram_id and s["date"].month == today.month and s["date"].year == today.year
    ]
    
    monthly_earnings = sum(s["hours"] * hourly_rate for s in user_shifts if s["shift_type"] != "HOLIDAY")
    weekly_hours = sum(s["hours"] for s in user_shifts if s["shift_type"] != "HOLIDAY")
    
    formatted = []
    for s in user_shifts:
        formatted.append({
            "date": s["date"].strftime("%Y-%m-%d"),
            "hours": s["hours"],
            "shift_type": s["shift_type"]
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

# ADVANCED TIMESHEET PARSING STATEMENT ENGINE FOR BOT PAGE DELIVERY
@app.get("/api/bot/weekly-report")
def get_structured_timesheet(
    telegram_id: str, 
    username: str = "Joseph", 
    hourly_rate: float = 11.44, 
    target: float = 1500.0, 
    limit: float = 40.0
):
    today = date.today()
    # Calculate current ISO week framework safely
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    
    # Map out names inside clean arrays
    days_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    days_dates = [start_week + timedelta(days=i) for i in range(7)]
    
    lines = []
    total_weekly_hours = 0.0
    
    for i, target_date in enumerate(days_dates):
        # Gather all entries hit on this specific structural cycle date
        day_logs = [s for s in DATABASE["shifts"] if s["telegram_id"] == telegram_id and s["date"] == target_date]
        
        is_holiday = any(s for s in day_logs if s["shift_type"] == "HOLIDAY")
        
        if is_holiday:
            lines.append(f"{days_map[i]}: [Day: 0h]   [Eve: 0h]   [Night: 0h]   -> HOLIDAY ☀️")
        else:
            day_h = sum(s["hours"] for s in day_logs if s["shift_type"] == "Day Shift")
            eve_h = sum(s["hours"] for s in day_logs if s["shift_type"] == "Evening Shift")
            night_h = sum(s["hours"] for s in day_logs if s["shift_type"] == "Night Shift")
            
            combined_h = day_h + eve_h + night_h
            total_weekly_hours += combined_h
            
            day_pay = combined_h * hourly_rate
            pay_str = f"£{day_pay:.2f}" if combined_h > 0 else "£0"
            
            lines.append(f"{days_map[i]}: [Day: {day_h:.2f}h]  [Eve: {eve_h:.2f}h]  [Night: {night_h:.2f}h]   -> {pay_str}")

    # Calculations for summary telemetry blocks
    total_weekly_gross = total_weekly_hours * hourly_rate
    overtime = max(0.0, total_weekly_hours - limit)
    overtime_str = f" (Overtime: +{overtime:.2f}h)" if overtime > 0 else ""
    
    # Calculate entire month aggregation parameters dynamically
    all_month_logs = [
        s for s in DATABASE["shifts"] 
        if s["telegram_id"] == telegram_id and s["date"].month == today.month and s["date"].year == today.year and s["shift_type"] != "HOLIDAY"
    ]
    monthly_accumulated = sum(s["hours"] * hourly_rate for s in all_month_logs)

    # Frame exact requested structure text block output
    report_string = (
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
    
    return {"structured_text": report_string}