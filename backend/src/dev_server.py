"""アプリケーションブートストラップ。

Container を組み立てて create_app に渡す。
Docker / ローカル開発の両方で使用。
"""

from __future__ import annotations

from sqlalchemy import create_engine

from api.app import create_app
from api.dependencies import Container
from infrastructure.config.settings import Settings
from infrastructure.rdb.base import Base


def _bootstrap() -> object:
    import infrastructure.rdb.models  # noqa: F401  — register all ORM models

    settings = Settings()

    engine = create_engine(
        f"sqlite:///{settings.sqlite_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)

    container = Container(
        engine=engine,
    )
    return container


app = create_app(_bootstrap())  # type: ignore[arg-type]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)  # noqa: S104
