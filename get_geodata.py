import json
import pandas as pd
import requests
import urllib
import time

# 国土地理院API
GeospatialUrl = "https://msearch.gsi.go.jp/address-search/AddressSearch?q="


def clean_address(address):
    """住所から郵便番号を除去"""
    if not address:
        return address
    
    import re
    # 郵便番号パターンを除去 (〒123-4567, 123-4567形式)
    address_cleaned = re.sub(r'〒?\d{3}-?\d{4}\s*', '', address)
    return address_cleaned.strip()

def get_coordinates(address):
    """国土地理院APIで住所を座標に変換"""
    if not address:
        return None, None
    
    # 郵便番号を除去
    cleaned_address = clean_address(address)
    
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

def process_instagram_posts():
    """Instagram投稿データを処理して座標を追加"""
    # JSONファイルを読み込み
    with open('instagram_posts.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)
    
    print(f"処理対象の投稿数: {len(posts)}")
    
    # 結果を格納するリスト
    processed_data = []
    
    for i, post in enumerate(posts):
        print(f"処理中 {i+1}/{len(posts)}: {post['id']}")
        
        # JSONのaddressとstore_nameを取得
        address = post.get('address')
        store_name = post.get('store_name')
        
        # 座標を取得
        lat, lng = None, None
        if address:
            lat, lng = get_coordinates(address)
            print(f"  住所: {address}")
            if lat and lng:
                print(f"  座標: ({lat}, {lng})")
            else:
                print("  座標取得失敗")
        else:
            print("  住所が見つかりません")
        
        # データを整理
        processed_data.append({
            'id': post['id'],
            'store_name': store_name,
            'address': address,
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
        })
        
        # API制限対策で遅延
        time.sleep(0.5)
    
    return processed_data

if __name__ == "__main__":
    # Instagram投稿データを処理
    processed_data = process_instagram_posts()
    
    # データフレームに変換
    df = pd.DataFrame(processed_data)
    
    # 座標が取得できたデータのみフィルタ
    df_with_coords = df[df['lat'].notna() & df['lng'].notna()]
    
    print(f"\n結果:")
    print(f"  全投稿数: {len(df)}")
    print(f"  座標取得成功: {len(df_with_coords)}")
    print(f"  成功率: {len(df_with_coords)/len(df)*100:.1f}%")
    
    # CSVに保存
    df.to_csv('./instagram_posts_with_coords.csv', encoding='utf-8', index=False)
    df_with_coords.to_csv('./instagram_posts_coords_only.csv', encoding='utf-8', index=False)
    
    # JSONにも保存（座標付きのみ）
    coords_data = df_with_coords.to_dict('records')
    with open('instagram_posts_with_coords.json', 'w', encoding='utf-8') as f:
        json.dump(coords_data, f, ensure_ascii=False, indent=2)
    
    print("\n保存完了:")
    print("  - instagram_posts_with_coords.csv (全データ)")
    print("  - instagram_posts_coords_only.csv (座標付きのみ)")
    print("  - instagram_posts_with_coords.json (座標付きのみ)")