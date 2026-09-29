# Universal File Utility Bot

An all-in-one Telegram utility bot for common file operations.

## Initial features

- Image conversion: PNG, JPG/JPEG and WebP
- PDF tools: merge PDFs and create PDFs from images
- ZIP archives: create ZIP files from multiple uploads
- File-size validation and temporary-file cleanup
- Environment-based configuration
- Async Telegram handlers with a simple job-processing foundation

## Run locally

1. Create a bot with @BotFather and copy the token.
2. Create a virtual environment.
3. Install dependencies:
   `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and set `BOT_TOKEN`.
5. Run:
   `python bot.py`

## Render

Use a Python web service/background worker environment as appropriate for your plan. Set `BOT_TOKEN` and other variables in the service environment; never commit `.env`.
