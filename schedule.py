import requests
from dataclasses import dataclass
from pydantic import ValidationError
from models import ScheduleData
from datetime import datetime, date, time, timedelta
from typing import List, Optional, Tuple, Dict


@dataclass
class DaySchedule:
    work_start: time
    work_end: time
    busy_slots: List[Tuple[time, time]]


class WorkerSchedule:
    def __init__(self, schedule_data):
        data = ScheduleData(**schedule_data)
        self.schedule: Dict[date, DaySchedule] = self._process_data(data)

    def _process_data(self, data: ScheduleData):
        processed: Dict[date, DaySchedule] = {}

        for day in data.days:
            busy_slots = [
                (slot.start, slot.end)
                for slot in data.timeslots
                if slot.day_id == day.id
            ]
            merged_slots = self._merge_slots(busy_slots)
            processed[day.date] = DaySchedule(
                work_start=day.start,
                work_end=day.end,
                busy_slots=merged_slots
            )
        return processed

    @staticmethod
    def _merge_slots(
        slots: List[Tuple[time, time]]
    ) -> List[Tuple[time, time]]:
        if not slots:
            return []
        slots.sort(key=lambda x: x[0])
        merged = [slots[0]]

        for current_start, current_end in slots[1:]:
            last_start, last_end = merged[-1]
            if current_start < last_end:
                merged[-1] = last_start, max(last_end, current_end)
            else:
                merged.append((current_start, current_end))

        return merged

    def get_busy_slots(
            self, d: date
    ) -> List[Tuple[time, time]]:
        return (
            self.schedule
            .get(d, DaySchedule(time.min, time.min, []))
            .busy_slots
        )

    def get_free_slots(self, d: date) -> List[Tuple[time, time]]:
        day = self.schedule.get(d)
        if not day:
            return []

        free_slots = []
        current = day.work_start

        for busy_start, busy_end in day.busy_slots:
            if current < busy_start:
                free_slots.append((current, busy_start))
            current = max(current, busy_end)

        if current < day.work_end:
            free_slots.append((current, day.work_end))

        return free_slots

    def get_free_slots_str(self, date_str: str) -> List[Dict[str, str]]:
        d = date.fromisoformat(date_str)
        return [
            {'start': s.strftime('%H:%M'), 'end': e.strftime('%H:%M')}
            for s, e in self.get_free_slots(d)
        ]

    def get_busy_slots_str(self, date_str: str):
        d = date.fromisoformat(date_str)
        return [
            {'start': s.strftime('%H:%M'), 'end': e.strftime('%H:%M')}
            for s, e in self.get_busy_slots(d)
        ]

    def is_available(self, date_str: str, start: str, end: str) -> bool:
        d = date.fromisoformat(date_str)
        start_time = time.fromisoformat(start)
        end_time = time.fromisoformat(end)

        day = self.schedule.get(d)
        if not day:
            return False

        if start_time < day.work_start or end_time > day.work_end:
            return False

        return all(
            end_time <= busy_start or start_time >= busy_end
            for busy_start, busy_end in day.busy_slots
        )

    def find_free_slot(self, duration_min: int) -> Optional[Dict[str, str]]:
        for work_date, day in sorted(self.schedule.items()):
            free_slots = self.get_free_slots(work_date)

            for start, end in free_slots:
                start_dt = datetime.combine(work_date, start)
                end_dt = datetime.combine(work_date, end)
                delta = (end_dt - start_dt).total_seconds() / 60

                if delta >= duration_min:
                    found_end = (start_dt + timedelta(minutes=duration_min))\
                        .time()
                    return {
                        'date': work_date.isoformat(),
                        'start': start.strftime('%H:%M'),
                        'end': found_end.strftime('%H:%M'),
                    }
            return None


if __name__ == '__main__':
    API_URL = 'https://ofc-test-01.tspb.su/test-task/'

    def fetch_schedule_data(url: str) -> dict:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    try:
        raw_data = fetch_schedule_data(API_URL)
        ws = WorkerSchedule(raw_data)
        print("Занятые слоты 2025-02-15:")
        for slot in ws.get_busy_slots_str("2025-02-15"):
            print(f"  {slot['start']} — {slot['end']}")

        print("\nСвободные слоты 2025-02-15:")
        for slot in ws.get_free_slots_str("2025-02-15"):
            print(f"  {slot['start']} — {slot['end']}")

        print("\nБлижайший свободный слот для 60 минут:")
        slot = ws.find_free_slot(60)
        if slot:
            print(f"  Найден: {slot['date']} {slot['start']} — {slot['end']}")
        else:
            print("  Нет подходящего слота")

        print("\nПроверка доступности 2025-02-15 с 12:30 до 13:30:")
        available = ws.is_available("2025-02-15", "12:30", "13:30")
        print("  Доступно" if available else "  Недоступно")
    except requests.RequestException as e:
        print(f'Requesr error {e}')
    except ValidationError as e:
        print(f'Validation error {e}, please use correct JSON')
