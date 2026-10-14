import os
import requests

def post_to_facebook(image_path, caption):
    # GitHub Secrets ya Environment variables se values uthayega
    page_id = os.getenv("PAGE_ID")
    page_access_token = os.getenv("PAGE_ACCESS_TOKEN")

    if not page_id or not page_access_token:
        raise ValueError("PAGE_ID ya PAGE_ACCESS_TOKEN environment variables set nahi hain.")

    url = f"https://graph.facebook.com/v20.0/{page_id}/photos"

    payload = {
        'message': caption,
        'access_token': page_access_token
    }

    # Image file ko binary mode mein upload karein
    with open(image_path, 'rb') as img_file:
        files = {
            'source': img_file
        }
        response = requests.post(url, data=payload, files=files)

    res = response.json()

    # Agar Facebook error throw kare toh details print karein
    if response.status_code != 200 or 'error' in res:
        raise Exception(f"Facebook API Error: {res}")

    print(f"Post successfully published! Post ID: {res.get('id')}")
    return res
