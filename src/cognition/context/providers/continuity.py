import time
from datetime import datetime
from typing import Optional

from src.cognition.context.models import ContextFreshness
from src.cognition.context.provider import ContextProvider, ProviderResponse
from src.cognition.orientation.models import DailyOrientationContext, RoutineStage
from src.interaction.events import PresenceEvent


class ContinuityContextProvider(ContextProvider):
    """
    Context Provider for Daily Orientation and Life Continuity.
    Determines current routine anchors, day/time orientation, and activity context.
    """

    @property
    def name(self) -> str:
        return "ContinuityContextProvider"

    @property
    def capability_domain(self) -> str:
        return "continuity"

    def fetch_context(self, event: PresenceEvent) -> ProviderResponse:
        start_time = time.perf_counter()

        now = datetime.now()
        hour = now.hour

        # Determine routine stage anchor based on time of day and event context
        if 5 <= hour < 9:
            stage = RoutineStage.BREAKFAST.value
            recent = "Woke up and started morning routine"
            upcoming = "Morning heart medication"
        elif 9 <= hour < 11:
            stage = RoutineStage.MEDICATION.value
            recent = "Completed breakfast"
            upcoming = "Morning walk & light reading"
        elif 11 <= hour < 14:
            stage = RoutineStage.LUNCH.value
            recent = "Resting in the living room"
            upcoming = "Lunch time"
        elif 14 <= hour < 17:
            if event.relationship and "Daughter" in event.relationship:
                stage = RoutineStage.FAMILY_VISIT.value
                recent = "Living room reading"
                upcoming = "Tea with Sarah"
            else:
                stage = RoutineStage.AFTERNOON.value
                recent = "Finished lunch"
                upcoming = "Afternoon relaxation"
        elif 17 <= hour < 21:
            stage = RoutineStage.EVENING.value
            recent = "Afternoon walk"
            upcoming = "Dinner & evening news"
        else:
            stage = RoutineStage.NIGHT.value
            recent = "Finished dinner"
            upcoming = "Preparing for sleep"

        current_day_str = now.strftime("%A, %B %d")
        approx_time_str = now.strftime("%I:%M %p").lstrip("0")

        # Today's orientation events
        today_events = [
            "Morning Medication (9:00 AM)",
            "Doctor's Appointment (2:00 PM)" if hour < 14 else "Family Visit with Sarah",
        ]

        orientation_data = DailyOrientationContext(
            routine_stage=stage,
            current_day=current_day_str,
            approximate_time=approx_time_str,
            today_events=today_events,
            recent_activity=recent,
            upcoming_activity=upcoming,
            confidence=0.95,
        )

        latency = (time.perf_counter() - start_time) * 1000

        return ProviderResponse(
            domain=self.capability_domain,
            data=orientation_data,
            confidence=0.95,
            freshness=ContextFreshness.REALTIME,
            latency_ms=latency,
        )
