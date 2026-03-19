import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv

SYSTEM_PROMPT = (
    "You are an expert English literature and language teacher preparing candidates for a competitive exam in Rajasthan, India. "
    "Write a concise syllabus note on the given topic. Use plain text only. Do not use markdown, hashtags, asterisks, bullets with symbols, emojis, or fluff. "
    "Keep it under 250 words. Include only: 1 short topic line, 3 crisp key points, and at least 5 MCQs with 4 options each plus the correct answer. "
    "Make the MCQs higher-level, syllabus-specific, and exam-focused. Avoid easy or generic questions. "
    "The content must be direct, syllabus-related, and exam-focused."
)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "google/gemma-3-27b-it:free"
TELEGRAM_API_BASE = "https://api.telegram.org"
OPENROUTER_HEADERS = {
    "Content-Type": "application/json",
    "HTTP-Referer": "https://litgram.app",
    "X-Title": "LitGram Telegram Bot",
}


def load_env_vars():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    channel = os.getenv("TELEGRAM_CHANNEL_ID")

    if not token or not openrouter_key or not channel:
        raise ValueError("Missing environment variable(s): TELEGRAM_BOT_TOKEN, OPENROUTER_API_KEY, TELEGRAM_CHANNEL_ID are required.")

    return token, openrouter_key, channel


def load_topics(syllabus_path="syllabus.json"):
    if not os.path.exists(syllabus_path):
        raise FileNotFoundError(f"{syllabus_path} not found.")

    with open(syllabus_path, "r", encoding="utf-8") as f:
        syllabus = json.load(f)

    parts = syllabus.get("parts", {})
    if not isinstance(parts, dict) or not parts:
        raise ValueError("syllabus.json must contain a non-empty 'parts' object.")

    topics = []
    for part, items in parts.items():
        if not isinstance(items, list):
            raise ValueError(f"Part '{part}' must be a list of topic strings.")
        topics.extend([str(t).strip() for t in items if str(t).strip()])

    if not topics:
        raise ValueError("No topics loaded from syllabus.json.")

    return topics


def read_index(index_path="topic_index.txt"):
    if not os.path.exists(index_path):
        return 0

    with open(index_path, "r", encoding="utf-8") as f:
        raw = f.read().strip()

    try:
        return int(raw)
    except (ValueError, TypeError):
        return 0


def write_index(index, index_path="topic_index.txt"):
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(str(index))


def sanitize_post_text(text):
    cleaned_lines = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            cleaned_lines.append("")
            continue

        if line.startswith("```"):
            continue

        while line.startswith("#"):
            line = line[1:].lstrip()

        if line.startswith(("- ", "* ")):
            line = line[2:].lstrip()

        line = line.replace("**", "").replace("__", "").replace("`", "")
        line = line.replace("*", "")

        if line:
            cleaned_lines.append(line)

    cleaned_text = "\n".join(cleaned_lines)
    while "\n\n\n" in cleaned_text:
        cleaned_text = cleaned_text.replace("\n\n\n", "\n\n")

    return cleaned_text.strip()


def generate_post(openrouter_key, topic):
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Topic: {topic}\n\n"
        "Return only the final post text. Make sure there are at least 5 MCQs."
    )

    print(f"Generating post content for topic: {topic}")

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 400,
    }
    headers = dict(OPENROUTER_HEADERS)
    headers["Authorization"] = f"Bearer {openrouter_key}"

    response = requests.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        json=payload,
        headers=headers,
        timeout=60,
    )
    if response.status_code != 200:
        raise RuntimeError(f"OpenRouter API error: {response.status_code} - {response.text}")

    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"OpenRouter returned no choices: {data}")

    text = choices[0].get("message", {}).get("content")
    if not text:
        raise RuntimeError(f"OpenRouter response missing content: {data}")

    print("Generation successful.")
    return sanitize_post_text(text)


def post_to_telegram(bot_token, channel_id, text):
    endpoint = f"{TELEGRAM_API_BASE}/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": text,
    }

    print(f"Sending post to Telegram channel: {channel_id}")
    resp = requests.post(endpoint, json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Telegram API error: {resp.status_code} - {resp.text}")

    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API false response: {data}")

    print("Post sent successfully.")
    return data


def run_once():
    token, openrouter_key, channel_id = load_env_vars()
    topics = load_topics()
    idx = read_index()

    if not topics:
        raise ValueError("No topics available to process")

    selected_topic = topics[idx % len(topics)]
    print(f"Selected topic index {idx} -> '{selected_topic}'")

    post_text = generate_post(openrouter_key, selected_topic)
    post_to_telegram(token, channel_id, post_text)

    next_idx = idx + 1
    write_index(next_idx)
    print(f"Next index saved: {next_idx}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Telegram exam-prep channel bot")
    parser.add_argument("--once", action="store_true", help="Run one post cycle and exit")
    args = parser.parse_args()

    try:
        if args.once:
            run_once()
        else:
            # default behavior: run once in this script; schedule is via CI
            run_once()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
