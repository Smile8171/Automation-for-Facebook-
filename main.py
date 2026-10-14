import os
import json
import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import google.generativeai as genai

# 1. Credentials
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PAGE_ID = os.getenv("PAGE_ID")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
HISTORY_FILE = "posted_history.json"

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def get_retry_session():
    """Network drop ya server error ke liye auto-retry session banata hai"""
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
    """Pichli post hui photos ki list load karta hai"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_posted_history(history):
    """Post hone ke baad file name save karta hai"""
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"History save notice: {e}")

def pick_reference_image(folder_path="references"):
    """Bina repeat kiye nayi photo select karta hai"""
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder '{folder_path}' nahi mila!")

    valid_exts = ('.jpg', '.jpeg', '.png', '.webp')
    all_photos = [
        f for f in os.listdir(folder_path)
        if f.lower().endswith(valid_exts)
    ]

    if not all_photos:
        raise ValueError(f"Folder '{folder_path}' mein koi photo nahi mili!")

    history = load_posted_history()

    # Jo photos abhi tak post nahi hui hain
    available_photos = [p for p in all_photos if p not in history]

    # Agar saari photos post ho chuki hain, toh cycle reset kar do
    if not available_photos:
        print("Saari photos ek baar post ho chuki hain. Cycle reset kiya ja raha hai...")
        history = []
        available_photos = all_photos

    chosen_file = random.choice(available_photos)
    history.append(chosen_file)
    save_posted_history(history)

    full_path = os.path.join(folder_path, chosen_file)
    print(f"Selected reference photo: {chosen_file} (Bachi hui: {len(available_photos) - 1})")
    return full_path

def generate_caption(topic):
    """Romanized Hindi (Hinglish) mein clean caption banata hai"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
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
    """Facebook Page ke /{PAGE_ID}/photos endpoint par image upload karta hai"""
    print("Uploading to Facebook Page...")

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
    # 1. Non-repeating photo pick karo
    image_to_post = pick_reference_image("references")

    # 2. Daily Hinglish theme
    themes = [
        "Subah ki shuruat, positivity aur naye iraade",
        "Zindagi ki khoobsurti aur self-growth",
        "Aesthetic lifestyle, shanti aur confidence",
        "Koshish aur sapno ko poora karne ki umeed",
        "Muskurahat aur har din ko behtar banane ki soch"
    ]
    topic = random.choice(themes)
    print(f"Today's Topic: {topic}")

    # 3. Caption taiyar karo
    caption = generate_caption(topic)
    print(f"Caption:\n{caption}\n")

    # 4. Facebook par upload karo
    post_to_facebook(image_to_post, caption)

if __name__ == "__main__":
    main()
