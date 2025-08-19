import json
import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ.get('GOOGLE_AI_API_KEY'))

def extract_store_info(caption):
    prompt = f"""
    以下のInstagramの投稿文から店舗名と住所を抽出してください。
    店舗名と住所が明記されている場合のみ抽出し、JSONフォーマットで返してください。
    住所は「【住所】」などの記載があるもののみ抽出してください。
    
    投稿文:
    {caption}
    
    出力形式:
    {{"store_name": "店舗名", "address": "住所"}}
    
    店舗名や住所が見つからない場合は:
    {{"store_name": null, "address": null}}
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    try:
        result = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
        return result
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Response text: {response.text}")
        return {"store_name": None, "address": None}

def process_instagram_posts(limit=None):
    with open('instagram_posts_genpon.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)
    
    if limit:
        posts = posts[:limit]
        print(f"Processing first {limit} posts for testing")
    
    for i, post in enumerate(posts):
        if 'caption' in post and post['caption']:
            try:
                print(f"Processing post {i+1}/{len(posts)}: {post['id']}")
                store_info = extract_store_info(post['caption'])
                post['store_name'] = store_info['store_name']
                post['address'] = store_info['address']
                print(f"  Store: {store_info['store_name']}, Address: {store_info['address']}")
                
                # レート制限対策で遅延
                time.sleep(7)
                
            except Exception as e:
                print(f"Error processing post {post['id']}: {e}")
                post['store_name'] = None
                post['address'] = None
        else:
            post['store_name'] = None
            post['address'] = None
    
    with open('instagram_posts_genpon.json', 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    
    print("Processing completed. Results saved to instagram_posts.json")

if __name__ == "__main__":
    process_instagram_posts()