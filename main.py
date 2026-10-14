import os
import random
import requests
import google.generativeai as genai

# Environment Variables / GitHub Secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PAGE_ID = os.getenv("PAGE_ID")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def pick_reference_image(folder_path="references"):
    """Folder se image file pick karta hai"""
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder '{folder_path}' nahi mila!")
    
    valid_exts = ('.jpg', '.jpeg', '.png', '.webp')
    photos = [
        os.path.join(folder_path, f) 
        for f in os.listdir(folder_path) 
        if f.lower().endswith(valid_exts)
    ]
    
    if not photos:
        raise ValueError(f"Folder '{folder_path}' mein koi photo nahi mili!")
    
    selected_photo = random.choice(photos)
    print(f"Selected reference image: {selected_photo}")
    return selected_photo

def generate_caption(topic):
    """Romanized Hindi (Hinglish) mein caption generate karta hai"""
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
        print(f"Caption generate error: {e}")
        return "Har nayi subah ek nayi umeed aur nayi taazgi lekar aati hai! Apne sapno ke peeche mehnat karte raho. #NayiSubah #PositiveVibes #Motivation #DailyInspiration"

def process_daily_image(ref_image_path):
    """Reference photo return karta hai"""
    print(f"Processing image using reference: {ref_image_path}...")
    return ref_image_path

def post_to_facebook(image_path, caption):
    """Facebook Page ke /{PAGE_ID}/photos endpoint par post karta hai"""
    print("Uploading to Facebook Page...")

    if not PAGE_ID or not PAGE_ACCESS_TOKEN:
        raise ValueError("PAGE_ID ya PAGE_ACCESS_TOKEN environment variables set nahi hain.")

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
    # 1. Reference photo select karo
    ref_photo = pick_reference_image("references")

    # 2. Hinglish theme select karo
    themes = [
        "Subah ki shuruat, positivity aur naye iraade",
        "Zindagi ki khoobsurti aur self-growth",
        "Aesthetic lifestyle, shanti aur confidence",
        "Koshish aur sapno ko poora karne ki umeed",
        "Muskurahat aur har din ko behtar banane ki soch"
    ]
    current_topic = random.choice(themes)
    print(f"Today's Topic: {current_topic}")

    # 3. Romanized Hindi caption generate karo
    caption = generate_caption(current_topic)
    print(f"Caption ready:\n{caption}\n")

    # 4. Image prepare karo
    final_image = process_daily_image(ref_photo)

    # 5. Facebook Page par upload karo
    post_to_facebook(final_image, caption)

if __name__ == "__main__":
    main()
