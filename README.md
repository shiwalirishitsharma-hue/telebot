# Telegram Exam Prep Channel Bot

A lightweight scheduled Telegram channel bot that uses OpenRouter + OpenAI-compatible API to generate short exam-prep posts from a syllabus and publish them automatically.

## Project Structure

- `.env` - secrets (not committed)
- `.env.example` - example env template
- `.gitignore`
- `requirements.txt`
- `syllabus.json` - exam topics structure
- `topic_index.txt` - current topic pointer state
- `bot.py` - main executable
- `.github/workflows/post.yml` - cron workflow

## Setup

1. Create a Telegram bot with [@BotFather](https://t.me/BotFather)
   - `/newbot`, choose name and username
   - copy `BOT_TOKEN`
2. Add bot as admin to your channel
   - Open channel settings > Administrators > Add bot
   - Give permission to post messages
3. Get channel ID
   - Use @username or numeric ID (e.g. `@yourchannel` recommended)
4. Get OpenRouter API key
   - Sign in at https://openrouter.ai
   - Create API key, copy it
5. Set GitHub repository secrets
   - `TELEGRAM_BOT_TOKEN`
   - `OPENROUTER_API_KEY`
   - `TELEGRAM_CHANNEL_ID`
6. Provide syllabus in `syllabus.json`
   - Format:
```json
{
  "exam": "Exam Name Here",
  "parts": {
    "Part Name": ["topic 1", "topic 2"],
    "Another Part": ["topic 1", "topic 2"]
  }
}
```
7. Confirm `topic_index.txt` exists and is tracked (default `0`).

## Run locally for test

- Create `.env` from `.env.example` with real values.
- `python -m pip install -r requirements.txt`
- `python bot.py --once`

## GitHub Actions

The workflow in `.github/workflows/post.yml` runs at:
- `02:30 UTC` (08:00 IST)
- `07:30 UTC` (13:00 IST)
- `13:30 UTC` (19:00 IST)
- manual `workflow_dispatch`

It runs `python bot.py --once` and commits `topic_index.txt` if changed.

## Behavior

- Loads env from `.env`.
- Loads and flattens all topics from `syllabus.json`.
- Picks topic at current index (mod length).
- Generates message via OpenRouter ChatCompletion.
- Sends Markdown message to Telegram channel.
- Increments and writes next index to `topic_index.txt`.

## Notes

- `topic_index.txt` must be committed (not ignored).
- `.env` must remain private and excluded from repository.
