import urllib.parse
import requests

appid = "dj00aiZpPVRySEhNVkxyMnZhciZzPWNvbnN1bWVyc2VjcmV0Jng9M2I-"
query = "Tromme"
url = "https://map.yahooapis.jp/search/local/V1/localSearch"
params = {
    "appid": appid,
    "query": query,
    "lat": 31.5840,
    "lon": 130.5410,
    "dist": 10,          # 半径が狭すぎると0件になります．必要に応じて広げてください．
    "ac": 46,           # 鹿児島県
    # "gc": "01",         # 飲食店
    "sort": "dist",     # 近い順
    "results": 1,       # 1件だけ取得＝最寄り
    "output": "json",
}

res = requests.get(url, params=params)
data = res.json()

# 最小限の安全化：Featureが無ければメッセージを出して終了
feat = data.get("Feature") or []
if not feat:
    print("該当なし．検索条件を緩めてください．")
else:
    print(feat[0]["Name"])
    print(feat[0]["Geometry"]["Coordinates"])  # 形式は「経度,緯度」です．
