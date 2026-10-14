import os
import requests
import google.generativeai as genai

# 1. API Keys aur Environment Variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PAGE_ID = os.getenv("PAGE_ID")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

# Setup Gemini AI
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_caption(topic):
    """Gemini AI se Facebook post ke liye caption generate karta hai"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            f"Write an engaging, insightful Facebook post caption about: '{topic}'. "
            "Keep it under 100 words, informative, with relevant hashtags and emojis."
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Caption generate karne mein issue: {e}")
        return f"Exploring {topic}! What are your thoughts on this? #Tech #AI #Innovation"

def download_image(image_url, save_path="temp_post_image.jpg"):
    """Image ko URL se local file mein download karta hai"""
    print("Downloading generated image...")
    res = requests.get(image_url, timeout=30)
    if res.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(res.content)
        return save_path
    else:
        raise Exception(f"Image download fail ho gayi: HTTP {res.status_code}")

def post_to_facebook(image_path, caption):
    """Facebook Page ke Graph API photos endpoint par image aur caption post karta hai"""
    print("Uploading to Facebook Page...")
    
    if not PAGE_ID or not PAGE_ACCESS_TOKEN:
        raise ValueError("PAGE_ID ya PAGE_ACCESS_TOKEN environment variable set nahi hain.")

    # Sahi Endpoint: {PAGE_ID}/photos ('me/photos' use nahi karna)
    url = f"https://graph.facebook.com/v20.0/{PAGE_ID}/photos"

    payload = {
        "message": caption,
        "access_token": PAGE_ACCESS_TOKEN
    }

    with open(image_path, "rb") as img_file:
        files = {
            "source": img_file
        }
        response = requests.post(url, data=payload, files=files, timeout=60)

    res = response.json()

    if response.status_code != 200 or "error" in res:
        raise Exception(f"Facebook API Error: {res}")

    print(f"Success! Post published. Photo ID: {res.get('id')}")
    return res

def main():
    # Aapka selected topic
    topic = "Latest AI breakthroughs and humanoid robotics revolution"
    print(f"Selected Topic: {topic}")

    # Step 1: Caption generate karein
    caption = generate_caption(topic)
    print("Caption generated. Processing clean image...")

    # Step 2: Image provide/download karein (ya jahan se aapki image aati hai)
    # Note: Agar image pehle se local path par hai toh direct wahi path pass karein
    sample_image_url = "https://picsum.photos/1200/630"
    image_path = download_image(sample_image_url, "clean_image.jpg")

    # Step 3: Facebook Page par upload karein
    try:
        post_to_facebook(image_path, caption)
    finally:
        # Temp file clean up
        if os.path.exists(image_path):
            os.remove(image_path)

if __name__ == "__main__":
    main()
