# Universal File Utility Bot

A Telegram bot for common image and document tasks. The project is public and welcomes contributions through GitHub issues and pull requests.

## Features

- Convert photos to PNG, JPG, and WebP.
- Optimize a photo to a requested maximum file size (250 KB, 500 KB, 1 MB, or 2 MB).
- Merge multiple PDF documents in the current batch.
- Package a batch of files into a ZIP archive.
- Clear a user's current batch with /clear.

### Image size notes

The size presets are target ceilings, not promises of exact file size. Compression exports JPEG and reduces quality first; if necessary to meet the selected ceiling, it also reduces pixel dimensions. Converting a photo to a different format does not inherently increase its visual quality. Telegram photo uploads may already be resized/compressed; send as a document when you need to preserve the original bytes (subject to the bot's input limit).

## Requirements

- Python 3.13 (pinned in .python-version)
- A Telegram bot token from @BotFather

## Run locally

1. Clone the repository and enter its directory.
2. Create and activate a virtual environment.
3. Install dependencies: pip install -r requirements.txt
4. Copy .env.example to .env and set BOT_TOKEN to your token.
5. Start: python bot.py

Never commit .env or share your token. If a token is exposed, revoke it in @BotFather and create a replacement.

## Deploy on Render

Create a **Background Worker** connected to this repository and the main branch.

- Runtime: Python
- Build command: pip install -r requirements.txt
- Start command: python bot.py
- Environment variable: BOT_TOKEN = your token
- Root directory: leave blank (repository root)

This bot uses long polling, so use one running worker instance for the bot token. Do not run multiple replicas of this polling bot simultaneously.

## Current limits and operational notes

- Hosted Telegram Bot API input download limit is configured conservatively at 19 MB per file.
- Maximum batch size: 8 files.
- Batch/session data is currently held in process memory; active batches are lost on restart. Local temporary files are not a durable storage layer.
- This is an early-stage project, not yet validated for high-volume or multi-instance production. Before scaling, add persistent session storage, queueing, rate limits, automated tests, and storage lifecycle controls.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md). Use [Issues](../../issues) for bugs and feature ideas, and submit a pull request from your fork. Pull requests are reviewed before merging.

## License

MIT. See [LICENSE](LICENSE).
