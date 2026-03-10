"""Точка входа FastAPI-приложения."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.queue import router as queue_router
from app.api.reservations import router as reservations_router
from app.core.config import settings

app = FastAPI(
    title="Библиотека Доброграда",
    description="API цифрового сервиса библиотеки с каталогом и доставкой книг",
    version="0.1.0",
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Добавляет security headers для снижения рисков XSS и clickjacking."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(catalog_router)
api_router.include_router(queue_router)
api_router.include_router(reservations_router)
api_router.include_router(admin_router)
app.include_router(api_router)


@app.get("/")
async def root():
    """Проверка доступности API."""
    return {"service": "library-dobrograd", "status": "ok"}


@app.get("/health")
async def health():
    """Эндпоинт для проверки здоровья сервиса."""
    return {"status": "healthy"}


@app.get("/api/health")
async def api_health():
    """Эндпоинт для проверки здоровья API через reverse proxy (/api)."""
    return {"status": "healthy"}
