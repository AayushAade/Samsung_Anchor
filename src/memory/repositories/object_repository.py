import re
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
            # First try exact match, then case-insensitive / partial match
            obj = session.query(Object).filter(Object.name == object_name).first()
            if not obj:
                obj = session.query(Object).filter(Object.name.ilike(f"%{object_name}%")).first()
            if not obj:
                return None
                
            histories = session.query(ObjectHistory).filter(ObjectHistory.object_name == obj.name).order_by(ObjectHistory.id.asc()).all()
            
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
                "name": obj.name,
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

    _QUERY_STOPWORDS = {"where", "what", "have", "seen", "find", "looking", "with", "your", "mine",
                        "there", "that", "this", "they", "them", "were", "they're", "it's", "left"}

    def search_object(self, query: str):
        """
        Find the observed object named in a free-text query.

        Matches whole words (punctuation stripped) so "where are my glasses?"
        finds "Reading Glasses". Returns the last-known-location dict or None.
        """
        if not query:
            return None
        q_lower = query.lower().strip()
        words = {w for w in re.findall(r"[a-z]+", q_lower) if len(w) > 2 and w not in self._QUERY_STOPWORDS}
        with self.session_factory() as session:
            names = [obj.name for obj in session.query(Object).all()]
        best, best_score = None, 0
        for name in names:
            n_lower = name.lower().replace("_", " ")
            name_words = set(re.findall(r"[a-z]+", n_lower))
            score = 3 if n_lower in q_lower else len(words & name_words | {w for w in words if w.rstrip("s") in {nw.rstrip("s") for nw in name_words}})
            if score > best_score:
                best, best_score = name, score
        return self.get_last_known_location(best) if best else None
