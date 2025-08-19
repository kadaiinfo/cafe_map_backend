# Cafe Map Backend

鹿児島県のカフェ情報を管理・配信するバックエンドシステム。Instagram APIからカフェデータを取得し、Cloudflare KVストアに保存して配信します。

## 概要

このプロジェクトは以下の機能を提供します：

- Instagram APIからカフェ情報とメディアURLを自動取得
- 取得したデータをJSONファイルとして保存
- Cloudflare KVストアへの自動アップロード
- GitHub Actionsによる定期実行（毎日18:00 JST）

## ファイル構成

```
.
├── fetch_data.py              # Instagram APIからデータを初期取得
├── update_media_urls.py       # メディアURLを更新するメインスクリプト
├── cafe_data_kv.json         # カフェデータ（位置情報、店舗情報等）
├── instagram_posts.json      # Instagram投稿データ
├── .github/workflows/
│   └── update-media-urls.yml # 自動実行ワークフロー
└── README.md
```

## セットアップ

### 1. 環境変数の設定

以下の環境変数を設定してください：

```bash
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
```

### 2. GitHub Secretsの設定

GitHubリポジトリで以下のシークレットを設定：

- `INSTAGRAM_ACCESS_TOKEN`: Instagram API アクセストークン
- `CLOUDFLARE_API_TOKEN`: Cloudflare API トークン
- `CLOUDFLARE_ACCOUNT_ID`: Cloudflare アカウントID
- `CLOUDFLARE_KV_NAMESPACE_ID`: KV名前空間ID

### 3. 依存関係のインストール

```bash
pip install requests python-dotenv
```

## 使用方法

### 手動実行

```bash
# 初回データ取得
python fetch_data.py

# メディアURL更新
python update_media_urls.py
```

### 自動実行

GitHub Actionsにより毎日18:00 JST（9:00 UTC）に自動実行されます。

手動実行する場合：
1. GitHubリポジトリの「Actions」タブを開く
2. 「Update Media URLs」ワークフローを選択
3. 「Run workflow」をクリック

## データ構造

### cafe_data_kv.json
```json
[
  {
    "id": "17992270148826796",
    "store_name": "KITCHEN Q",
    "address": "霧島市隼人町小浜2320－1",
    "lat": 31.740374,
    "lng": 130.689957,
    "caption": "...",
    "media_url": "https://...",
    "permalink": "https://www.instagram.com/p/..."
  }
]
```

## 機能詳細

### fetch_data.py
- Instagram Graph APIからすべての投稿データを取得
- ページネーション対応で全データを順次取得
- `instagram_posts.json`に結果を保存

### update_media_urls.py
- Instagram APIから最新データを取得
- 既存の`cafe_data_kv.json`のメディアURLを更新
- バックアップファイルを自動作成
- ログ機能付き

### GitHub Actions ワークフロー
- 定期実行（cron: '0 9 * * *'）
- Python環境とWranglerのセットアップ
- スクリプト実行後、Cloudflare KVに自動アップロード
- 変更があった場合のみGitコミット

## Cloudflare KV連携

更新されたデータは自動的にCloudflare KVストアにアップロードされます：

```bash
# 手動アップロード例
wrangler kv key put cafe_data_kv.json --path=cafe_data_kv.json --namespace-id=YOUR_NAMESPACE_ID
```

## ログ

`update_media_urls.log`にスクリプトの実行ログが記録されます。

## 注意事項

- Instagram APIトークンには有効期限があります
- APIレート制限に注意してください
- Cloudflare KVの容量制限を確認してください

## トラブルシューティング

### Instagram APIエラー
- アクセストークンの有効性を確認
- Instagram APIの利用制限を確認

### Cloudflare KVエラー
- APIトークンの権限を確認
- アカウントIDと名前空間IDが正しいか確認

### GitHub Actionsエラー
- シークレットが正しく設定されているか確認
- ワークフローの実行ログを確認