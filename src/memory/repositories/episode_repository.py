from sqlalchemy.orm import Session
from src.memory.models import EpisodeModel
from src.cognition.episode import Episode
from datetime import datetime

class DatabaseEpisodeRepository:
    """
    SQLAlchemy backed repository for Episodic memories.
    """
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def add_episode(self, episode: Episode) -> None:
        with self.session_factory() as session:
            db_episode = EpisodeModel(
                person=episode.person,
                summary=episode.summary,
                timestamp=episode.timestamp.isoformat() if isinstance(episode.timestamp, datetime) else str(episode.timestamp),
                location=episode.location,
                commitments=episode.commitments,
                tags=episode.tags
            )
            session.add(db_episode)
            session.commit()

    def latest_episode(self) -> Episode | None:
        with self.session_factory() as session:
            db_episode = session.query(EpisodeModel).order_by(EpisodeModel.id.desc()).first()
            if not db_episode:
                return None
            return self._to_domain(db_episode)

    def episodes_for_person(self, person: str) -> list[Episode]:
        with self.session_factory() as session:
            # Case insensitive match using ilike
            db_episodes = session.query(EpisodeModel).filter(EpisodeModel.person.ilike(f"%{person}%")).order_by(EpisodeModel.id.desc()).all()
            return [self._to_domain(e) for e in db_episodes]

    def get_all_episodes(self) -> list[Episode]:
        with self.session_factory() as session:
            db_episodes = session.query(EpisodeModel).order_by(EpisodeModel.timestamp.asc(), EpisodeModel.id.asc()).all()
            return [self._to_domain(e) for e in db_episodes]

    def get_episodes_for_today(self) -> list[Episode]:
        today_str = datetime.now().strftime("%Y-%m-%d")
        with self.session_factory() as session:
            db_episodes = session.query(EpisodeModel).filter(EpisodeModel.timestamp.startswith(today_str)).order_by(EpisodeModel.timestamp.asc(), EpisodeModel.id.asc()).all()
            return [self._to_domain(e) for e in db_episodes]

    def get_visitors_for_today(self) -> list[str]:
        episodes = self.get_episodes_for_today()
        visitors = []
        for ep in episodes:
            if ep.person and ep.person.strip() and ep.person.strip().lower() not in ["unknown", "none", "anonymous"]:
                p = ep.person.strip()
                if p not in visitors:
                    visitors.append(p)
        return visitors

    def get_recent_episodes(self, limit: int = 20) -> list[Episode]:
        with self.session_factory() as session:
            db_episodes = session.query(EpisodeModel).order_by(EpisodeModel.id.desc()).limit(limit).all()
            return [self._to_domain(e) for e in reversed(db_episodes)]

    def clear(self) -> None:
        with self.session_factory() as session:
            session.query(EpisodeModel).delete()
            session.commit()

    def count(self) -> int:
        with self.session_factory() as session:
            return session.query(EpisodeModel).count()
            
    def _to_domain(self, db_model: EpisodeModel) -> Episode:
        try:
            ts = datetime.fromisoformat(db_model.timestamp)
        except Exception:
            ts = datetime.now()
            
        return Episode(
            person=db_model.person,
            summary=db_model.summary,
            timestamp=ts,
            location=db_model.location or "",
            commitments=list(db_model.commitments) if db_model.commitments else [],
            tags=list(db_model.tags) if db_model.tags else []
        )

