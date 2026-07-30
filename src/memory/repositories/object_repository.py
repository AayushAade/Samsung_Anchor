from datetime import datetime
from sqlalchemy.orm import Session
from src.memory.models import Object, ObjectHistory
import json

class ObjectRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def log_object(self, object_name: str, x: float, y: float, room: str, bounding_box: list = None):
        now_str = datetime.now().isoformat()
        
        with self.session_factory() as session:
            obj = session.query(Object).filter(Object.name == object_name).first()
            if not obj:
                obj = Object(name=object_name)
                session.add(obj)
                
            obj.last_seen = now_str
            obj.x = x
            obj.y = y
            obj.room = room
            obj.bounding_box = bounding_box
            
            history = ObjectHistory(
                object_name=object_name,
                timestamp=now_str,
                x=x,
                y=y,
                room=room,
                bounding_box=bounding_box
            )
            session.add(history)
            
            # Keep only last 50
            histories = session.query(ObjectHistory).filter(ObjectHistory.object_name == object_name).order_by(ObjectHistory.id.asc()).all()
            if len(histories) > 50:
                for h in histories[:-50]:
                    session.delete(h)
                    
            session.commit()
            return True

    def get_last_known_location(self, object_name: str):
        with self.session_factory() as session:
            obj = session.query(Object).filter(Object.name == object_name).first()
            if not obj:
                return None
                
            histories = session.query(ObjectHistory).filter(ObjectHistory.object_name == object_name).order_by(ObjectHistory.id.asc()).all()
            
            history_list = []
            for h in histories:
                history_list.append({
                    "timestamp": h.timestamp,
                    "x": h.x,
                    "y": h.y,
                    "room": h.room,
                    "bounding_box": h.bounding_box
                })
                
            return {
                "last_seen": obj.last_seen,
                "x": obj.x,
                "y": obj.y,
                "room": obj.room,
                "bounding_box": obj.bounding_box,
                "history": history_list
            }

    def get_all_objects(self):
        objects_dict = {}
        with self.session_factory() as session:
            objs = session.query(Object).all()
            for obj in objs:
                objects_dict[obj.name] = self.get_last_known_location(obj.name)
        return objects_dict
