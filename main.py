
import os
import json
import random
import time
import urllib.parse
import requests

# GitHub Actions Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Keep your existing Facebook Graph API version.
FB_GRAPH_VERSION = os.getenv("FB_GRAPH_VERSION", "v21.0")

TOPICS = [
    "Latest AI breakthroughs and futuristic gadgets",
    "Car maintenance and automotive DIY tips",
    "Smart home gadgets and future technology",
    "Productivity hacks and useful technology",
    "Space exploration and astronomy discoveries",
]


def check_secrets():
    required = {
        "GEMINI_API_KEY": GEMINI_KEY,
        "FB_PAGE_ID": FB_PAGE_ID,
        "FB_ACCESS_TOKEN": FB_ACCESS_TOKEN,
        "POLLINATIONS_API_KEY": POLLINATIONS_API_KEY,
    }

    missing = [
        name for name, value in required.items()
        if not value
    ]

    if missing:
        raise Exception(
            "Missing GitHub Secrets: " + ", ".join(missing)
        )


def request_with_retry(method, url, **kwargs):
    """Retry temporary server errors and rate limits."""
    last_response = None

    for attempt in range(4):
        response = requests.request(
            method, url, timeout=90, **kwargs
        )
        last_response = response

        if response.status_code not in (
            429, 500, 502, 503, 504
        ):
            return response

        print(
            f"Temporary HTTP {response.status_code}; "
            f"attempt {attempt + 1}/4"
        )

        if attempt < 3:
            time.sleep(2 ** (attempt + 1))

    return last_response


def find_active_gemini_model():
    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models"
    )

    response = request_with_retry(
        "GET",
        url,
        headers={"x-goog-api-key": GEMINI_KEY},
    )
    response.raise_for_status()

    models = response.json().get("models", [])

    supported = [
        model.get("name", "")
        for model in models
        if "generateContent" in
        model.get("supportedGenerationMethods", [])
    ]

    # Prefer a current stable Flash model.
    preferred = [
        "models/gemini-3.8-flash",
        "models/gemini-3.6-flash",
        "models/gemini-3.5-flash-lite",
        "models/gemini-3-flash-preview",
    ]

    for name in preferred:
        if name in supported:
            print(f"Selected Gemini model: {name}")
            return name

    # Fallback: choose a Flash model actually listed by the API.
    flash_models = sorted(
        [
            name for name in supported
            if "flash" in name.lower()
            and "2.5" not in name.lower()
            and "2.0" not in name.lower()
        ],
        reverse=True,
    )

    if flash_models:
        print(f"Selected fallback model: {flash_models[0]}")
        return flash_models[0]

    raise Exception(
        "No supported Gemini Flash model found. "
        "Check the models available to your API key."
    )


def get_caption_and_prompt(topic):
    model_name = find_active_gemini_model()

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/{model_name}:generateContent"
    )

    prompt = f"""
Create a Facebook post about: {topic}

Return ONLY valid JSON in this format:
{{
  "caption": "Engaging caption with emojis and 4-5 hashtags",
  "image_prompt": "Detailed image prompt under 50 words"
}}

Requirements:
- Write the caption in natural, engaging English.
- Make it suitable for a general audience.
- Create a visually appealing image prompt.
- Do not use Markdown code fences.
"""

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.8,
        },
    }

    response = request_with_retry(
        "POST",
        url,
        headers={
            "x-goog-api-key": GEMINI_KEY,
            "Content-Type": "application/json",
        },
        json=payload,
    )
    response.raise_for_status()

    result = response.json()
    candidates = result.get("candidates", [])

    if not candidates:
        raise Exception(
            f"Gemini returned no candidates: {result}"
        )

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(
        part.get("text", "") for part in parts
    ).strip()

    if not text:
        raise Exception("Gemini returned an empty response.")

    # Handle accidental Markdown fences.
    text = text.replace("```json", "").replace("```", "").strip()
    data = json.loads(text)

    caption = data.get("caption", "").strip()
    image_prompt = data.get("image_prompt", "").strip()

    if not caption or not image_prompt:
        raise Exception(
            "Gemini response is missing caption or image_prompt."
        )

    return caption, image_prompt


def generate_image_free(prompt):
    encoded_prompt = urllib.parse.quote(prompt, safe="")

    url = (
        "https://gen.pollinations.ai/image/"
        f"{encoded_prompt}"
    )

    response = request_with_retry(
        "GET",
        url,
        headers={
            "Authorization": f"Bearer {POLLINATIONS_API_KEY}"
        },
        params={
            "model": "flux",
            "width": 1024,
            "height": 1024,
        },
    )
    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type", ""
    ).lower()

    if not content_type.startswith("image/"):
        raise Exception(
            "Pollinations did not return an image. "
            f"Content-Type: {content_type}; "
            f"Response: {response.text[:500]}"
        )

    if not response.content:
        raise Exception("Generated image is empty.")

    print("Image generated successfully.")
    return response.content, content_type


def post_to_facebook(image_bytes, content_type, caption):
    url = (
        f"https://graph.facebook.com/"
        f"{FB_GRAPH_VERSION}/{FB_PAGE_ID}/photos"
    )

    extension = (
        "png" if "png" in content_type else "jpg"
    )

    # Do not retry Facebook posting automatically:
    # a timeout could happen after Facebook has accepted the post.
    response = requests.post(
        url,
        data={
            "message": caption,
            "access_token": FB_ACCESS_TOKEN,
        },
        files={
            "source": (
                f"facebook_post.{extension}",
                image_bytes,
                content_type,
            )
        },
        timeout=120,
    )

    try:
        result = response.json()
    except ValueError:
        raise Exception(
            f"Facebook returned HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )

    if response.ok and result.get("id"):
        print(
            "Facebook post successful! "
            f"Photo ID: {result['id']}"
        )
        return

    raise Exception(f"Facebook API Error: {result}")


def main():
    check_secrets()

    selected_topic = random.choice(TOPICS)
    print(f"Today's topic: {selected_topic}")

    caption, image_prompt = get_caption_and_prompt(
        selected_topic
    )

    print("Caption generated successfully.")
    print("Generating image...")

    image_bytes, content_type = generate_image_free(
        image_prompt
    )

    print("Uploading image to Facebook Page...")

    post_to_facebook(
        image_bytes,
        content_type,
        caption,
    )


if __name__ == "__main__":
    main()
