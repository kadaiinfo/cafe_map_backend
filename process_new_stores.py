import json
import os
import time
from dotenv import load_dotenv
import google.generativeai as genai
import requests
import urllib.parse
import re

load_dotenv()
genai.configure(api_key=os.environ.get('GOOGLE_AI_API_KEY'))

def load_skipped_posts():
    """スキップされた投稿IDのリストを読み込み"""
    try:
        with open('skipped_posts.json', 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_skipped_posts(skipped_ids):
    """スキップされた投稿IDのリストを保存"""
    with open('skipped_posts.json', 'w', encoding='utf-8') as f:
        json.dump(list(skipped_ids), f, ensure_ascii=False, indent=2)

def find_new_stores():
    """instagram_posts.jsonとcafe_data_kv.jsonを比較して新しい店舗IDを特定"""
    with open('instagram_posts.json', 'r', encoding='utf-8') as f:
        instagram_posts = json.load(f)
    
    with open('cafe_data_kv.json', 'r', encoding='utf-8') as f:
        cafe_data = json.load(f)
    
    # 既存店舗IDとスキップ済みIDのセットを作成
    existing_ids = set(store['id'] for store in cafe_data)
    skipped_ids = load_skipped_posts()
    
    # instagram_posts.jsonから新しい投稿のみを抽出（既存・スキップ済みを除外）
    new_posts = []
    for post in instagram_posts:
        if post['id'] not in existing_ids and post['id'] not in skipped_ids:
            new_posts.append(post)
    
    print(f"既存店舗数: {len(existing_ids)}")
    print(f"スキップ済み投稿数: {len(skipped_ids)}")
    print(f"Instagram投稿数: {len(instagram_posts)}")
    print(f"新規処理対象数: {len(new_posts)}")
    
    return new_posts

def extract_store_info(caption):
    """Gemini APIを使って投稿から店舗名と住所を抽出"""
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
    
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    response = model.generate_content(prompt)
    
    try:
        result = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
        return result
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Response text: {response.text}")
        return {"store_name": None, "address": None}

def clean_address(address):
    """住所から郵便番号を除去"""
    if not address:
        return address
    
    # 郵便番号パターンを除去 (〒123-4567, 123-4567形式)
    address_cleaned = re.sub(r'〒?\d{3}-?\d{4}\s*', '', address)
    return address_cleaned.strip()

def get_coordinates(address):
    """国土地理院APIで住所を座標に変換"""
    if not address:
        return None, None
    
    cleaned_address = clean_address(address)
    GeospatialUrl = "https://msearch.gsi.go.jp/address-search/AddressSearch?q="
    
    try:
        s_quote = urllib.parse.quote(cleaned_address)
        response = requests.get(GeospatialUrl + s_quote)
        response.raise_for_status()
        
        data = response.json()
        if data and len(data) > 0:
            coordinates = data[0]["geometry"]["coordinates"]
            return coordinates[1], coordinates[0]  # lat, lng
        else:
            print(f"座標が見つかりませんでした: {cleaned_address}")
            return None, None
    except Exception as e:
        print(f"座標取得エラー ({cleaned_address}): {e}")
        return None, None

def process_new_stores():
    """新しい店舗データを処理してcafe_data_kv.jsonに追加"""
    # 新しい店舗を特定
    new_posts = find_new_stores()
    
    if not new_posts:
        print("新しい店舗はありません。")
        return
    
    processed_stores = []
    skipped_ids = load_skipped_posts()
    
    for i, post in enumerate(new_posts):
        print(f"処理中 {i+1}/{len(new_posts)}: {post['id']}")
        
        # 投稿から店舗情報を抽出
        if 'caption' in post and post['caption']:
            try:
                store_info = extract_store_info(post['caption'])
                if not isinstance(store_info, dict):
                    print(f"  エラー: store_infoが辞書ではありません: {type(store_info)}")
                    store_info = {"store_name": None, "address": None}
                time.sleep(7)  # API制限対策
            except Exception as e:
                print(f"  店舗情報抽出エラー: {e}")
                store_info = {"store_name": None, "address": None}
        else:
            store_info = {"store_name": None, "address": None}
        
        # 座標を取得
        lat, lng = None, None
        if isinstance(store_info, dict) and store_info.get('address'):
            lat, lng = get_coordinates(store_info['address'])
            time.sleep(0.5)  # API制限対策
        
        # 店舗名と住所が両方取得できた場合のみ追加
        if (isinstance(store_info, dict) and 
            store_info.get('store_name') and 
            store_info.get('address') and 
            lat and lng):
            processed_store = {
                'id': post['id'],
                'store_name': store_info['store_name'],
                'address': store_info['address'],
                'lat': lat,
                'lng': lng,
                'caption': post.get('caption', ''),
                'media_url': post.get('media_url', ''),
                'permalink': post.get('permalink', ''),
                'timestamp': post.get('timestamp', ''),
                'username': post.get('username', ''),
                'like_count': post.get('like_count', 0),
                'comments_count': post.get('comments_count', 0),
                'media_type': post.get('media_type', '')
            }
            processed_stores.append(processed_store)
            print(f"  追加: {store_info['store_name']} - {store_info['address']}")
        else:
            print(f"  スキップ: 店舗情報または座標が不完全")
            # スキップされた投稿IDを記録
            skipped_ids.add(post['id'])
    
    # cafe_data_kv.jsonに追加
    if processed_stores:
        with open('cafe_data_kv.json', 'r', encoding='utf-8') as f:
            cafe_data = json.load(f)
        
        cafe_data.extend(processed_stores)
        
        with open('cafe_data_kv.json', 'w', encoding='utf-8') as f:
            json.dump(cafe_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n{len(processed_stores)}件の新しい店舗をcafe_data_kv.jsonに追加しました。")
    else:
        print("\n追加できる新しい店舗はありませんでした。")
    
    # スキップリストを保存
    save_skipped_posts(skipped_ids)
    print(f"スキップリストに{len(skipped_ids) - len(load_skipped_posts())}件追加しました。")

if __name__ == "__main__":
    process_new_stores()