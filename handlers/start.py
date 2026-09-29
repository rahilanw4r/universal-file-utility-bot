from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Universal File Utility Bot\n\n"
        "Send an image to convert formats or optimize its file size using the size buttons. Send documents to build a batch.\n\n"
        "Commands:\n"
        "/zip — package your current batch into a ZIP\n"
        "/mergepdf — merge 2 or more PDF documents\n"
        "/clear — discard your current batch\n"
        "/help — show this guide\n\n"
        "Current hosted-Bot-API input limit: 19 MB per file. Send images as photos for conversion; "
        "send PDFs and other files as documents."
    )


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "How to use the bot:\n\n"
        "1. Send a photo and tap PNG, JPG, or WebP to convert it, or choose a KB/MB target to compress it.\n"
        "2. Send PDF documents, then /mergepdf to combine them in upload order.\n"
        "3. Send files, then /zip to archive the batch.\n"
        "4. Use /clear to remove the batch without processing.\n\n"
        "Limits: 19 MB per input file and 8 files per batch. Compression targets are maximums, not guaranteed exact sizes; reducing size can reduce image quality. "
        "Background removal needs the optional requirements-ai.txt install and may be resource-intensive. Only use files you have the right to process."
    )
