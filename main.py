from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date
from typing import List, Dict, Any

app = FastAPI()

# CRUCIAL: This allows your Vercel frontend to talk to this backend safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows your Vercel app link to access this API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory database simulation (Wipes on server restart)
# In production, you will replace this with a PostgreSQL/Supabase link
DATABASE: Dict[str, Any] = {
    "shifts": []
}

class ShiftPayload(BaseModel):
    telegram_id: str
    hours: float
    date: date

@app.get("/api/user-data")
def get_user_data(telegram_id: str):
    # Filter shifts belonging only to this specific user
    user_shifts = [s for s in DATABASE["shifts"] if s["telegram_id"] == telegram_id]
    
    # Calculate totals dynamically based on UK minimum wage assumption (£11.44)
    hourly_rate = 11.44
    monthly_earnings = sum(s["hours"] * hourly_rate for s in user_shifts)
    weekly_hours = sum(s["hours"] for s in user_shifts)
    
    # Format structural payload for your HTML front-end
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
    # ENFORCE ONE ENTRY PER DAY SAFEGUARD
    already_exists = any(
        s for s in DATABASE["shifts"] 
        if s["telegram_id"] == payload.telegram_id and s["date"] == payload.date
    )
    
    if already_exists:
        raise HTTPException(
            status_code=400, 
            detail="Data entry constraint violation: Shift already finalized for today."
        )
        
    DATABASE["shifts"].append(payload.dict())
    return {"status": "success", "message": "Transaction written successfully"}
