import asyncio
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers.media import cleanup, router as media_router
from handlers.start import router as start_router


class HealthHandler(BaseHTTPRequestHandler):
    """Minimal HTTP health endpoint for Render Web Service port checks."""

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK - Universal File Utility Bot is running\\n")

    def log_message(self, format: str, *args) -> None:
        # Avoid cluttering logs with routine health-check requests.
        return


def start_health_server() -> HTTPServer:
    """Bind the HTTP health endpoint to Render's assigned port."""
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logging.getLogger(__name__).info("Health check server listening on port %d", port)
    return server


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # Render Web Services require an HTTP listener on the assigned PORT.
    health_server = start_health_server()
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(media_router)
    dp.shutdown.register(cleanup)

    try:
        # Keep pending updates on restart; do not silently discard user messages.
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        health_server.shutdown()
        health_server.server_close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
