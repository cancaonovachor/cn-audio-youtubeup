# cn-audio-youtubeup

音声ファイル（WAV、MP3等）をYouTubeの高品質な動画ファイルに自動変換し、YouTubeにアップロードするツール

## 特徴

✅ **一括処理**: フォルダ内のすべての音声ファイルを自動処理  
✅ **高品質な音声**: アップロード時の音声品質を192kbpsで保持  
✅ **簡単セットアップ**: ワンコマンドで依存パッケージをインストール  
✅ **OAuth 2.0認証**: Google公式の認可フローでセキュアに認証  
✅ **ロギング機能**: すべてのプロセスを詳細にログ記録  
✅ **エラーハンドリング**: 失敗ファイルの特定と詳細なエラー報告  

## 必要な環境

- Python 3.8以上
- FFmpeg
- インターネット接続（YouTube APIアクセス用）

## インストール

### 1. FFmpegをインストール

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu:**
```bash
sudo apt-get install ffmpeg
```

**CentOS/RHEL:**
```bash
sudo yum install ffmpeg
```

### 2. このプロジェクトのセットアップを実行
```bash
cd cn-audio-youtubeup
bash setup.sh
```

または手動でセットアップ：
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## セットアップ後の初期設定

### 1. ロゴ画像の配置

プロジェクトルートに `logo.PNG` を配置してください

```
cn-audio-youtubeup/
├── logo.PNG         ← ここに配置
├── audio/
├── output/
└── ...
```

### 2. YouTube OAuth認証

YouTube APIで認証するには、Google Cloud Consoleで以下を設定する必要があります：

**步骤:**
1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成
3. YouTube Data API v3を有効化
4. OAuth同意画面を設定
5. デスクトップアプリ用のOAuth 2.0クライアントを作成
6. `client_secret.json` をダウンロード
7. `config/client_secret.json` に配置

**既存のGoogle認証情報を使用する場合:**
```bash
# 提供された client_secret_*.json を config/ にコピー
cp ~/Downloads/client_secret_*.json config/client_secret.json
```

## 使用方法

### 完全自動化（変換＋アップロード）

```bash
source venv/bin/activate
python3 main.py
```

### 変換のみ

```bash
python3 main.py --skip-upload
```

### アップロードのみ

```bash
python3 main.py --skip-conversion
```

### 詳細ログで実行

```bash
python3 main.py --verbose
```

## ディレクトリ構造

```
cn-audio-youtubeup/
├── audio/                    # 入力音声ファイル（WAV、MP3等）
├── output/                   # 出力動画ファイル（MP4）
├── config/                   # 設定ファイル
│   ├── config.json          # プロジェクト設定
│   ├── client_secret.json   # YouTube OAuth認証
│   └── youtube_token.pickle # 認証トークン（初回生成）
├── logs/                     # ログファイル
│   ├── conversion.log       # 変換ログ
│   ├── upload.log           # アップロードログ
│   └── main.log             # メインログ
├── audio_to_video.py        # 音声→動画変換スクリプト
├── youtube_uploader.py      # YouTubeアップロードスクリプト
├── main.py                  # メイン実行スクリプト
├── setup.sh                 # セットアップスクリプト
├── requirements.txt         # Python依存パッケージ
├── logo.PNG                 # 動画に使用する画像（ロゴ）
└── README.md               # このファイル
```

## 設定ファイル（config/config.json）

### 動画設定
```json
"video": {
  "resolution": "720p",      // "720p", "1080p", "4K"
  "fps": 30,                 // フレームレート
  "video_bitrate": "500k",   // ビデオビットレート
  "audio_bitrate": "192k",   // 音声ビットレート（高品質）
  "audio_sample_rate": 48000 // サンプリングレート
}
```

### YouTube設定
```json
"upload": {
  "default_category": "22",              // 22=音楽
  "default_privacy_status": "private",   // "private", "unlisted", "public"
  "default_language": "ja",              // 言語
  "auto_publish": false,                 // 自動公開（推奨: false）
  "title_template": "{filename}",        // タイトルテンプレート
  "description_template": "..."          // 説明文テンプレート
}
```

## サポートされる音声形式

- `.wav` - WAV形式
- `.mp3` - MP3形式
- `.flac` - FLAC形式
- `.m4a` - M4A形式
- `.aac` - AAC形式

## トラブルシューティング

### エラー: "FFmpeg not found"
FFmpegがインストールされていません。上記のインストール方法を参照してください。

### エラー: "client_secret.json not found"
`config/client_secret.json` が見つかりません。
Google Cloud Consoleから認証ファイルをダウンロードして配置してください。

### YouTubeアップロード時のエラー

**「403 Forbidden」エラー:**
- YouTube APIが有効になっていない
- OAuth同意画面が設定されていない

**「411 Length Required」エラー:**
- ファイルサイズが大きすぎる
- ネットワーク接続を確認

### 音声ファイルが検出されない
- `audio/` フォルダにファイルを配置しているか確認
- ファイル拡張子が `.wav`, `.mp3` 等のサポート形式か確認
- パーミッションを確認（読み取り可能か）

### 変換は成功したがアップロードが失敗
- YouTube APIの割り当てを確認
- アカウントがYouTubeチャンネルに紐付いているか確認
- ネットワーク接続を確認

## パフォーマンス

### 処理時間の目安

| 音声長 | 変換時間 | アップロード時間 | 合計 |
|-------|--------|--------------|-----|
| 5分   | 2-3分  | 1-2分 (10Mbps) | 3-5分 |
| 30分  | 10-15分 | 5-10分 (10Mbps) | 15-25分 |
| 60分  | 20-30分 | 10-15分 (10Mbps) | 30-45分 |

※ ネットワーク速度やマシンスペックに依存

## ログ確認

各処理のログはログフォルダに保存されます：

```bash
# 最新のログを確認
tail -f logs/main.log

# 特定のプロセスのみ確認
tail -f logs/conversion.log    # 変換ログ
tail -f logs/upload.log        # アップロードログ
```

## 重要な注意事項

⚠️ **セキュリティに関する注意:**
- `config/client_secret.json` は絶対に公開しないでください
- `.gitignore` に認証ファイルが含まれています

⚠️ **YouTubeの利用規約:**
- アップロードされた動画は著作権ポリシーに準拠する必要があります
- デフォルトでは「私人限定」に設定されています

⚠️ **データ使用料:**
- YouTube Data API v3はデフォルトで月間1,000,000クォータを無料で使用できます

## コマンドお詳細

### audio_to_video.py - 音声→動画変換

```python
from audio_to_video import AudioToVideoConverter

converter = AudioToVideoConverter()
results = converter.process_all_audio_files()
```

### youtube_uploader.py - YouTubeアップロード

```python
from youtube_uploader import YouTubeUploader

uploader = YouTubeUploader()
results = uploader.process_all_videos()
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## サポート

問題が発生した場合は、以下の情報を記録してください：
- エラーメッセージ全体
- ログファイルの内容（`logs/main.log`）
- 実行したコマンド
- 処理対象のファイル情報

## 今後の改善予定

- [ ] GUIインターフェース
- [ ] バッチ処理の最適化
- [ ] プレイリスト自動作成
- [ ] ウォッチフォルダー機能（自動監視）
- [ ] 複数アカウント対応
- [ ] ビデオテンプレートのカスタマイズ

---

最後に、このツールが役に立つことを願っています！
