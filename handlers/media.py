from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

from aiogram import Router
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import MAX_FILE_SIZE_BYTES, TEMP_DIR
from services.file_compressor import create_zip
from services.image_converter import convert_image
from services.pdf_tools import images_to_pdf, merge_pdfs
from utils.file_manager import remove_path

router = Router()

user_batches: dict[int, list[Path]] = {}
user_batch_types: dict[int, str] = {}
job_semaphore = asyncio.Semaphore(2)


def action_keyboard():
    builder = InlineKeyboardBuilder()
    for label, callback in [
        ("PNG", "img:png"),
        ("JPG", "img:jpg"),
        ("WebP", "img:webp"),
    ]:
        builder.button(text=label, callback_data=callback)
    builder.adjust(3)
    return builder.as_markup()


async def check_size(message: Message, size: int | None) -> bool:
    if size is not None and size > MAX_FILE_SIZE_BYTES:
        await message.answer(
            f"File is too large. Maximum supported input size is "
            f"{MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
        )
        return False
    return True


@router.message(lambda message: message.document is not None)
async def document_handler(message: Message) -> None:
    document = message.document
    if not await check_size(message, document.file_size):
        return

    user_id = message.from_user.id
    workdir = TEMP_DIR / str(user_id)
    workdir.mkdir(parents=True, exist_ok=True)

    suffix = Path(document.file_name or "file.bin").suffix.lower()
    destination = workdir / f"{uuid4().hex}{suffix or '.bin'}"

    async with job_semaphore:
        try:
            tg_file = await message.bot.get_file(document.file_id)
            await message.bot.download(tg_file, destination)

            batch = user_batches.setdefault(user_id, [])
            batch.append(destination)

            file_type = "pdf" if suffix == ".pdf" else "other"
            user_batch_types[user_id] = file_type

            await message.answer(
                f"Received {document.file_name or 'file'}\n"
                f"Batch now contains {len(batch)} file(s).\n\n"
                "Use /mergepdf for PDFs or /zip to create a ZIP archive."
            )
        except Exception as exc:
            remove_path(destination)
            await message.answer(f"Could not download the file: {exc}")


@router.message(lambda message: message.photo is not None)
async def photo_handler(message: Message) -> None:
    photo = message.photo[-1]
    if not await check_size(message, photo.file_size):
        return

    user_id = message.from_user.id
    workdir = TEMP_DIR / str(user_id)
    workdir.mkdir(parents=True, exist_ok=True)
    source = workdir / f"{uuid4().hex}.jpg"

    async with job_semaphore:
        try:
            tg_file = await message.bot.get_file(photo.file_id)
            await message.bot.download(tg_file, source)
            await message.answer(
                "Choose the output format:",
                reply_markup=action_keyboard(),
            )
        except Exception as exc:
            remove_path(source)
            await message.answer(f"Could not process the image: {exc}")


@router.callback_query(lambda callback: callback.data and callback.data.startswith("img:"))
async def image_conversion_callback(callback: CallbackQuery) -> None:
    if not callback.message:
        await callback.answer()
        return

    target_format = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    workdir = TEMP_DIR / str(user_id)

    images = sorted(workdir.glob("*.jpg"))
    if not images:
        await callback.answer("Image expired. Please send it again.", show_alert=True)
        return

    source = images[-1]
    target = workdir / f"{uuid4().hex}.{target_format}"

    async with job_semaphore:
        try:
            convert_image(source, target, target_format)
            await callback.message.answer_document(
                FSInputFile(target),
                caption=f"Converted to {target_format.upper()}",
            )
        except Exception as exc:
            await callback.message.answer(f"Conversion failed: {exc}")
        finally:
            remove_path(source)
            remove_path(target)

    await callback.answer()


@router.message(lambda message: message.text and message.text.strip().lower() == "/mergepdf")
async def merge_pdf_handler(message: Message) -> None:
    user_id = message.from_user.id
    batch = user_batches.get(user_id, [])

    if len(batch) < 2 or not all(path.suffix.lower() == ".pdf" for path in batch):
        await message.answer("Send at least two PDF files first, then use /mergepdf.")
        return

    target = batch[0].parent / f"{uuid4().hex}.pdf"

    async with job_semaphore:
        try:
            merge_pdfs(batch, target)
            await message.answer_document(FSInputFile(target), caption="Merged PDF")
        except Exception as exc:
            await message.answer(f"PDF merge failed: {exc}")
        finally:
            for path in batch:
                remove_path(path)
            remove_path(target)
            user_batches.pop(user_id, None)
            user_batch_types.pop(user_id, None)


@router.message(lambda message: message.text and message.text.strip().lower() == "/zip")
async def zip_handler(message: Message) -> None:
    user_id = message.from_user.id
    batch = user_batches.get(user_id, [])

    if not batch:
        await message.answer("Send one or more files first, then use /zip.")
        return

    target = batch[0].parent / f"{uuid4().hex}.zip"

    async with job_semaphore:
        try:
            create_zip(batch, target)
            await message.answer_document(FSInputFile(target), caption="ZIP archive")
        except Exception as exc:
            await message.answer(f"ZIP creation failed: {exc}")
        finally:
            for path in batch:
                remove_path(path)
            remove_path(target)
            user_batches.pop(user_id, None)
            user_batch_types.pop(user_id, None)
