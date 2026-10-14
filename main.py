import os
import json
import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import google.generativeai as genai
from PIL import Image

# 1. Credentials / Secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PAGE_ID = os.getenv("PAGE_ID")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
HISTORY_FILE = "posted_history.json"

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def get_retry_session():
    """Network connection fail ya drop hone par automatic 3 baar retry karega"""
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
    """Purani post ho chuki photos ki list nikalta hai"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_posted_history(history):
    """Nayi post hui photo ka naam file mein save karta hai"""
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"History save notice: {e}")

def pick_reference_image(folder_path="references"):
    """Bina repeat kiye references folder se ek photo select karta hai"""
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder '{folder_path}' nahi mila!")

    valid_exts = ('.jpg', '.jpeg', '.png', '.webp')
    all_photos = [f for f in os.listdir(folder_path) if f.lower().endswith(valid_exts)]

    if not all_photos:
        raise ValueError(f"Folder '{folder_path}' mein koi photo nahi mili!")

    history = load_posted_history()
    available_photos = [p for p in all_photos if p not in history]

    # Agar saari photos post ho chuki hon, toh history reset kar do
    if not available_photos:
        print("Saari photos ka ek round complete. Cycle reset...")
        history = []
        available_photos = all_photos

    chosen_file = random.choice(available_photos)
    history.append(chosen_file)
    save_posted_history(history)

    full_path = os.path.join(folder_path, chosen_file)
    print(f"Selected reference photo: {chosen_file}")
    return full_path

def describe_reference_and_make_prompt(ref_image_path, topic):
    """Reference photo ke visual features maintain rakhte hue HD prompt banata hai"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        img = Image.open(ref_image_path)
        
        prompt = (
            f"Analyze the facial appearance, hairstyle, skin tone, and overall aesthetic of the person in this image. "
            f"Write a high-end photography prompt for a new scene themed around: '{topic}'. "
            "Strict Instructions: Maintain the exact same facial identity, age, and features as the reference image. "
            "Only change the posture, background, clothes, and lighting. "
            "Style: DSLR 85mm portrait, f/1.8 aperture, natural sunlight, highly detailed skin texture, 4k ultra-realistic photo. "
            "Keep the prompt under 60 words, descriptive for FLUX.1. Output ONLY the raw prompt."
        )
        response = model.generate_content([prompt, img])
        img_prompt = response.text.strip().replace("\n", " ")
        print(f"Generated HD Prompt: {img_prompt}")
        return img_prompt
    except Exception as e:
        print(f"Prompt fallback: {e}")
        return f"Hyper-realistic portrait photography, crisp focus, soft natural daylight, 8k resolution, cinematic lighting, themed on {topic}"

def generate_ai_image(image_prompt, output_path="generated_post.jpg"):
    """Hugging Face FLUX.1-schnell model se image generate aur download karta hai"""
    print("Generating High-Quality image with FLUX.1...")
    
    api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": image_prompt}

    session = get_retry_session()
    response = session.post(api_url, headers=headers, json=payload, timeout=120)

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"HD Image generated and saved to {output_path}")
        return output_path
    else:
        raise Exception(f"FLUX generation failed with HTTP {response.status_code}: {response.text}")

def generate_caption(topic):
    """Romanized Hindi (Hinglish) mein Facebook caption banata hai"""
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
    # 1. Reference photo select karo
    ref_photo = pick_reference_image("references")

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

    # 3. Gemini se visual prompt banwao
    hd_prompt = describe_reference_and_make_prompt(ref_photo, topic)

    # 4. FLUX.1 se HD photo generate karo
    img_path = generate_ai_image(hd_prompt, "generated_post.jpg")

    # 5. Hinglish caption generate karo
    caption = generate_caption(topic)
    print(f"Caption ready:\n{caption}\n")

    # 6. Facebook par upload karo aur temp file clean karo
    try:
        post_to_facebook(img_path, caption)
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)

if __name__ == "__main__":
    main()
