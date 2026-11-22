from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, select


DB_URL = "mysql+aiomysql://root:@MySQL-8.4:3306/specs_master_db"

engine = create_async_engine(DB_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Gpu(Base):
    __tablename__ = 'gpus'

    id: Mapped[int] = mapped_column(primary_key=True)
    full_product_name: Mapped[str] = mapped_column(String(255))
    technical_name: Mapped[str] = mapped_column(String(255))


async def get_db():
    async with async_session() as session:
        yield session


app = FastAPI()

@app.get('/api/gpus')
async def get_gpus(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Gpu))
    items = result.scalars().all()

    return items


@app.get('/')
async def read_index():
    return FileResponse('static/index.html')


@app.get('/cpus')
async def read_cpus():
    return FileResponse('static/cpus.html')


@app.get('/gpus')
async def read_gpus():
    return FileResponse('static/gpus.html')


app.mount('/static', StaticFiles(directory='static'), name='static')