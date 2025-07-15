from datetime import date, time
from typing import List
from pydantic import BaseModel


class Day(BaseModel):
    id: int
    date: date
    start: time
    end: time


class Timeslot(BaseModel):
    id: int
    day_id: int
    start: time
    end: time


class ScheduleData(BaseModel):
    days: List[Day]
    timeslots: List[Timeslot]
