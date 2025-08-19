import requests
import json
from urllib.parse import urlparse

ACCESS_TOKEN = "IGAASNrIOurLFBZAFAxZA2YzbEpWYjJHUktoQkVlYnI3T0RNSl9ucEg3QXdDSF9JUnZApUUtoSXQxZAlZAtdGg1UUUxNkRmZA21vSDNYbUhYSlpsNWhYTWZAHMC1ZAZAzRzZA2twY2RGeXlWdmQ1bDJadDVqd05hS1Y0ZAWhBNmN3ZAVdDd2RIdwZDZD"       # Instagram Loginならユーザートークン．Facebook Loginならページトークン．
IG_USER_ID = "24958190963767720"  
HOST = "graph.instagram.com"  # Facebook Loginなら graph.facebook.com

fields = "id,caption,media_type,media_url,permalink,timestamp,username,like_count,comments_count,media_product_type"

url = f"https://{HOST}/v23.0/{IG_USER_ID}/media"
params = {
    "access_token": ACCESS_TOKEN,
    "fields": fields,
    "limit": 100  # 1リクエストの最大近くまで引き上げ
}

all_items = []

while url:
    # nextに完全URLが入るので，nextを使うときはparamsを付け直さない
    resp = requests.get(url, params=params if "?" not in url else None)
    payload = resp.json()
    if "error" in payload:
        raise RuntimeError(payload["error"])

    all_items.extend(payload.get("data", []))

    # 次ページのURLを取得
    url = payload.get("paging", {}).get("next")
    # 2回目以降はparamsを空にしておく（nextはクエリ付きURLなのでそのまま使う）
    params = None

print(f"total: {len(all_items)}")

# JSONファイルに保存
with open('instagram_posts.json', 'w', encoding='utf-8') as f:
    json.dump(all_items, f, ensure_ascii=False, indent=2)

print("instagram_posts.json に保存しました")
print(json.dumps(all_items[:3], indent=2, ensure_ascii=False))  # 例として先頭3件だけ表示
