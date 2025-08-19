#!/usr/bin/env python3
"""
Instagram APIからデータを取得してcafe_data_kv.jsonのmedia_urlを更新するスクリプト
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_media_urls.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MediaUrlUpdater:
    def __init__(self):
        # Instagram API設定
        self.ACCESS_TOKEN = "IGAASNrIOurLFBZAFAxZA2YzbEpWYjJHUktoQkVlYnI3T0RNSl9ucEg3QXdDSF9JUnZApUUtoSXQxZAlZAtdGg1UUUxNkRmZA21vSDNYbUhYSlpsNWhYTWZAHMC1ZAZAzRzZA2twY2RFeXlWdmQ1bDJadDVqd05hS1Y0ZAWhBNmN3ZAVdDd2RIdwZDZD"
        self.IG_USER_ID = "24958190963767720"
        self.HOST = "graph.instagram.com"
        self.fields = "id,caption,media_type,media_url,permalink,timestamp,username,like_count,comments_count,media_product_type"
        
        # ファイルパス
        self.cafe_data_file = "cafe_data_kv.json"
        self.instagram_posts_file = "instagram_posts.json"
        
    def fetch_instagram_data(self) -> List[Dict]:
        """Instagram APIからデータを取得（fetch_data.pyと同じ方式）"""
        logger.info("Instagram APIからデータを取得開始")
        
        url = f"https://{self.HOST}/v23.0/{self.IG_USER_ID}/media"
        params = {
            "access_token": self.ACCESS_TOKEN,
            "fields": self.fields,
            "limit": 100
        }
        
        all_items = []
        
        try:
            while url:
                # nextに完全URLが入るので，nextを使うときはparamsを付け直さない
                resp = requests.get(url, params=params if "?" not in url else None)
                payload = resp.json()
                
                if "error" in payload:
                    logger.error(f"Instagram API エラー: {payload['error']}")
                    raise RuntimeError(payload["error"])
                
                items = payload.get("data", [])
                all_items.extend(items)
                logger.info(f"取得済みアイテム数: {len(all_items)}")
                
                # 次ページのURLを取得
                url = payload.get("paging", {}).get("next")
                # 2回目以降はparamsを空にしておく（nextはクエリ付きURLなのでそのまま使う）
                params = None
                
        except requests.RequestException as e:
            logger.error(f"API リクエストエラー: {e}")
            logger.info("既存のinstagram_posts.jsonファイルを使用します")
            return self.load_existing_instagram_data()
        except Exception as e:
            logger.error(f"予期しないエラー: {e}")
            logger.info("既存のinstagram_posts.jsonファイルを使用します")
            return self.load_existing_instagram_data()
            
        logger.info(f"Instagram データ取得完了: 総数 {len(all_items)}")
        return all_items
        
    def load_existing_instagram_data(self) -> List[Dict]:
        """既存のInstagram投稿データを読み込み"""
        try:
            with open(self.instagram_posts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"既存のInstagramデータを読み込み: {len(data)} 件")
            return data
        except FileNotFoundError:
            logger.error(f"{self.instagram_posts_file} が見つかりません")
            raise
        except Exception as e:
            logger.error(f"既存Instagramデータ読み込みエラー: {e}")
            raise
        
    def save_instagram_data(self, data: List[Dict]) -> None:
        """Instagram データをJSONファイルに保存"""
        try:
            with open(self.instagram_posts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Instagram データを {self.instagram_posts_file} に保存完了")
        except Exception as e:
            logger.error(f"Instagram データ保存エラー: {e}")
            raise
            
    def load_cafe_data(self) -> List[Dict]:
        """cafe_data_kv.jsonを読み込み"""
        try:
            with open(self.cafe_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"カフェデータ読み込み完了: {len(data)} 件")
            return data
        except FileNotFoundError:
            logger.error(f"{self.cafe_data_file} が見つかりません")
            raise
        except Exception as e:
            logger.error(f"カフェデータ読み込みエラー: {e}")
            raise
            
    def update_media_urls(self, cafe_data: List[Dict], instagram_data: List[Dict]) -> List[Dict]:
        """カフェデータのmedia_urlを更新"""
        logger.info("media_url更新処理開始")
        
        # Instagram投稿をIDでマッピング
        instagram_map = {item["id"]: item for item in instagram_data}
        
        updated_count = 0
        not_found_count = 0
        
        for cafe in cafe_data:
            cafe_id = cafe.get("id")
            if not cafe_id:
                logger.warning(f"カフェデータにIDがありません: {cafe.get('store_name', 'Unknown')}")
                continue
                
            if cafe_id in instagram_map:
                old_url = cafe.get("media_url", "")
                new_url = instagram_map[cafe_id].get("media_url", "")
                
                if old_url != new_url:
                    cafe["media_url"] = new_url
                    updated_count += 1
                    logger.info(f"更新: {cafe.get('store_name', 'Unknown')} - ID: {cafe_id}")
                else:
                    logger.debug(f"変更なし: {cafe.get('store_name', 'Unknown')} - ID: {cafe_id}")
            else:
                not_found_count += 1
                logger.warning(f"Instagram投稿が見つかりません: {cafe.get('store_name', 'Unknown')} - ID: {cafe_id}")
                
        logger.info(f"media_url更新完了: 更新数 {updated_count}, 見つからない数 {not_found_count}")
        return cafe_data
        
    def save_cafe_data(self, data: List[Dict]) -> None:
        """更新されたカフェデータを保存"""
        try:
            # バックアップを作成
            backup_file = f"{self.cafe_data_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if os.path.exists(self.cafe_data_file):
                with open(self.cafe_data_file, 'r', encoding='utf-8') as src:
                    with open(backup_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                logger.info(f"バックアップ作成: {backup_file}")
            
            # 新しいデータを保存
            with open(self.cafe_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"カフェデータ保存完了: {self.cafe_data_file}")
            
        except Exception as e:
            logger.error(f"カフェデータ保存エラー: {e}")
            raise
            
    def run(self) -> None:
        """メイン処理を実行"""
        try:
            logger.info("=== media_url更新処理開始 ===")
            
            # 1. Instagram APIからデータ取得
            instagram_data = self.fetch_instagram_data()
            
            # 2. Instagram データを保存
            self.save_instagram_data(instagram_data)
            
            # 3. カフェデータを読み込み
            cafe_data = self.load_cafe_data()
            
            # 4. media_urlを更新
            updated_cafe_data = self.update_media_urls(cafe_data, instagram_data)
            
            # 5. 更新されたカフェデータを保存
            self.save_cafe_data(updated_cafe_data)
            
            logger.info("=== media_url更新処理完了 ===")
            
        except Exception as e:
            logger.error(f"処理中にエラーが発生しました: {e}")
            raise

def main():
    """メイン関数"""
    updater = MediaUrlUpdater()
    updater.run()

if __name__ == "__main__":
    main()