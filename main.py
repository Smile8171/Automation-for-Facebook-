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

def get_caption_and_prompt(topic: str):
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

    # Direct Google REST API endpoints (No SDK issues)
    models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    text = None

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_KEY}"
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        res_json = response.json()

        if "candidates" in res_json:
            text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            break
        else:
            print(f"Tried {model_name}, error: {res_json.get('error', {}).get('message', res_json)}")

    if not text:
        raise Exception("Gemini API call failed across all models. Please check GEMINI_API_KEY.")

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
