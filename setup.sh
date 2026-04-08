#!/bin/bash
# セットアップスクリプト
# 依存パッケージのインストールと初期設定

set -e

echo "🚀 cn-audio-youtubeup セットアップを開始します..."
echo ""

# Pythonバージョン確認
echo "✓ Pythonバージョンを確認中..."
python3 --version

# 仮想環境の作成
echo ""
echo "✓ 仮想環境を作成中..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  → 仮想環境を作成しました"
else
    echo "  → 仮想環境は既に存在します"
fi

# 仮想環境を有効化
echo ""
echo "✓ 仮想環境を有効化中..."
source venv/bin/activate

# pipをアップグレード
echo ""
echo "✓ pipをアップグレード中..."
pip install --upgrade pip setuptools wheel

# 依存パッケージをインストール
echo ""
echo "✓ 依存パッケージをインストール中..."
pip install -r requirements.txt

# FFmpegがインストールされているか確認
echo ""
echo "✓ FFmpegの確認中..."
if ! command -v ffmpeg &> /dev/null; then
    echo "  ⚠ FFmpegがインストールされていません"
    echo "  インストール方法:"
    echo "    macOS: brew install ffmpeg"
    echo "    Ubuntu: sudo apt-get install ffmpeg"
    echo "    CentOS: sudo yum install ffmpeg"
else
    echo "  → FFmpegは既にインストールされています"
    ffmpeg -version | head -n 1
fi

# 必要なディレクトリ作成
echo ""
echo "✓ 必要なディレクトリを作成中..."
mkdir -p audio output config logs

# 設定ファイルの確認
echo ""
echo "✓ 設定ファイルの確認中..."
if [ ! -f "config/config.json" ]; then
    echo "  ⚠ config/config.json が見つかりません"
else
    echo "  → config/config.json は存在します"
fi

if [ ! -f "config/client_secret.json" ]; then
    echo "  ⚠ config/client_secret.json が見つかりません"
    echo "    Google Cloud Consoleから取得してください"
else
    echo "  → config/client_secret.json は存在します"
fi

# ロゴ画像の確認
echo ""
echo "✓ ロゴ画像の確認中..."
if [ -f "logo.PNG" ] || [ -f "logo.png" ]; then
    echo "  → ロゴ画像が見つかりました"
else
    echo "  ⚠ logo.PNG が見つかりません"
    echo "    プロジェクトルートに配置してください"
fi

# スクリプトに実行権限を付与
echo ""
echo "✓ スクリプトに実行権限を付与中..."
chmod +x audio_to_video.py youtube_uploader.py main.py

echo ""
echo "✅ セットアップが完了しました！"
echo ""
echo "【次のステップ】"
echo "1. audio/ フォルダに音声ファイル（wav, mp3等）を配置"
echo "2. YouTube認証: python3 youtube_uploader.py --auth-only (初回のみ)"
echo "3. 実行: python3 main.py"
echo ""
echo "詳細は README.md を参照してください"
echo ""
