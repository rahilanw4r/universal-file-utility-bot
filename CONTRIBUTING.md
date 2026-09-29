# Contributing

Thanks for helping improve Universal File Utility Bot.

## Before you start
- Open an issue first for a major feature or architectural change.
- Keep changes focused and explain the user-facing behavior.
- Never commit bot tokens, .env files, private user files, or deployment credentials.
- Do not add features that bypass access controls or process files users are not authorized to use.

## Development
1. Fork this repository and create a feature branch.
2. Use Python 3.13 and install dependencies:
   python -m venv .venv
   pip install -r requirements.txt
3. Copy .env.example to .env and set a test bot token from @BotFather.
4. Run the bot with python bot.py.
5. Run checks before opening a pull request:
   python -m compileall -q .
   python -m unittest discover -s tests

## Pull requests
Include what changed and why, reproducible/manual test steps, non-sensitive sample input/output when relevant, and any new configuration or deployment implications.

By submitting a contribution, you agree that your contribution may be distributed under the repository's MIT license.
