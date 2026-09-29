# Universal File Utility Bot

A Telegram bot for common image and document tasks. The project is public and welcomes contributions through GitHub issues and pull requests.

## Features

- Convert photos to PNG, JPG, and WebP.
- Optimize a photo to a requested maximum file size (250 KB, 500 KB, 1 MB, or 2 MB).
- Merge multiple PDF documents in the current batch.
- Package a batch of files into a ZIP archive.
- Clear a user's current batch with /clear.

### Image editing and background removal\n\nSend a photo and use the inline buttons to convert, compress, or apply edits. `/resize 1200 800` resizes the latest available photo to exact dimensions (1–10000 pixels per side). This exact resize may change the original aspect ratio. Basic editing uses Pillow and does not call a paid API.\n\nBackground removal is optional: install it with `python -m pip install -r requirements-ai.txt` before running the bot. The open-source AI model may download on first use and needs extra memory/CPU; it is not installed in the default deployment.\n\n### Image size notes

The size presets are target ceilings, not promises of exact file size. Compression exports JPEG and reduces quality first; if necessary to meet the selected ceiling, it also reduces pixel dimensions. Transparent PNG/WebP conversion preserves alpha; JPEG conversion flattens transparency onto white. Telegram photo uploads may already be resized/compressed; send as a document when you need to preserve original bytes (subject to the bot's input limit).

## Requirements

- Python 3.13 (pinned in .python-version)
- A Telegram bot token from @BotFather

## Run locally

1. Clone the repository and enter its directory.
2. Create and activate a virtual environment.
3. Install dependencies: `python -m pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and set `BOT_TOKEN` to your token.
5. Start: `python bot.py`

Never commit `.env` or share your token. If a token is exposed, revoke it in @BotFather and create a replacement.

## Run with Docker Compose

Install Docker Compose, create `.env` with `BOT_TOKEN=your_token`, then run:

```sh
docker compose up --build -d
docker compose logs -f bot
```

Stop with `docker compose down`. The bot uses long polling; run only one active instance for a given bot token.

## Deploy on Render

Create a **Web Service** connected to this repository and the main branch.

- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `python bot.py`
- Environment variable: `BOT_TOKEN` = your token
- Root directory: leave blank (repository root)

The bot uses long polling plus a small HTTP health endpoint for Render. Use one running instance for the bot token; do not run multiple replicas simultaneously.

## Current limits and operational notes

- Hosted Telegram Bot API input download limit is configured conservatively at 19 MB per file.
- Maximum batch size: 8 files.
- Batch/session data is currently held in process memory; active batches are lost on restart. Local temporary files are not a durable storage layer.
- Temporary files are cleaned on orderly shutdown; a crash can leave stale files. Periodic cleanup and persistent session storage are future hardening work.
- This is an early-stage project, not yet validated for high-volume or multi-instance production. Before scaling, add persistent sessions, queueing, rate limits, storage lifecycle controls, and monitoring.

## Tests

Run locally with:

```sh
python -m unittest discover -s tests -v
```

GitHub Actions runs this test command for pushes to `main` and pull requests targeting `main`.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md). Use [Issues](../../issues) for bugs and feature ideas, and submit a pull request from your fork. Pull requests are reviewed before merging.

## License

MIT. See [LICENSE](LICENSE).
