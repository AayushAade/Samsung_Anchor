from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class RoomLocation(Enum):
    LIVING_ROOM = "Living Room"
    BEDROOM = "Bedroom"
    KITCHEN = "Kitchen"
    BATHROOM = "Bathroom"
    ENTRANCE = "Entrance"
    UNKNOWN = "Unknown"


class ActivityType(Enum):
    WALKING = "Walking"
    SITTING = "Sitting"
    SLEEPING = "Sleeping"
    READING = "Reading"
    EATING = "Eating"
    WATCHING_TV = "Watching TV"
    MEDICATION = "Taking Medication"
    TALKING = "Talking"
    IDLE = "Idle"
    FALLEN = "Fallen / Emergency"


class AudioEventType(Enum):
    SPEECH_PRESENT = "Speech Present"
    SILENCE = "Silence"
    CALLING_NAME = "Calling Name"
    CRYING = "Crying / Distress"
    LOUD_NOISE = "Loud Noise"
    GLASS_BREAK = "Glass Break"
    ALARM = "Alarm"
    DOOR_BELL = "Doorbell"
    UNKNOWN = "Unknown"


@dataclass
class FrameData:
    frame_id: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    width: int = 1280
    height: int = 720
    fps: float = 30.0


@dataclass
class DetectedFace:
    face_id: str
    name: Optional[str]
    confidence: float
    first_seen: str
    last_seen: str
    is_known: bool = False


@dataclass
class DetectedObject:
    object_name: str
    location: RoomLocation
    confidence: float = 0.90
    last_seen: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    is_moving: bool = False


@dataclass
class AudioEvent:
    event_type: AudioEventType
    confidence: float = 0.95
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))


@dataclass
class PerceptionContext:
    current_room: RoomLocation = RoomLocation.LIVING_ROOM
    detected_activity: ActivityType = ActivityType.SITTING
    detected_faces: List[DetectedFace] = field(default_factory=list)
    detected_objects: List[DetectedObject] = field(default_factory=list)
    audio_events: List[AudioEvent] = field(default_factory=list)
    fps: float = 30.0
    last_updated: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
