from collections.abc import AsyncIterator

from neo4j import AsyncGraphDatabase
from sqlalchemy import DateTime, Float, Integer, JSON, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .config import get_settings

settings = get_settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
session_factory = async_sessionmaker(engine, expire_on_commit=False)
neo4j_driver = AsyncGraphDatabase.driver(
    settings.neo4j_uri,
    auth=(settings.neo4j_user, settings.neo4j_password),
)


class Base(DeclarativeBase):
    pass


class DetectionRecord(Base):
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(2048), index=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    verdict: Mapped[str] = mapped_column(String(32), index=True)
    screenshot: Mapped[str] = mapped_column(String(2048))
    dom: Mapped[str] = mapped_column(String(2048))
    signals: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def save_detection(
    session: AsyncSession, result: dict, screenshot: str, dom: str
) -> DetectionRecord:
    record = DetectionRecord(
        url=result["url"],
        brand=result.get("brand"),
        score=result["score"],
        verdict=result["verdict"],
        screenshot=screenshot,
        dom=dom,
        signals=result.get("behavioral", {}),
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def get_detections(session: AsyncSession) -> list[DetectionRecord]:
    result = await session.execute(
        select(DetectionRecord).order_by(DetectionRecord.created_at.desc())
    )
    return list(result.scalars())


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


async def close_connections() -> None:
    await engine.dispose()
    await neo4j_driver.close()
