import os
import random
import urllib.parse
from io import BytesIO
import requests
from PIL import Image

# Secrets
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

TOPICS = [
    "Latest AI breakthroughs and humanoid robotics revolution",
    "Car engine maintenance, DIY automotive care and tuning hacks",
    "Smart home gadgets and futuristic tech lifestyle",
    "Productivity automation tools for modern developers",
    "Deep space exploration, astronomy and new galaxy discoveries"
]

def get_caption_and_image_prompt(topic: str):
    """Text generation with fallback so workflow never fails."""
    prompt = (
        f"Create an engaging Facebook post with emojis and 3-4 hashtags about: '{topic}'. "
        f"At the end, strictly write 'IMAGE_PROMPT:' followed by a 20-word realistic image description."
    )
    url = f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}"
    try:
        r = requests.get(url, timeout=30)
        text = r.text.strip()
    except Exception:
        text = f"Exploring {topic}! The future is evolving rapidly. #Tech #Innovation #DailyUpdate\n\nIMAGE_PROMPT: Cinematic ultra detailed photograph of {topic}"

    if "IMAGE_PROMPT:" in text:
        parts = text.split("IMAGE_PROMPT:")
        caption = parts[0].replace("CAPTION:", "").strip()
        img_prompt = parts[1].strip()
    else:
        caption = text
        img_prompt = f"Cinematic detailed realistic photograph of {topic}"

    return caption, img_prompt

def download_and_crop_clean_image(img_prompt: str) -> BytesIO:
    """HD Image download karke watermark bottom se 100% crop kar deta hai."""
    clean_prompt = img_prompt.replace("\n", " ")[:150]
    seed = random.randint(1, 999999)
    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(clean_prompt)}?width=1024&height=1024&seed={seed}"
    
    print("Downloading generated image...")
    res = requests.get(img_url, timeout=60)
    img = Image.open(BytesIO(res.content)).convert("RGB")

    # Watermark wala bottom hissa crop (45 pixels)
    width, height = img.size
    cropped = img.crop((0, 0, width, height - 45))

    output = BytesIO()
    cropped.save(output, format="JPEG", quality=95)
    output.seek(0)
    return output

def post_to_facebook(image_bytes: BytesIO, caption: str):
    """Facebook Page par clean photo upload karta hai."""
    url = f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/photos"
    files = {
        'source': ('photo.jpg', image_bytes, 'image/jpeg')
    }
    data = {
        'message': caption,
        'access_token': FB_ACCESS_TOKEN
    }
    r = requests.post(url, data=data, files=files, timeout=60)
    res = r.json()
    if "id" in res:
        print(f"Posted successfully to Facebook! Post ID: {res['id']}")
    else:
        raise Exception(f"Facebook API Error: {res}")

def main():
    if not FB_PAGE_ID or not FB_ACCESS_TOKEN:
        raise Exception("Missing FB_PAGE_ID or FB_ACCESS_TOKEN in secrets!")

    topic = random.choice(TOPICS)
    print(f"Selected Topic: {topic}")

    caption, img_prompt = get_caption_and_image_prompt(topic)
    print(f"Caption generated. Processing clean image...")
    
    clean_image = download_and_crop_clean_image(img_prompt)

    print("Uploading to Facebook Page...")
    post_to_facebook(clean_image, caption)

if __name__ == "__main__":
    main()
