#!/usr/bin/env python3
"""
動画ファイルをYouTubeにアップロードするスクリプト
OAuth 2.0認証を使用して認可されたアップロードを実行
"""

import os
import json
import sys
import pickle
import logging
from pathlib import Path
from datetime import datetime

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ログディレクトリ作成
os.makedirs('logs', exist_ok=True)


class YouTubeUploader:
    """YouTubeに動画をアップロードするクラス"""
    
    # YouTube API設定
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    API_SERVICE_NAME = 'youtube'
    API_VERSION = 'v3'
    
    # アップロード設定
    RESUMABLE_UPLOAD_CHUNK_SIZE = 256 * 1024 * 1024  # 256MB
    
    def __init__(self, config_path: str = './config/config.json'):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config = self._load_config(config_path)
        self.video_output_dir = self.config['paths']['video_output']
        self.client_secret_file = self.config['youtube']['client_secret_file']
        self.token_file = self.config['youtube']['token_file']
        
        # YouTube APIクライアント
        self.youtube = None
        self._authenticate()
        
        logger.info("YouTubeアップローダー初期化完了")
    
    def _load_config(self, config_path: str) -> dict:
        """設定ファイルを読み込む"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _authenticate(self) -> None:
        """OAuth 2.0で認証"""
        credentials = None
        
        # 既存のトークンがあれば読み込む
        if os.path.exists(self.token_file):
            logger.info(f"既存のトークンを読み込み中: {self.token_file}")
            with open(self.token_file, 'rb') as token:
                credentials = pickle.load(token)
        
        # 認証情報が無いか無効なら新規認証
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                logger.info("トークンをリフレッシュ中...")
                credentials.refresh(Request())
            else:
                logger.info("新規認証フロー開始")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_file,
                    self.SCOPES
                )
                credentials = flow.run_local_server(port=0)
            
            # トークンを保存
            with open(self.token_file, 'wb') as token:
                pickle.dump(credentials, token)
            logger.info(f"トークンを保存しました: {self.token_file}")
        
        # YouTube APIクライアントを作成
        self.youtube = build(
            self.API_SERVICE_NAME,
            self.API_VERSION,
            credentials=credentials
        )
        logger.info("YouTube APIクライアント作成完了")
    
    def _get_video_metadata(self, video_filename: str) -> dict:
        """
        動画のメタデータを生成
        
        Args:
            video_filename: 動画ファイル名（拡張子あり）
            
        Returns:
            メタデータ辞書
        """
        # ファイル名から.mp4を除去してタイトルにする
        title = Path(video_filename).stem
        
        # テンプレートからタイトル・説明文を生成
        title_template = self.config['upload'].get('title_template', '{filename}')
        description_template = self.config['upload'].get('description_template', '{filename}')
        
        title = title_template.format(
            filename=title,
            timestamp=datetime.now().isoformat()
        )
        
        description = description_template.format(
            filename=title,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # カテゴリーID（22 = Music）
        category_id = self.config['upload'].get('default_category', '22')
        
        # プライバシー設定
        privacy_status = self.config['upload'].get('default_privacy_status', 'private')
        
        # 言語
        language = self.config['upload'].get('default_language', 'ja')
        
        metadata = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': ['audio', 'music', 'uploaded'],
                'categoryId': category_id,
                'defaultLanguage': language,
                'localized': {
                    'title': title,
                    'description': description
                }
            },
            'status': {
                'privacyStatus': privacy_status,
                'madeForKids': False
            }
        }
        
        logger.info(f"メタデータ: {title[:50]}...")
        logger.info(f"プライバシー設定: {privacy_status}")
        
        return metadata
    
    def upload_video(self, video_path: str) -> dict:
        """
        動画ファイルをYouTubeにアップロード
        
        Args:
            video_path: 動画ファイルのパス
            
        Returns:
            アップロード結果を含む辞書
        """
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"ビデオファイルが見つかりません: {video_path}")
            
            # ファイルサイズを確認
            file_size = os.path.getsize(video_path)
            file_size_mb = file_size / (1024 * 1024)
            logger.info(f"アップロード開始: {Path(video_path).name} ({file_size_mb:.2f} MB)")
            
            # メタデータを取得
            body = self._get_video_metadata(Path(video_path).name)
            
            # ファイルをアップロード
            media_body = MediaFileUpload(
                video_path,
                mimetype='video/mp4',
                chunksize=self.RESUMABLE_UPLOAD_CHUNK_SIZE,
                resumable=True
            )
            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media_body
            )

            # アップロード実行
            response = None
            while response is None:
                try:
                    status, response = request.next_chunk()
                    if status:
                        percent_complete = int(status.progress() * 100)
                        logger.info(f"アップロード進捗: {percent_complete}%")
                except HttpError as e:
                    if e.resp.status in [400, 403]:
                        logger.error(f"アップロードエラー: {e}")
                        return {'status': 'error', 'video_id': None, 'error': str(e)}
                    else:
                        raise e
            
            # 成功時
            video_id = response.get('id')
            logger.info(f"アップロード成功: {video_id}")
            logger.info(f"URL: https://youtu.be/{video_id}")
            
            return {
                'status': 'success',
                'video_id': video_id,
                'url': f'https://youtu.be/{video_id}'
            }
            
        except Exception as e:
            logger.error(f"アップロード失敗: {str(e)}")
            return {
                'status': 'error',
                'video_id': None,
                'error': str(e)
            }
    
    def process_all_videos(self, skip_uploaded: bool = True) -> dict:
        """
        outputディレクトリ内のすべての動画ファイルをアップロード
        
        Args:
            skip_uploaded: アップロード済みファイルをスキップするか
            
        Returns:
            処理結果を含む辞書
        """
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'videos': []
        }
        
        if not os.path.exists(self.video_output_dir):
            logger.error(f"出力ディレクトリが見つかりません: {self.video_output_dir}")
            return results
        
        # mp4ファイルを検索
        video_files = sorted(Path(self.video_output_dir).glob('*.mp4'))
        
        if not video_files:
            logger.warning("アップロード対象の動画ファイルが見つかりません")
            return results
        
        logger.info(f"アップロード対象の動画ファイル: {len(video_files)}個")
        
        for video_file in video_files:
            results['total'] += 1
            logger.info(f"処理中: {video_file.name} ({results['total']}/{len(video_files)})")
            
            result = self.upload_video(str(video_file))
            
            if result['status'] == 'success':
                results['success'] += 1
                results['videos'].append({
                    'file': video_file.name,
                    'status': 'success',
                    'video_id': result['video_id'],
                    'url': result['url']
                })
            else:
                results['failed'] += 1
                results['videos'].append({
                    'file': video_file.name,
                    'status': 'error',
                    'error': result.get('error')
                })
        
        # 結果をログ
        logger.info("=" * 50)
        logger.info("アップロード完了")
        logger.info(f"総ファイル数: {results['total']}")
        logger.info(f"成功: {results['success']}")
        logger.info(f"失敗: {results['failed']}")
        logger.info("=" * 50)
        
        return results


def main():
    """メイン処理"""
    try:
        uploader = YouTubeUploader()
        results = uploader.process_all_videos()
        
        # 成功/失敗の別なく、結果を表示
        for video in results['videos']:
            if video['status'] == 'success':
                print(f"✓ {video['file']}: {video['url']}")
            else:
                print(f"✗ {video['file']}: {video['error']}")
        
        # 終了コード
        sys.exit(0 if results['failed'] == 0 else 1)
        
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
