from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


DATABASE_URL = "postgresql+asyncpg://orders:orders@localhost:5401/orders"


engine = create_async_engine(url=DATABASE_URL, echo=True)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session
