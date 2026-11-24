import hashlib
import hmac
import os
import re
import secrets
import warnings
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from pathlib import PurePosixPath
from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Float, Integer, String, inspect, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from slugify import slugify
from starlette.middleware.sessions import SessionMiddleware


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
DATABASE_URL = "sqlite+aiosqlite:////data/database.db"
SESSION_SECRET = os.getenv("SESSION_SECRET") or secrets.token_urlsafe(32)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip().lower()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ADMIN_NICKNAME = os.getenv("ADMIN_NICKNAME", "Specs Admin").strip()
MAX_IMAGE_SIZE = 2 * 1024 * 1024
IMAGE_FORMATS = {".jpg": "JPEG", ".png": "PNG", ".webp": "WEBP"}
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)


@dataclass(frozen=True)
class ValidatedImage:
    content: bytes
    extension: str


def image_slug(value: str) -> str:
    slug = slugify(value, separator="_", lowercase=True, max_length=180)
    if not slug:
        raise HTTPException(
            status_code=422, detail="Из названия не удалось создать имя файла"
        )
    return slug


async def validate_image_upload(upload: UploadFile | None) -> ValidatedImage | None:
    if upload is None:
        return None

    try:
        if not upload.filename:
            return None
        extension = Path(upload.filename).suffix.lower()
        expected_format = IMAGE_FORMATS.get(extension)
        if expected_format is None:
            raise HTTPException(
                status_code=415,
                detail="Разрешены только изображения .jpg, .png и .webp",
            )
        if upload.size is not None and upload.size > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=413, detail="Максимальный размер файла — 2 МиБ")

        content = await upload.read(MAX_IMAGE_SIZE + 1)
        if len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=413, detail="Максимальный размер файла — 2 МиБ")
        if not content:
            raise HTTPException(status_code=422, detail="Файл изображения пуст")

        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as image:
                if image.format != expected_format:
                    raise HTTPException(
                        status_code=415,
                        detail="Содержимое файла не соответствует его формату",
                    )
                image.verify()
        return ValidatedImage(content=content, extension=extension)
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        SyntaxError,
        UnidentifiedImageError,
    ):
        raise HTTPException(
            status_code=415, detail="Файл не является корректным изображением"
        ) from None
    finally:
        await upload.close()


def stage_image(image: ValidatedImage) -> Path:
    staging_dir = ROOT / ".upload-staging"
    staging_dir.mkdir(parents=True, exist_ok=True)
    staged = staging_dir / f"{secrets.token_hex(16)}.tmp"
    try:
        with staged.open("xb") as file:
            file.write(image.content)
    except OSError:
        staged.unlink(missing_ok=True)
        raise
    return staged


def image_files_for_stem(directory: Path, stem: str) -> list[Path]:
    if not directory.exists():
        return []
    return [
        path
        for path in directory.iterdir()
        if path.is_file()
        and path.stem.casefold() == stem.casefold()
        and path.suffix.lower() in IMAGE_FORMATS
    ]


def stored_image_file(relative_path: str, expected_directory: str) -> Path | None:
    if not relative_path or "\\" in relative_path:
        return None
    expected_root = (STATIC_DIR / "images" / expected_directory).resolve()
    candidate = (STATIC_DIR / relative_path).resolve()
    try:
        candidate.relative_to(expected_root)
    except ValueError:
        return None
    if candidate.suffix.lower() not in IMAGE_FORMATS:
        return None
    return candidate


def discard_file(path: Path | None) -> None:
    if path is not None and path.exists():
        path.unlink()


def promote_staged_image(staged: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.resolve().relative_to((STATIC_DIR / "images").resolve())
    os.replace(staged, target)


class Base(DeclarativeBase):
    pass


class Gpu(Base):
    __tablename__ = "gpus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_product_name: Mapped[str] = mapped_column(String(255), unique=True)
    technical_name: Mapped[str] = mapped_column(String(255))
    vram_type: Mapped[str] = mapped_column(String(32))
    vram_volume: Mapped[int] = mapped_column(Integer)
    vram_clock_frequency: Mapped[int] = mapped_column(Integer)
    core_clock_frequency: Mapped[int] = mapped_column(Integer)
    gpu_image_dir_path: Mapped[str] = mapped_column(String(255), default="")


class Cpu(Base):
    __tablename__ = "cpus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_product_name: Mapped[str] = mapped_column(String(255), unique=True)
    technical_name: Mapped[str] = mapped_column(String(255))
    cores_count: Mapped[int] = mapped_column(Integer)
    threads_count: Mapped[int] = mapped_column(Integer)
    clock_frequency: Mapped[float] = mapped_column(Float)
    cpu_image_dir_path: Mapped[str] = mapped_column(String(255), default="")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String(33), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    avatar_dir_path: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(16), default="user", server_default="user")


async def get_db():
    async with async_session() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]
app = FastAPI(title="SPECS-MASTER")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="specs_master_session",
    same_site="lax",
    https_only=os.getenv("SESSION_HTTPS_ONLY", "false").lower() == "true",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
async def initialize_database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

        def ensure_user_role(sync_connection):
            inspector = inspect(sync_connection)
            if "users" in inspector.get_table_names():
                columns = {column["name"] for column in inspector.get_columns("users")}
                if "role" not in columns:
                    sync_connection.execute(
                        text(
                            "ALTER TABLE users ADD COLUMN role "
                            "VARCHAR(16) NOT NULL DEFAULT 'user'"
                        )
                    )

        await connection.run_sync(ensure_user_role)

    if not ADMIN_EMAIL and ADMIN_PASSWORD:
        raise RuntimeError("ADMIN_EMAIL is required when ADMIN_PASSWORD is configured")
    if ADMIN_EMAIL:
        if len(ADMIN_PASSWORD) < 10:
            raise RuntimeError(
                "Set ADMIN_PASSWORD to at least 10 characters to bootstrap the admin account"
            )
        if len(ADMIN_NICKNAME) < 2 or len(ADMIN_NICKNAME) > 33:
            raise RuntimeError("ADMIN_NICKNAME must contain 2 to 33 characters")
        async with async_session() as session:
            result = await session.execute(select(User).where(User.email == ADMIN_EMAIL))
            admin = result.scalar_one_or_none()
            if admin is None:
                admin = User(
                    nickname=ADMIN_NICKNAME,
                    email=ADMIN_EMAIL,
                    password=hash_password(ADMIN_PASSWORD),
                    role="admin",
                )
                session.add(admin)
            elif not verify_password(ADMIN_PASSWORD, admin.password):
                raise RuntimeError(
                    "ADMIN_PASSWORD does not match the account configured by ADMIN_EMAIL"
                )
            admin.role = "admin"
            await session.commit()


def hash_password(password: str) -> str:
    rounds = 310_000
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("ascii"), rounds
    ).hex()
    return f"pbkdf2_sha256${rounds}${salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, rounds, salt, expected = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("ascii"), int(rounds)
        ).hex()
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def user_data(user: User) -> dict:
    return {
        "id": user.id,
        "nickname": user.nickname,
        "email": user.email,
        "role": user.role,
        "avatar_dir_path": user.avatar_dir_path,
    }


def cpu_data(cpu: Cpu) -> dict:
    return {
        "id": cpu.id,
        "full_product_name": cpu.full_product_name,
        "technical_name": cpu.technical_name,
        "cores_count": cpu.cores_count,
        "threads_count": cpu.threads_count,
        "clock_frequency": cpu.clock_frequency,
        "cpu_image_dir_path": cpu.cpu_image_dir_path,
    }


def gpu_data(gpu: Gpu) -> dict:
    return {
        "id": gpu.id,
        "full_product_name": gpu.full_product_name,
        "technical_name": gpu.technical_name,
        "vram_type": gpu.vram_type,
        "vram_volume": gpu.vram_volume,
        "vram_clock_frequency": gpu.vram_clock_frequency,
        "core_clock_frequency": gpu.core_clock_frequency,
        "gpu_image_dir_path": gpu.gpu_image_dir_path,
    }


async def get_current_user(request: Request, db: DbSession) -> User:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(status_code=401, detail="Войдите в аккаунт")
    user = await db.get(User, user_id)
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Войдите в аккаунт")
    return user


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ только для администратора")
    return user


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=128)


def validate_email(email: str) -> str:
    normalized = email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
        raise HTTPException(status_code=422, detail="Укажите корректный email")
    return normalized


async def ensure_component_image_slot(
    db: AsyncSession, model, directory: Path, technical_name: str
) -> None:
    existing = await db.execute(
        select(model.id).where(model.technical_name == technical_name)
    )
    if existing.scalar_one_or_none() or image_files_for_stem(directory, technical_name):
        raise HTTPException(
            status_code=409,
            detail="Техническое имя уже используется; измените название комплектующей",
        )


async def ensure_avatar_slot(
    db: AsyncSession,
    slug: str,
    user_id: int | None = None,
    current_path: str = "",
) -> None:
    query = select(User.avatar_dir_path).where(User.avatar_dir_path != "")
    if user_id is not None:
        query = query.where(User.id != user_id)
    stored_paths = (await db.execute(query)).scalars().all()
    if any(
        PurePosixPath(path).parent.as_posix() == "images/users"
        and PurePosixPath(path).stem.casefold() == slug.casefold()
        for path in stored_paths
    ):
        raise HTTPException(status_code=409, detail="Имя файла аватара уже занято")

    directory = STATIC_DIR / "images" / "users"
    current_file = stored_image_file(current_path, "users")
    if any(
        current_file is None or path.resolve() != current_file.resolve()
        for path in image_files_for_stem(directory, slug)
    ):
        raise HTTPException(status_code=409, detail="Имя файла аватара уже занято")


def store_new_image(image: ValidatedImage, target: Path) -> None:
    if target.exists():
        raise HTTPException(status_code=409, detail="Изображение с таким именем уже существует")
    staged = stage_image(image)
    try:
        promote_staged_image(staged, target)
    finally:
        discard_file(staged)


@app.get("/api/cpus")
async def get_cpus(db: DbSession):
    result = await db.execute(select(Cpu).order_by(Cpu.full_product_name))
    return [cpu_data(cpu) for cpu in result.scalars().all()]


@app.get("/api/gpus")
async def get_gpus(db: DbSession):
    result = await db.execute(select(Gpu).order_by(Gpu.full_product_name))
    return [gpu_data(gpu) for gpu in result.scalars().all()]


async def compare_items(
    model,
    serializer,
    first_id: int,
    second_id: int,
    db: AsyncSession,
) -> list[dict]:
    if first_id == second_id:
        raise HTTPException(status_code=422, detail="Выберите два разных компонента")
    result = await db.execute(
        select(model).where(model.id.in_([first_id, second_id]))
    )
    items = {item.id: item for item in result.scalars().all()}
    if len(items) != 2:
        raise HTTPException(status_code=404, detail="Компонент не найден")
    return [serializer(items[first_id]), serializer(items[second_id])]


@app.get("/api/cpus/compare")
async def compare_cpus(
    db: DbSession,
    first_id: Annotated[int, Query(gt=0)],
    second_id: Annotated[int, Query(gt=0)],
):
    return {
        "items": await compare_items(Cpu, cpu_data, first_id, second_id, db)
    }


@app.get("/api/gpus/compare")
async def compare_gpus(
    db: DbSession,
    first_id: Annotated[int, Query(gt=0)],
    second_id: Annotated[int, Query(gt=0)],
):
    return {
        "items": await compare_items(Gpu, gpu_data, first_id, second_id, db)
    }


@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    db: DbSession,
    nickname: Annotated[str, Form(min_length=2, max_length=33)],
    email: Annotated[str, Form(min_length=5, max_length=255)],
    password: Annotated[str, Form(min_length=10, max_length=128)],
    avatar: Annotated[UploadFile | None, File()] = None,
):
    email = validate_email(email)
    nickname = nickname.strip()
    if not 2 <= len(nickname) <= 33:
        raise HTTPException(status_code=422, detail="Имя пользователя слишком короткое")
    uploaded_avatar = await validate_image_upload(avatar)
    avatar_path = ""
    avatar_target = None
    if uploaded_avatar is not None:
        slug = image_slug(nickname)
        await ensure_avatar_slot(db, slug)
        avatar_target = STATIC_DIR / "images" / "users" / (
            f"{slug}{uploaded_avatar.extension}"
        )
        store_new_image(uploaded_avatar, avatar_target)
        avatar_path = avatar_target.relative_to(STATIC_DIR).as_posix()

    user = User(
        nickname=nickname,
        email=email,
        password=hash_password(password),
        avatar_dir_path=avatar_path,
    )
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        discard_file(avatar_target)
        raise HTTPException(
            status_code=409, detail="Такой email или никнейм уже зарегистрирован"
        ) from None
    except SQLAlchemyError:
        await db.rollback()
        discard_file(avatar_target)
        raise
    request.session.clear()
    request.session["user_id"] = user.id
    return {"user": user_data(user)}


@app.post("/api/auth/login")
async def login(payload: LoginInput, request: Request, db: DbSession):
    email = validate_email(payload.email)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    request.session.clear()
    request.session["user_id"] = user.id
    return {"user": user_data(user)}


@app.get("/api/auth/me")
async def current_user(request: Request, db: DbSession):
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int):
        return {"user": None}
    user = await db.get(User, user_id)
    if user is None:
        request.session.clear()
        return {"user": None}
    return {"user": user_data(user)}


@app.post("/api/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@app.put("/api/auth/avatar")
async def update_avatar(
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
    image: Annotated[UploadFile, File()],
):
    uploaded_image = await validate_image_upload(image)
    if uploaded_image is None:
        raise HTTPException(status_code=422, detail="Выберите изображение")

    slug = image_slug(user.nickname)
    await ensure_avatar_slot(db, slug, user.id, user.avatar_dir_path)
    target = STATIC_DIR / "images" / "users" / f"{slug}{uploaded_image.extension}"
    target_relative_path = target.relative_to(STATIC_DIR).as_posix()
    previous_path = user.avatar_dir_path
    previous_file = stored_image_file(previous_path, "users")
    staged = stage_image(uploaded_image)
    backup = None

    try:
        if target.exists():
            if previous_file is None or target.resolve() != previous_file.resolve():
                raise HTTPException(status_code=409, detail="Имя файла аватара уже занято")
            backup = target.with_name(f".{target.name}.{secrets.token_hex(8)}.bak")
            os.replace(target, backup)
        promote_staged_image(staged, target)
    except OSError:
        discard_file(staged)
        if backup is not None and backup.exists():
            discard_file(target)
            os.replace(backup, target)
        raise
    except HTTPException:
        discard_file(staged)
        raise

    user.avatar_dir_path = target_relative_path
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        discard_file(target)
        if backup is not None and backup.exists():
            os.replace(backup, target)
        discard_file(staged)
        raise

    discard_file(staged)
    discard_file(backup)
    if previous_file is not None and previous_file.resolve() != target.resolve():
        discard_file(previous_file)
    return {"user": user_data(user)}


@app.post("/api/admin/cpus", status_code=status.HTTP_201_CREATED)
async def create_cpu(
    db: DbSession,
    _: Annotated[User, Depends(require_admin)],
    full_product_name: Annotated[str, Form(min_length=2, max_length=255)],
    cores_count: Annotated[int, Form(gt=0)],
    threads_count: Annotated[int, Form(gt=0)],
    clock_frequency: Annotated[float, Form(gt=0)],
    image: Annotated[UploadFile | None, File()] = None,
):
    full_product_name = full_product_name.strip()
    if len(full_product_name) < 2:
        raise HTTPException(status_code=422, detail="Укажите название процессора")
    technical_name = image_slug(full_product_name)
    await ensure_component_image_slot(
        db, Cpu, STATIC_DIR / "images" / "site" / "cpus", technical_name
    )
    uploaded_image = await validate_image_upload(image)
    image_path = ""
    image_target = None
    if uploaded_image is not None:
        image_target = STATIC_DIR / "images" / "site" / "cpus" / (
            f"{technical_name}{uploaded_image.extension}"
        )
        store_new_image(uploaded_image, image_target)
        image_path = image_target.relative_to(STATIC_DIR).as_posix()

    cpu = Cpu(
        full_product_name=full_product_name,
        technical_name=technical_name,
        cores_count=cores_count,
        threads_count=threads_count,
        clock_frequency=clock_frequency,
        cpu_image_dir_path=image_path,
    )
    db.add(cpu)
    try:
        await db.commit()
        await db.refresh(cpu)
    except IntegrityError:
        await db.rollback()
        discard_file(image_target)
        raise HTTPException(
            status_code=409, detail="Процессор с таким названием уже существует"
        ) from None
    except SQLAlchemyError:
        await db.rollback()
        discard_file(image_target)
        raise
    return cpu_data(cpu)


@app.post("/api/admin/gpus", status_code=status.HTTP_201_CREATED)
async def create_gpu(
    db: DbSession,
    _: Annotated[User, Depends(require_admin)],
    full_product_name: Annotated[str, Form(min_length=2, max_length=255)],
    vram_type: Annotated[str, Form()],
    vram_volume: Annotated[int, Form(gt=0)],
    vram_clock_frequency: Annotated[int, Form(gt=0)],
    core_clock_frequency: Annotated[int, Form(gt=0)],
    image: Annotated[UploadFile | None, File()] = None,
):
    full_product_name = full_product_name.strip()
    if len(full_product_name) < 2:
        raise HTTPException(status_code=422, detail="Укажите название видеокарты")
    if vram_type not in {"GDDR4", "GDDR5", "GDDR6", "GDDR6X", "GDDR7"}:
        raise HTTPException(status_code=422, detail="Недопустимый тип видеопамяти")
    technical_name = image_slug(full_product_name)
    await ensure_component_image_slot(
        db, Gpu, STATIC_DIR / "images" / "site" / "gpus", technical_name
    )
    uploaded_image = await validate_image_upload(image)
    image_path = ""
    image_target = None
    if uploaded_image is not None:
        image_target = STATIC_DIR / "images" / "site" / "gpus" / (
            f"{technical_name}{uploaded_image.extension}"
        )
        store_new_image(uploaded_image, image_target)
        image_path = image_target.relative_to(STATIC_DIR).as_posix()

    gpu = Gpu(
        full_product_name=full_product_name,
        technical_name=technical_name,
        vram_type=vram_type,
        vram_volume=vram_volume,
        vram_clock_frequency=vram_clock_frequency,
        core_clock_frequency=core_clock_frequency,
        gpu_image_dir_path=image_path,
    )
    db.add(gpu)
    try:
        await db.commit()
        await db.refresh(gpu)
    except IntegrityError:
        await db.rollback()
        discard_file(image_target)
        raise HTTPException(
            status_code=409, detail="Видеокарта с таким названием уже существует"
        ) from None
    except SQLAlchemyError:
        await db.rollback()
        discard_file(image_target)
        raise
    return gpu_data(gpu)


@app.get("/")
async def read_index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/cpus")
async def read_cpus():
    return FileResponse(STATIC_DIR / "cpus.html")


@app.get("/gpus")
async def read_gpus():
    return FileResponse(STATIC_DIR / "gpus.html")


@app.get("/lk")
async def read_profile():
    return FileResponse(STATIC_DIR / "lk.html")


@app.get("/login")
async def read_login():
    return FileResponse(STATIC_DIR / "auth.html")


@app.get("/admin")
async def read_admin(_: Annotated[User, Depends(require_admin)]):
    return FileResponse(ROOT / "templates" / "admin.html")
