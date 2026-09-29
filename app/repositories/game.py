import logging

from sqlmodel import Session, select

from app.models.game import Game, GameBase
from app.schemas.game import GameCreate

logger = logging.getLogger(__name__)


class GameRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, game_data: GameCreate | GameBase) -> Game:
        try:
            game = Game.model_validate(game_data)
            self.db.add(game)
            self.db.commit()
            self.db.refresh(game)
            return game
        except Exception as e:
            logger.error(f"Error creating game: {e}")
            self.db.rollback()
            raise

    def get_by_id(self, game_id: int) -> Game | None:
        return self.db.get(Game, game_id)

    def get_all(self) -> list[Game]:
        return self.db.exec(select(Game)).all()
