from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path
from uuid import uuid4

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import MAX_FILE_SIZE_BYTES, MAX_BATCH_FILES, TEMP_DIR
from services.file_compressor import create_zip
from services.image_converter import compress_to_target, convert_image, increase_to_target
from services.image_editing import edit_image, remove_background
from services.pdf_tools import merge_pdfs
from utils.file_manager import remove_path, safe_suffix

router = Router()
log = logging.getLogger(__name__)

# State is isolated per Telegram user within this single bot process.
# For multiple replicas, move sessions/locks to Redis or a database.
_batches: dict[int, list[Path]] = {}
_image_tokens: dict[str, tuple[int, Path]] = {}
_user_locks: dict[int, asyncio.Lock] = {}
_job_slots = asyncio.Semaphore(2)
_pending_input: dict[int, tuple[str, str]] = {}


def _lock_for(user_id: int) -> asyncio.Lock:
    return _user_locks.setdefault(user_id, asyncio.Lock())


def _keyboard(token: str):
    builder = InlineKeyboardBuilder()
    for label, fmt in (("PNG", "png"), ("JPG", "jpg"), ("WebP", "webp")):
        builder.button(text=label, callback_data=f"img:{token}:{fmt}")
    for label, kb in (("≤250 KB", "250"), ("≤500 KB", "500"), ("≤1 MB", "1024"), ("≤2 MB", "2048")):
        builder.button(text=label, callback_data=f"img:{token}:kb{kb}")
    for label, action in (("Resize", "resize"), ("Custom KB/MB", "customsize"), ("Rotate 90°", "rotate"), ("Mirror", "flip"), ("Flip", "flop"), ("Grayscale", "gray"), ("Sepia", "sepia"), ("Blur", "blur"), ("Sharpen", "sharpen"), ("Brighten", "bright"), ("Darken", "dark"), ("Contrast", "contrast"), ("Saturate", "saturate"), ("Auto contrast", "autocontrast"), ("Remove BG", "bg")):
        builder.button(text=label, callback_data=f"edit:{token}:{action}")
    builder.adjust(3, 2, 2, 2, 2, 2, 2, 2)
    return builder.as_markup()


async def _reject_size(message: Message, size: int | None) -> bool:
    if size is not None and size > MAX_FILE_SIZE_BYTES:
        await message.answer(f"Input limit is {MAX_FILE_SIZE_BYTES // 1048576} MB per file. Send a smaller file.")
        return True
    return False


async def _download(message: Message, file_id: str, dest: Path) -> None:
    tg_file = await message.bot.get_file(file_id)
    await message.bot.download(tg_file, destination=dest)
    # Defense in depth: reject missing/incorrect Telegram metadata after download.
    if not dest.is_file() or dest.stat().st_size > MAX_FILE_SIZE_BYTES:
        remove_path(dest)
        raise ValueError("File exceeds the configured input limit.")


@router.message(lambda m: m.document is not None)
async def document_handler(message: Message) -> None:
    if not message.from_user or not message.document:
        return
    doc = message.document
    if await _reject_size(message, doc.file_size):
        return
    user_id = message.from_user.id
    workdir = TEMP_DIR / str(user_id)
    workdir.mkdir(parents=True, exist_ok=True)
    dest = workdir / f"{uuid4().hex}{safe_suffix(doc.file_name or 'file.bin')}"
    try:
        async with _user_locks.setdefault(user_id, asyncio.Lock()):
            if len(_batches.get(user_id, [])) >= MAX_BATCH_FILES:
                await message.answer(f"Batch limit is {MAX_BATCH_FILES} files. Use /zip or /mergepdf to finish the current batch.")
                return
            async with _job_slots:
                await _download(message, doc.file_id, dest)
            _batches.setdefault(user_id, []).append(dest)
            await message.answer(
                f"Added: {Path(doc.file_name or 'file').name}\n"
                f"Batch: {len(_batches[user_id])}/{MAX_BATCH_FILES}\n"
                "Use /zip to archive files, /mergepdf for 2+ PDFs, or /clear to discard the batch."
            )
    except Exception:
        remove_path(dest)
        log.exception("Document handling failed for user_id=%s", user_id)
        await message.answer("I couldn't download or add that file. Check the file size and try again.")


@router.message(lambda m: m.photo is not None)
async def photo_handler(message: Message) -> None:
    if not message.from_user or not message.photo:
        return
    photo = message.photo[-1]
    if await _reject_size(message, photo.file_size):
        return
    user_id = message.from_user.id
    workdir = TEMP_DIR / str(user_id)
    workdir.mkdir(parents=True, exist_ok=True)
    source = workdir / f"{uuid4().hex}.img"
    token = uuid4().hex[:16]
    try:
        async with _job_slots:
            await _download(message, photo.file_id, source)
        _image_tokens[token] = (user_id, source)
        await message.answer("Choose output format:", reply_markup=_keyboard(token))
    except Exception:
        remove_path(source)
        log.exception("Photo download failed for user_id=%s", user_id)
        await message.answer("I couldn't download that image. Please try sending it again.")


@router.callback_query(lambda c: c.data is not None and c.data.startswith("img:"))
async def image_conversion_callback(callback: CallbackQuery) -> None:
    if not callback.data or not callback.message:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Invalid action.", show_alert=True)
        return
    _, token, fmt = parts
    entry = _image_tokens.get(token)
    size_request = fmt.startswith("kb") and fmt[2:].isdigit()
    if (fmt not in {"png", "jpg", "webp"} and not size_request) or not entry or entry[0] != callback.from_user.id:
        await callback.answer("This image action is invalid or expired.", show_alert=True)
        return
    _image_tokens.pop(token, None)
    source = entry[1]
    target = source.with_name(f"{uuid4().hex}.jpg" if size_request else f"{uuid4().hex}.{fmt}")
    try:
        async with _job_slots:
            if size_request:
                actual_bytes = await asyncio.to_thread(compress_to_target, source, target, int(fmt[2:]) * 1024)
            else:
                await asyncio.to_thread(convert_image, source, target, fmt)
                actual_bytes = target.stat().st_size
        if actual_bytes > MAX_FILE_SIZE_BYTES:
            await callback.message.answer("Output exceeds the bot's send limit. Choose a smaller target size.")
        else:
            caption = (f"JPEG optimized: {actual_bytes / 1024:.1f} KB (requested ≤ {int(fmt[2:])} KB)."
                       if size_request else f"Converted to {fmt.upper()} ({actual_bytes / 1024:.1f} KB)")
            await callback.message.answer_document(FSInputFile(target), caption=caption)
    except Exception:
        log.exception("Image conversion failed for user_id=%s", callback.from_user.id)
        await callback.message.answer("Image conversion failed. Try another image or format.")
    finally:
        remove_path(source)
        remove_path(target)
    await callback.answer()


@router.callback_query(lambda c: c.data is not None and c.data.startswith("edit:"))
async def image_edit_callback(callback: CallbackQuery) -> None:
    if not callback.data or not callback.message:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Invalid action.", show_alert=True)
        return
    _, token, action = parts
    entry = _image_tokens.get(token)
    allowed = {"rotate", "flip", "flop", "gray", "invert", "autocontrast", "blur", "sharpen",
               "bright", "dark", "contrast", "saturate", "sepia", "bg", "resize", "customsize"}
    if action not in allowed or not entry or entry[0] != callback.from_user.id:
        await callback.answer("This image action is invalid or expired.", show_alert=True)
        return

    if action in {"resize", "customsize"}:
        _pending_input[callback.from_user.id] = (action, token)
        prompt = ("Resize mode activated. Send dimensions like 1200 800 or 1200x800."
                  if action == "resize" else
                  "Custom size mode activated. Send 500 KB or 2 MB for a maximum size. Use +2 MB for a minimum size.")
        await callback.message.answer(prompt)
        await callback.answer()
        return

    source = entry[1]
    target = source.with_name(f"{uuid4().hex}.png")
    try:
        async with _job_slots:
            if action == "bg":
                await asyncio.to_thread(remove_background, source, target)
            else:
                await asyncio.to_thread(edit_image, source, target, action)
        if target.stat().st_size > MAX_FILE_SIZE_BYTES:
            await callback.message.answer("Edited image exceeds the bot's send limit.")
        else:
            await callback.message.answer_document(FSInputFile(target), caption=f"Image edit: {action}")
    except RuntimeError as exc:
        await callback.message.answer(str(exc))
    except Exception:
        log.exception("Image edit failed for user_id=%s", callback.from_user.id)
        await callback.message.answer("Couldn't edit this image. Try another image.")
    finally:
        remove_path(target)
    await callback.answer()


@router.message(lambda m: m.text and m.from_user and m.from_user.id in _pending_input)
async def custom_image_input_handler(message: Message) -> None:
    user_id = message.from_user.id
    action, token = _pending_input.pop(user_id)
    entry = _image_tokens.get(token)
    if not entry or entry[0] != user_id:
        await message.answer("That image session expired. Send the image again.")
        return
    source = entry[1]

    if action == "resize":
        raw = (message.text or "").lower().replace("×", "x").replace(",", " ")
        parts = raw.replace("x", " ").split()
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            _pending_input[user_id] = (action, token)
            await message.answer("Invalid dimensions. Send them like 1200 800 or 1200x800.")
            return
        width, height = map(int, parts)
        target = source.with_name(f"{uuid4().hex}.png")
        try:
            async with _job_slots:
                await asyncio.to_thread(edit_image, source, target, "resize", width, height)
            if target.stat().st_size > MAX_FILE_SIZE_BYTES:
                await message.answer("The resized image is too large to send.")
            else:
                await message.answer_document(FSInputFile(target), caption=f"Resized to {width} × {height} px")
        except ValueError as exc:
            await message.answer(str(exc))
            _pending_input[user_id] = (action, token)
        except Exception:
            log.exception("Custom resize failed for user_id=%s", user_id)
            await message.answer("Couldn't resize this image.")
        finally:
            remove_path(target)
            _image_tokens.pop(token, None)
            remove_path(source)
        return

    raw = (message.text or "").strip().lower()
    minimum = raw.startswith("+")
    raw = raw.lstrip("+").strip()
    import re
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(kb|kib|mb|mib)", raw)
    if not match:
        _pending_input[user_id] = (action, token)
        await message.answer("Invalid size. Example: 500 KB, 2 MB, or +2 MB.")
        return
    value, unit = float(match.group(1)), match.group(2)
    multiplier = 1024 if unit in {"kb", "kib"} else 1024 * 1024
    target_bytes = int(value * multiplier)
    if target_bytes < 10 * 1024 or target_bytes > MAX_FILE_SIZE_BYTES:
        _pending_input[user_id] = (action, token)
        await message.answer(f"Choose between 10 KB and {MAX_FILE_SIZE_BYTES // 1048576} MB.")
        return

    target = source.with_name(f"{uuid4().hex}.jpg")
    try:
        async with _job_slots:
            if minimum:
                actual = await asyncio.to_thread(increase_to_target, source, target, target_bytes)
            else:
                actual = await asyncio.to_thread(compress_to_target, source, target, target_bytes)
        if actual > MAX_FILE_SIZE_BYTES:
            await message.answer(f"Result is {actual / 1024 / 1024:.2f} MB, above the bot send limit. Try a smaller target.")
            return
        await message.answer_document(FSInputFile(target),
            caption=f"JPEG: {actual / 1024:.1f} KB (target {'≥' if minimum else '≤'} {value:g} {unit.upper()})")
    except Exception:
        log.exception("Custom size processing failed for user_id=%s", user_id)
        await message.answer("Couldn't reach that file-size target with this image.")
    finally:
        remove_path(target)
        _image_tokens.pop(token, None)
        remove_path(source)


async def _take_batch(user_id: int) -> list[Path]:
    async with _lock_for(user_id):
        return _batches.pop(user_id, [])


@router.message(Command("clear"))
async def clear_handler(message: Message) -> None:
    if not message.from_user:
        return
    files = await _take_batch(message.from_user.id)
    for path in files:
        remove_path(path)
    await message.answer(f"Cleared {len(files)} file(s) from your batch.")


@router.message(Command("zip"))
async def zip_handler(message: Message) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    async with _lock_for(user_id):
        batch = list(_batches.get(user_id, []))
        if not batch:
            await message.answer("Send files first, then use /zip.")
            return
        target = batch[0].parent / f"{uuid4().hex}.zip"
        try:
            async with _job_slots:
                await asyncio.to_thread(create_zip, batch, target)
            if target.stat().st_size > MAX_FILE_SIZE_BYTES:
                await message.answer("The ZIP is larger than the bot's send limit. Try fewer or smaller files.")
                return
            await message.answer_document(FSInputFile(target), caption="Your ZIP archive")
            _batches.pop(user_id, None)
        except Exception:
            log.exception("ZIP creation failed for user_id=%s", user_id)
            await message.answer("Couldn't create the ZIP. Check that the files are valid and try again.")
        finally:
            remove_path(target)
            if user_id not in _batches:
                for path in batch:
                    remove_path(path)


@router.message(Command("mergepdf"))
async def merge_pdf_handler(message: Message) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    async with _lock_for(user_id):
        batch = list(_batches.get(user_id, []))
        if len(batch) < 2 or not all(p.suffix.lower() == ".pdf" for p in batch):
            await message.answer("Send at least two PDF documents (as files), then use /mergepdf.")
            return
        target = batch[0].parent / f"{uuid4().hex}.pdf"
        try:
            async with _job_slots:
                await asyncio.to_thread(merge_pdfs, batch, target)
            if target.stat().st_size > MAX_FILE_SIZE_BYTES:
                await message.answer("Merged PDF is larger than the bot's send limit. Try fewer or smaller PDFs.")
                return
            await message.answer_document(FSInputFile(target), caption="Merged PDF")
            _batches.pop(user_id, None)
        except Exception:
            log.exception("PDF merge failed for user_id=%s", user_id)
            await message.answer("Couldn't merge those PDFs. One may be damaged or encrypted.")
        finally:
            remove_path(target)
            if user_id not in _batches:
                for path in batch:
                    remove_path(path)


async def cleanup() -> None:
    # Best-effort shutdown cleanup; persistent storage/queue is needed for restart recovery.
    for files in _batches.values():
        for path in files:
            remove_path(path)
    for _, path in _image_tokens.values():
        remove_path(path)
    _batches.clear()
    _image_tokens.clear()
    _pending_input.clear()
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
