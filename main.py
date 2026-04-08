#!/usr/bin/env python3
"""
メイン実行スクリプト
音声ファイルから動画への変換とYouTubeへのアップロードを自動化
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# スクリプトのディレクトリをPythonパスに追加
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from audio_to_video import AudioToVideoConverter
from youtube_uploader import YouTubeUploader

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/main.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ログディレクトリ作成
os.makedirs('logs', exist_ok=True)


class AudioToYouTubePipeline:
    """音声→YouTube自動パイプライン"""
    
    def __init__(self, skip_conversion: bool = False, skip_upload: bool = False):
        """
        初期化
        
        Args:
            skip_conversion: 音声→動画変換をスキップするか
            skip_upload: YouTubeアップロードをスキップするか
        """
        self.skip_conversion = skip_conversion
        self.skip_upload = skip_upload
        self.start_time = datetime.now()
        
        logger.info("=" * 60)
        logger.info("Audio to YouTube Pipeline")
        logger.info("=" * 60)
        logger.info(f"開始時刻: {self.start_time}")
        logger.info(f"変換スキップ: {skip_conversion}")
        logger.info(f"アップロードスキップ: {skip_upload}")
    
    def run(self) -> dict:
        """
        パイプラインを実行
        
        Returns:
            実行結果
        """
        results = {
            'conversion': None,
            'upload': None,
            'total_time': 0
        }
        
        try:
            # ステップ1: 音声→動画変換
            if not self.skip_conversion:
                logger.info("\n【ステップ1】音声ファイルを動画に変換...")
                converter = AudioToVideoConverter()
                results['conversion'] = converter.process_all_audio_files()
                
                logger.info(f"変換結果: {results['conversion']['success']}/{results['conversion']['total']}")
            
            # ステップ2: YouTubeアップロード
            if not self.skip_upload:
                logger.info("\n【ステップ2】動画をYouTubeにアップロード...")
                uploader = YouTubeUploader()
                results['upload'] = uploader.process_all_videos()
                
                logger.info(f"アップロード結果: {results['upload']['success']}/{results['upload']['total']}")
            
            # 実行時間を計算
            end_time = datetime.now()
            elapsed_time = (end_time - self.start_time).total_seconds()
            results['total_time'] = elapsed_time
            
            logger.info("\n" + "=" * 60)
            logger.info("パイプライン実行完了")
            logger.info(f"実行時間: {elapsed_time:.2f}秒")
            logger.info("=" * 60)
            
            return results
            
        except Exception as e:
            logger.error(f"パイプライン実行エラー: {str(e)}")
            logger.error("トレースバック:", exc_info=True)
            return results
    
    def print_summary(self, results: dict) -> None:
        """
        実行結果のサマリーを表示
        
        Args:
            results: 実行結果
        """
        print("\n" + "=" * 60)
        print("【実行サマリー】")
        print("=" * 60)
        
        if results['conversion']:
            print(f"\n▶ 音声→動画変換")
            print(f"  - 処理ファイル: {results['conversion']['total']}")
            print(f"  - 成功: {results['conversion']['success']}")
            print(f"  - 失敗: {results['conversion']['failed']}")
            
            if results['conversion']['failed'] > 0:
                print(f"  ⚠ 失敗ファイル:")
                for file_info in results['conversion']['files']:
                    if file_info['status'] == 'failed':
                        print(f"    - {Path(file_info['input']).name}")
        
        if results['upload']:
            print(f"\n▶ YouTube アップロード")
            print(f"  - 処理ファイル: {results['upload']['total']}")
            print(f"  - 成功: {results['upload']['success']}")
            print(f"  - 失敗: {results['upload']['failed']}")
            
            if results['upload']['success'] > 0:
                print(f"  ✓ アップロード成功:")
                for video_info in results['upload']['videos']:
                    if video_info['status'] == 'success':
                        print(f"    - {video_info['file']}")
                        print(f"      URL: {video_info['url']}")
            
            if results['upload']['failed'] > 0:
                print(f"  ✗ アップロード失敗:")
                for video_info in results['upload']['videos']:
                    if video_info['status'] == 'error':
                        print(f"    - {video_info['file']}: {video_info['error']}")
        
        print(f"\n実行時間: {results['total_time']:.2f}秒")
        print("=" * 60 + "\n")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='音声ファイルをYouTubeにアップロードする自動パイプライン',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 完全自動化（変換+アップロード）
  python3 main.py

  # 変換のみ
  python3 main.py --skip-upload

  # アップロードのみ
  python3 main.py --skip-conversion

  # 詳細ログで実行
  python3 main.py --verbose
        """
    )
    
    parser.add_argument(
        '--skip-conversion',
        action='store_true',
        help='音声→動画変換をスキップ'
    )
    
    parser.add_argument(
        '--skip-upload',
        action='store_true',
        help='YouTubeアップロードをスキップ'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='詳細ログを表示'
    )
    
    args = parser.parse_args()
    
    # ロギングレベルを調整
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # パイプラインを実行
    pipeline = AudioToYouTubePipeline(
        skip_conversion=args.skip_conversion,
        skip_upload=args.skip_upload
    )
    
    results = pipeline.run()
    pipeline.print_summary(results)
    
    # 終了コード
    if results['upload'] and results['upload']['failed'] > 0:
        sys.exit(1)
    elif results['conversion'] and results['conversion']['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
