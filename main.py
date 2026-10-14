import os
import json
import random
import urllib.parse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import google.generativeai as genai
from PIL import Image

# 1. Credentials / Secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PAGE_ID = os.getenv("PAGE_ID")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
HISTORY_FILE = "posted_history.json"

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def get_retry_session():
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

def load_posted_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_posted_history(history):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"History save notice: {e}")

def pick_reference_image(folder_path="references"):
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder '{folder_path}' nahi mila!")

    valid_exts = ('.jpg', '.jpeg', '.png', '.webp')
    all_photos = [f for f in os.listdir(folder_path) if f.lower().endswith(valid_exts)]

    if not all_photos:
        raise ValueError(f"Folder '{folder_path}' mein koi photo nahi mili!")

    history = load_posted_history()
    available_photos = [p for p in all_photos if p not in history]

    if not available_photos:
        print("Saari photos post ho chuki hain. Cycle reset...")
        history = []
        available_photos = all_photos

    chosen_file = random.choice(available_photos)
    history.append(chosen_file)
    save_posted_history(history)

    full_path = os.path.join(folder_path, chosen_file)
    print(f"Selected reference photo: {chosen_file}")
    return full_path

def describe_reference_and_make_prompt(ref_image_path, topic):
    """Gemini se HD visual realism prompt banata hai"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        img = Image.open(ref_image_path)
        
        prompt = (
            f"Look at this person in the reference image. Describe their facial identity, hairstyle, and skin tone. "
            f"Now write an ultra-realistic 4K photography prompt featuring this exact same person in a new scene about: '{topic}'. "
            "Keep natural lighting, sharp focus, DSLR quality, highly detailed skin texture, realistic morning lifestyle. "
            "Keep the prompt strictly under 40 words, comma-separated."
        )
        response = model.generate_content([prompt, img])
        img_prompt = response.text.strip().replace("\n", " ")
        print(f"Generated HD Prompt: {img_prompt}")
        return img_prompt
    except Exception as e:
        print(f"Prompt fallback: {e}")
        return f"Hyper-realistic portrait photography, crisp focus, soft natural daylight, 8k resolution, cinematic lighting, themed on {topic}"

def generate_ai_image(image_prompt, output_path="generated_post.jpg"):
    """High-Resolution Flux Engine se 1080x1080 sharp image generate karta hai"""
    print("Generating High-Resolution photo...")
    
    encoded_prompt = urllib.parse.quote(image_prompt)
    seed = random.randint(10000, 999999)
    # High-Definition Flux pipeline with no watermarks
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&model=flux&seed={seed}&nologo=true&enhance=true"

    session = get_retry_session()
    response = session.get(image_url, timeout=90)

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"HD Image generated successfully and saved to {output_path}")
        return output_path
    else:
        raise Exception(f"Image generation failed with HTTP {response.status_code}")

def generate_caption(topic):
    """Romanized Hindi (Hinglish) caption generate karta hai"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            f"Write an engaging, positive Facebook post caption about: '{topic}'. "
            "STRICT RULES: Write entirely in Hindi using English letters/script (Hinglish). "
            "Do NOT use Devanagari script. Do NOT write in pure English. "
            "Use natural, conversational everyday Hindi. "
            "Keep it under 3-4 sentences. Add matching emojis and 3-4 relevant hashtags at the end."
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Caption generate notice: {e}")
        return "Har nayi subah ek nayi umeed aur nayi taazgi lekar aati hai! Apne sapno ke peeche lagatar mehnat karte raho. ✨ #NayiSubah #PositiveVibes #DailyMotivation #SelfGrowth"

def post_to_facebook(image_path, caption):
    print("Uploading HD image to Facebook Page...")

    if not PAGE_ID or not PAGE_ACCESS_TOKEN:
        raise ValueError("PAGE_ID ya PAGE_ACCESS_TOKEN environment variables set nahi hain.")

    url = f"https://graph.facebook.com/v20.0/{PAGE_ID}/photos"
    payload = {
        "message": caption,
        "access_token": PAGE_ACCESS_TOKEN
    }

    session = get_retry_session()
    with open(image_path, "rb") as img_file:
        files = {"source": img_file}
        response = session.post(url, data=payload, files=files, timeout=60)

    res = response.json()
    if response.status_code != 200 or "error" in res:
        raise Exception(f"Facebook API Error: {res}")

    print(f"Success! Post published. Photo ID: {res.get('id')}")
    return res

def main():
    ref_photo = pick_reference_image("references")

    themes = [
        "Subah ki shuruat, positivity aur naye iraade",
        "Zindagi ki khoobsurti aur self-growth",
        "Aesthetic lifestyle, shanti aur confidence",
        "Koshish aur sapno ko poora karne ki umeed",
        "Muskurahat aur har din ko behtar banane ki soch"
    ]
    topic = random.choice(themes)
    print(f"Today's Topic: {topic}")

    hd_prompt = describe_reference_and_make_prompt(ref_photo, topic)
    img_path = generate_ai_image(hd_prompt, "generated_post.jpg")
    caption = generate_caption(topic)
    print(f"Caption ready:\n{caption}\n")

    try:
        post_to_facebook(img_path, caption)
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)

if __name__ == "__main__":
    main()
