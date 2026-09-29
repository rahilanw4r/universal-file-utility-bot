from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Welcome to Universal File Utility Bot!\n\n"
        "Send me an image, PDF, or multiple files and I’ll help you convert, merge, or archive them.\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show help"
    )


@router.message(lambda message: message.text and message.text.startswith("/help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "How to use the bot:\n\n"
        "• Send an image to use image conversion.\n"
        "• Send multiple PDFs together, then use /mergepdf.\n"
        "• Send multiple files, then use /zip.\n\n"
        "Supported image formats: PNG, JPG/JPEG, WebP."
    )
