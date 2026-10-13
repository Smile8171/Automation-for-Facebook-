import os
import random
import urllib.parse
import requests

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

TOPICS = [
    "Latest AI breakthroughs and futuristic gadgets",
    "Car maintenance, engine health and automotive DIY hacks",
    "Smart home gadgets and future tech lifestyle",
    "Productivity hacks and automated coding tools",
    "Space exploration and astronomy discoveries"
]

def find_active_gemini_model():
    # Google API se directly active supported models ki list nikalte hain
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}"
    res = requests.get(url).json()

    if "models" not in res:
        raise Exception(f"Invalid API Key or API error: {res.get('error', {}).get('message', res)}")

    # Jo model generateContent support karta ho use choose karein
    for m in res["models"]:
        name = m.get("name", "")
        methods = m.get("supportedGenerationMethods", [])
        if "generateContent" in methods:
            # Prefers flash or default models
            if "flash" in name:
                return name
    
    # Fallback to first capable model
    for m in res["models"]:
        if "generateContent" in m.get("supportedGenerationMethods", []):
            return m.get("name")

    raise Exception("No content generation model found for this key.")

def get_caption_and_prompt(topic: str):
    model_name = find_active_gemini_model()
    print(f"Using dynamically detected model: {model_name}")

    prompt_text = f"""
    Create a high-engagement Facebook post about: '{topic}'.
    Format response strictly like this:
    CAPTION: [Write engaging caption with emojis and 4-5 hashtags]
    IMAGE_PROMPT: [Write a concise, vivid image prompt under 30 words]
    """

    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_KEY}"
    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
    res_json = response.json()

    if "candidates" not in res_json:
        raise Exception(f"Gemini error: {res_json.get('error', {}).get('message', res_json)}")

    text = res_json["candidates"][0]["content"]["parts"][0]["text"]
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
