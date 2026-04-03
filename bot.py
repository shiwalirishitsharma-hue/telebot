import argparse
import html
import json
import os
import sys
from typing import Any

import requests
from dotenv import load_dotenv

SYSTEM_PROMPT = (
    "You are an expert RPSC First Grade English faculty member who specializes in teaching rural, Hindi-medium students from Rajasthan. "
    "Write a high-impact Telegram post in Hinglish for the exact syllabus topic provided. "
    "Use Devanagari script for explanation and emotional support, and English only for technical terms, rules, literary titles, and names. "
    "Keep the tone warm, encouraging, and coaching-like. "
    "Use Telegram-safe HTML formatting only: use <b> for bold, keep bullets as \u2022, and do not use markdown fences or code blocks. "
    "Stay strictly within the given syllabus topic and do not drift to unrelated content. "
    "Make the post concise, readable, and exam-oriented."
)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_CANDIDATES = [
    "mistralai/mistral-small-2603",
    "openai/gpt-oss-120b:free",
    "google/gemma-3-4b-it:free",
]
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
        for topic in items:
            topic_text = str(topic).strip()
            if topic_text:
                topics.append({"part": str(part).strip(), "topic": topic_text})

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
            line = f"\u2022 {line[2:].lstrip()}"

        line = line.replace("**", "").replace("__", "").replace("`", "")
        line = line.replace("*", "")

        if line:
            cleaned_lines.append(line)

    cleaned_text = "\n".join(cleaned_lines)
    while "\n\n\n" in cleaned_text:
        cleaned_text = cleaned_text.replace("\n\n\n", "\n\n")

    escaped_text = html.escape(cleaned_text.strip())
    escaped_text = escaped_text.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
    return escaped_text

def generate_post_with_model(openrouter_key, topic, model):
    prompt = build_generation_prompt(topic)

    print(f"Generating post content for topic: {topic['topic']}")

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 750,
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

def build_generation_prompt(topic: Any):
    part = topic["part"]
    topic_name = topic["topic"]
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Syllabus exam: RPSC Senior Teacher / Lecturer Grade English\n"
        f"Syllabus part: {part}\n"
        f"Syllabus topic: {topic_name}\n\n"
        "Follow this exact structure:\n"
        "1. <b>Catchy Headline</b> in Hindi with benefit-driven tone.\n"
        "2. <b>The Concept</b> explained in 3 to 5 bullet points.\n"
        "3. <b>Exam Insight</b> mentioning how many questions were asked from this topic in the 2022 or 2024 RPSC exams.\n"
        "4. <b>The Daily Battle</b>: one high-probability MCQ with 4 options and the correct answer.\n"
        "5. <b>Motivation Anchor</b>: one short, emotional Hindi closing line.\n\n"
        "Important rules:\n"
        "- Use Hinglish naturally, with Devanagari script for explanation and English for technical terms.\n"
        "- Keep the post short, sharp, and highly shareable for Telegram.\n"
        "- Use bullets and bold text for readability.\n"
        "- If you are unsure about the exact 2022/2024 question count, do not invent a number; instead phrase the exam insight carefully and honestly.\n"
        "- Return only the final post content."
    )

def generate_post(openrouter_key, topic):
    last_error = None

    for model in MODEL_CANDIDATES:
        print(f"Trying model: {model}")
        try:
            return generate_post_with_model(openrouter_key, topic, model)
        except RuntimeError as exc:
            message = str(exc)
            last_error = exc
            if " 429 -" in message or '"code":429' in message:
                print(f"Model rate-limited: {model}")
                continue
            raise

    raise RuntimeError(f"All OpenRouter model attempts were rate-limited: {last_error}")

def post_to_telegram(bot_token, channel_id, text):
    endpoint = f"{TELEGRAM_API_BASE}/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
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
    print(f"Selected topic index {idx} -> '{selected_topic['part']} | {selected_topic['topic']}'")

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
