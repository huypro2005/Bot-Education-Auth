from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models  # noqa: F401 — đăng ký ORM với Base trước create_all

from app.api import admin_router
from database import init_db
import asyncio
from contextlib import asynccontextmanager
from bot_handlers.bot_handlers import register_handlers
from telegram.ext import Application
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_app: Application | None = None

async def run_telegram_bot() -> None:
    global telegram_app
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing. Add it to .env.")

    telegram_app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .connect_timeout(20)
        .read_timeout(20)
        .write_timeout(20)
        .pool_timeout(20)
        .get_updates_connect_timeout(20)
        .get_updates_read_timeout(20)
        .get_updates_pool_timeout(20)
        .concurrent_updates(True)
        .http_version("1.1")
        .build()
    )
    register_handlers(telegram_app)
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling(drop_pending_updates=True)

async def stop_telegram_bot() -> None:
    global telegram_app
    if telegram_app:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()
        telegram_app = None

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    bot_task = asyncio.create_task(run_telegram_bot())
    try:
        yield
    finally:
        await stop_telegram_bot()
        bot_task.cancel()



app = FastAPI(
    title="WebCuaMe Admin API",
    description="Admin APIs for whitelist, subject, class, and teaching assignment management.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)