import os
import random
import requests
from openai import OpenAI
from google import genai

# Environments
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

openai_client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None
gemini_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

# Topic pool - AI roz inme se ek choose karega ya randomly rotate hoga
TOPICS = [
    "Latest AI breakthroughs and futuristic gadgets",
    "Car maintenance, engine health and automotive DIY hacks",
    "Smart home gadgets and future tech lifestyle",
    "Productivity hacks and automated coding tools",
    "Space exploration and astronomy discoveries"
]

def get_caption_and_prompt(topic: str):
    prompt = f"""
    You are a viral social media manager.
    Create a high-engagement Facebook post about: '{topic}'.
    Format response EXACTLY like this:
    CAPTION: [Write engaging caption with line breaks, hooks, and 4-5 relevant hashtags]
    IMAGE_PROMPT: [Write a hyper-detailed 1:1 photorealistic digital art prompt for DALL-E 3]
    """
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        text = response.text
    except Exception as e:
        print(f"Gemini fallback trigger: {e}")
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.choices[0].message.content

    caption = text.split("CAPTION:")[1].split("IMAGE_PROMPT:")[0].strip()
    img_prompt = text.split("IMAGE_PROMPT:")[1].strip()
    return caption, img_prompt

def generate_image(image_prompt: str) -> str:
    print("Generating image via DALL-E 3...")
    res = openai_client.images.generate(
        model="dall-e-3",
        prompt=image_prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )
    return res.data[0].url

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
    img_url = generate_image(img_prompt)
    post_to_facebook(img_url, caption)
