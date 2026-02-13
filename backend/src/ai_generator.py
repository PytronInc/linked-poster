"""Provider-agnostic AI content generation (OpenAI or Anthropic)."""

from __future__ import annotations

import logging

import httpx

import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert LinkedIn content writer. You create engaging, professional posts that drive engagement and grow personal brand visibility.

Guidelines:
- Keep posts concise (under 3000 characters)
- Use line breaks for readability
- Include a hook in the first line to stop the scroll
- End with a call-to-action or thought-provoking question
- Use relevant hashtags (3-5 max) at the end
- Do NOT use markdown formatting (no bold, italic, headers) — LinkedIn doesn't render it
- Use emojis sparingly and only when appropriate for the tone"""


def _tone_instruction(tone: str) -> str:
    return {
        "professional": "Use a professional, authoritative tone. Back claims with data or experience.",
        "casual": "Use a conversational, approachable tone. Write like you're talking to a friend.",
        "thought-leadership": "Use a visionary, forward-thinking tone. Share unique insights and challenge conventional thinking.",
        "storytelling": "Use a narrative, story-driven tone. Start with a personal anecdote or scenario.",
    }.get(tone, "Use a professional tone.")


def _type_instruction(post_type: str) -> str:
    return {
        "text": "Write a standard text post.",
        "insight": "Share a specific insight or lesson learned. Start with the key takeaway.",
        "article_share": "Write a post that introduces and comments on an article or trend. Frame why it matters.",
        "poll_intro": "Write an engaging intro for a LinkedIn poll. Pose the question clearly and explain why it matters.",
    }.get(post_type, "Write a standard text post.")


def _build_prompt(topic: str, tone: str, post_type: str, additional_context: str | None) -> str:
    parts = [
        f"Topic: {topic}",
        f"Tone: {_tone_instruction(tone)}",
        f"Type: {_type_instruction(post_type)}",
    ]
    if additional_context:
        parts.append(f"Additional context: {additional_context}")
    parts.append("Generate 3 different LinkedIn post variants. Separate each variant with '---'.")
    return "\n\n".join(parts)


def _build_improve_prompt(content: str, instructions: str | None) -> str:
    parts = [
        "Improve the following LinkedIn post. Make it more engaging, clearer, and better structured.",
        f"Original post:\n{content}",
    ]
    if instructions:
        parts.append(f"Specific instructions: {instructions}")
    parts.append("Return the improved version only. Do not include explanations.")
    return "\n\n".join(parts)


async def _generate_openai(prompt: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.8,
                "max_tokens": 4000,
            },
            headers={
                "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _generate_anthropic(prompt: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            json={
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 4000,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            },
            headers={
                "x-api-key": config.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]


async def _generate(prompt: str) -> str:
    provider = config.AI_PROVIDER.lower()
    if provider == "anthropic":
        return await _generate_anthropic(prompt)
    return await _generate_openai(prompt)


async def generate_posts(topic: str, tone: str, post_type: str, additional_context: str | None = None) -> list[str]:
    """Generate 3 post variants for a given topic."""
    prompt = _build_prompt(topic, tone, post_type, additional_context)
    raw = await _generate(prompt)

    # Split on '---' separator
    variants = [v.strip() for v in raw.split("---") if v.strip()]
    # If splitting didn't work well, return the whole thing as one variant
    if len(variants) < 2:
        variants = [raw.strip()]
    return variants[:3]


async def improve_post(content: str, instructions: str | None = None) -> str:
    """Improve an existing post draft."""
    prompt = _build_improve_prompt(content, instructions)
    return (await _generate(prompt)).strip()
