from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Universal File Utility Bot\\n\\n"
        "Send a photo for format conversion, compression, and editing buttons. "
        "Use /resize WIDTH HEIGHT for custom pixel dimensions. Send documents to build a batch.\\n\\n"
        "Commands:\\n"
        "/resize WIDTH HEIGHT — resize to exact pixel dimensions\\n"
        "/zip — package your current batch into a ZIP\\n"
        "/mergepdf — merge 2 or more PDF documents\\n"
        "/clear — discard your current batch\\n"
        "/help — show this guide\\n\\n"
        "Input limit: 19 MB per file; batch limit: 8 files. "
        "Background removal is an optional free AI feature and needs its separate install."
    )


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "Image tools: PNG/JPG/WebP conversion, size presets, custom resize, rotate, mirror, flip, "
        "grayscale, sepia, blur, sharpen, brighten, darken, contrast, saturation, and auto-contrast. "
        "Tap an edit button after sending a photo.\\n"
        "/resize WIDTH HEIGHT — exact dimensions in pixels (1–10000 each).\\n\\n"
        "Document tools: send 2+ PDFs then /mergepdf, or send files then /zip. "
        "/clear discards the current file batch.\\n\\n"
        "Limits: 19 MB per input file and 8 files per batch. Compression targets are ceilings, "
        "not exact-size guarantees. For free AI background removal, install requirements-ai.txt; "
        "it may use substantial CPU and memory. Only process files you have permission to use."
    )
