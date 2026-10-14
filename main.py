import os
import random
from io import BytesIO
import requests
from google import genai
from google.genai import types

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

# Official Google GenAI client
client = genai.Client(api_key=GEMINI_KEY)

TOPICS = [
    "Latest AI breakthroughs and humanoid robotics",
    "Car engine maintenance, DIY automotive care and tuning",
    "Smart home gadgets and future tech lifestyle",
    "Productivity automation tools for developers",
    "Space exploration, astronomy and new galaxy discoveries"
]

def generate_caption_and_prompt(topic: str):
    """Gemini se Facebook caption aur image prompt generate karwata hai."""
    prompt = (
        f"Write an engaging Facebook post with emojis and 3-4 hashtags about: '{topic}'. "
        f"At the very end, strictly add 'IMAGE_PROMPT:' followed by a detailed visual prompt "
        f"describing a realistic, cinematic scene (without any text or letters inside the image)."
    )

    response = client.models.generate_content(
                model="gemini-2.0-flash",
        ",
        contents=prompt
    )
    text = response.text.strip()

    if "IMAGE_PROMPT:" in text:
        parts = text.split("IMAGE_PROMPT:")
        caption = parts[0].strip()
        img_prompt = parts[1].strip()
    else:
        caption = text
        img_prompt = f"Cinematic, ultra-detailed 8k photograph representing {topic}"

    return caption, img_prompt

def generate_imagen_image(img_prompt: str) -> BytesIO:
    """Google Imagen model se clean, watermark-free image banata hai."""
    print(f"Generating image via Gemini Imagen: {img_prompt[:70]}...")
    result = client.models.generate_images(
        model="imagen-3.0-generate-002",
        prompt=img_prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="1:1",
            output_mime_type="image/jpeg"
        )
    )

    generated_image = result.generated_images[0]
    return BytesIO(generated_image.image.image_bytes)

def post_to_facebook(image_bytes: BytesIO, caption: str):
    """Facebook Page par post publish karta hai."""
    url = f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/photos"
    files = {
        'source': ('image.jpg', image_bytes, 'image/jpeg')
    }
    data = {
        'message': caption,
        'access_token': FB_ACCESS_TOKEN
    }
    r = requests.post(url, data=data, files=files, timeout=60)
    res = r.json()
    if "id" in res:
        print(f"Posted successfully to Facebook! ID: {res['id']}")
    else:
        raise Exception(f"Facebook API Error: {res}")

def main():
    if not GEMINI_KEY:
        raise Exception("Missing GEMINI_API_KEY in GitHub Secrets.")
    if not FB_PAGE_ID or not FB_ACCESS_TOKEN:
        raise Exception("Missing FB_PAGE_ID or FB_ACCESS_TOKEN in GitHub Secrets.")

    topic = random.choice(TOPICS)
    print(f"Selected Topic: {topic}")

    caption, img_prompt = generate_caption_and_prompt(topic)
    image_bytes = generate_imagen_image(img_prompt)

    print("Uploading to Facebook...")
    post_to_facebook(image_bytes, caption)

if __name__ == "__main__":
    main()
