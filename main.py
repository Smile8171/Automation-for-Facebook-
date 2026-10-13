
import os
import random
import json
import requests
import urllib.parse


GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

TOPICS = [
    "Latest AI breakthroughs and futuristic gadgets",
    "Car maintenance, engine health and automotive DIY hacks",
    "Smart home gadgets and future tech lifestyle",
    "Productivity hacks and automated coding tools",
    "Space exploration and astronomy discoveries",
]


def check_secrets():
    missing = []

    if not GEMINI_KEY:
        missing.append("GEMINI_API_KEY")
    if not FB_PAGE_ID:
        missing.append("FB_PAGE_ID")
    if not FB_ACCESS_TOKEN:
        missing.append("FB_ACCESS_TOKEN")

    if missing:
        raise Exception(
            "Missing GitHub Secrets: " + ", ".join(missing)
        )


def find_active_gemini_model():
    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models"
    )

    response = requests.get(
        url,
        headers={"x-goog-api-key": GEMINI_KEY},
        timeout=30,
    )
    response.raise_for_status()

    models = response.json().get("models", [])

    supported = [
        model.get("name", "")
        for model in models
        if "generateContent" in
        model.get("supportedGenerationMethods", [])
    ]

    # Try newer Flash models first.
    preferred = [
        "models/gemini-3.8-flash",
        "models/gemini-3.5-flash",
        "models/gemini-3-flash",
    ]

    for name in preferred:
        if name in supported:
            return name

    # Do not select the retired/unavailable 2.5 Flash
    # model that caused the previous workflow error.
    flash_models = [
        name for name in supported
        if "flash" in name.lower()
        and "gemini-2.5-flash" not in name.lower()
        and "gemini-2.5-flash-lite" not in name.lower()
    ]

    if flash_models:
        # Prefer higher version numbers when available.
        flash_models.sort(reverse=True)
        return flash_models[0]

    raise Exception(
        "No suitable Gemini Flash model found. "
        "Check the models available to your API key."
    )


def get_caption_and_prompt(topic: str):
    model_name = find_active_gemini_model()

    print(f"Using dynamically detected model: {model_name}")

    prompt_text = f"""
Create a high-engagement Facebook post about: {topic}

Return ONLY valid JSON with these two fields:
{{
  "caption": "An engaging Facebook caption with emojis and 4-5 hashtags",
  "image_prompt": "A detailed, vivid image prompt under 50 words"
}}

Requirements:
- Use natural, engaging language.
- Make the caption suitable for a general audience.
- Do not include Markdown code fences.
- The image prompt must describe a visually appealing image.
"""

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/{model_name}:generateContent"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        },
    }

    response = requests.post(
        url,
        headers={
            "x-goog-api-key": GEMINI_KEY,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
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


def generate_image_free(prompt: str) -> str:
    encoded_prompt = urllib.parse.quote(prompt, safe="")

    # Prefer the current Pollinations API when a key is configured.
    if POLLINATIONS_API_KEY:
        image_url = (
            "https://gen.pollinations.ai/image/"
            f"{encoded_prompt}?model=flux"
        )

        response = requests.get(
            image_url,
            headers={
                "Authorization": f"Bearer {POLLINATIONS_API_KEY}"
            },
            timeout=180,
        )
        response.raise_for_status()

        # Upload the generated image bytes directly to Facebook.
        image_bytes = response.content

        if not image_bytes:
            raise Exception("Image API returned an empty image.")

        return image_bytes

    # Legacy endpoint fallback.
    image_url = (
        "https://image.pollinations.ai/prompt/"
        f"{encoded_prompt}?width=1024&height=1024&nologo=true"
    )

    response = requests.get(
        image_url,
        timeout=180,
        allow_redirects=True,
    )
    response.raise_for_status()

    if not response.content:
        raise Exception("Image API returned an empty image.")

    return response.content


def post_to_facebook(image_data, caption: str):
    url = (
        f"https://graph.facebook.com/v21.0/"
        f"{FB_PAGE_ID}/photos"
    )

    data = {
        "message": caption,
        "access_token": FB_ACCESS_TOKEN,
    }

    files = {
        "source": ("facebook_post.jpg", image_data, "image/jpeg")
    }

    response = requests.post(
        url,
        data=data,
        files=files,
        timeout=120,
    )

    result = response.json()

    if response.ok and "id" in result:
        print(f"Posted successfully! ID: {result['id']}")
    else:
        raise Exception(f"Facebook API Error: {result}")


if __name__ == "__main__":
    check_secrets()

    selected_topic = random.choice(TOPICS)
    print(f"Today's Topic: {selected_topic}")

    caption, image_prompt = get_caption_and_prompt(
        selected_topic
    )

    print("Caption generated successfully.")
    print("Generating image...")

    image_data = generate_image_free(image_prompt)

    print("Image generated. Posting to Facebook...")
    post_to_facebook(image_data, caption)
