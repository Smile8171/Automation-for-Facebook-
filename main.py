import os
import random
import urllib.parse
import requests
import google.generativeai as genai

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

TOPICS = [
    "Latest AI breakthroughs and futuristic gadgets",
    "Car maintenance, engine health and automotive DIY hacks",
    "Smart home gadgets and future tech lifestyle",
    "Productivity hacks and automated coding tools",
    "Space exploration and astronomy discoveries"
]

def get_caption_and_prompt(topic: str):
    prompt = f"""
    Create a high-engagement Facebook post about: '{topic}'.
    Format response strictly like this:
    CAPTION: [Write engaging caption with emojis and 4-5 hashtags]
    IMAGE_PROMPT: [Write a concise, vivid image prompt under 30 words]
    """
    
    # Stable models fallback list
    candidate_models = ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-pro']
    text = ""
    
    for m in candidate_models:
        try:
            model = genai.GenerativeModel(m)
            response = model.generate_content(prompt)
            text = response.text
            if text:
                break
        except Exception:
            continue
            
    if not text:
        raise Exception("Unable to get response from Gemini models.")

    caption = text.split("CAPTION:")[1].split("IMAGE_PROMPT:")[0].strip()
    img_prompt = text.split("IMAGE_PROMPT:")[1].strip()
    return caption, img_prompt

def generate_image_free(prompt: str) -> str:
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
    return image_url

def post_to_facebook(img_url: str, caption: str):
    url = f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/photos"
    data = {
        "url": img_url,
        "message": caption,
        "access_token": FB_ACCESS_TOKEN
    }
    r = requests.post(url, data=data)
    res = r.json()
    if "id" in res:
        print(f"Posted successfully! ID: {res['id']}")
    else:
        raise Exception(f"Facebook API Error: {res}")

if __name__ == "__main__":
    selected_topic = random.choice(TOPICS)
    print(f"Today's Topic: {selected_topic}")
    caption, img_prompt = get_caption_and_prompt(selected_topic)
    img_url = generate_image_free(img_prompt)
    post_to_facebook(img_url, caption)
