#!/usr/bin/env python3
"""
音声ファイルを動画ファイルに変換するスクリプト
静止画（ロゴ）と共に音声を組み合わせて動画を生成
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
import logging

import subprocess
from pydub import AudioSegment

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/conversion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ログディレクトリ作成
os.makedirs('logs', exist_ok=True)


class AudioToVideoConverter:
    """音声ファイルを動画に変換するクラス"""
    
    SUPPORTED_AUDIO_FORMATS = ['.wav', '.mp3', '.flac', '.m4a', '.aac']
    
    def __init__(self, config_path: str = './config/config.json'):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config = self._load_config(config_path)
        self.audio_input_dir = self.config['paths']['audio_input']
        self.video_output_dir = self.config['paths']['video_output']
        self.logo_path = self.config['image']['logo_path']
        
        # ディレクトリ作成
        os.makedirs(self.audio_input_dir, exist_ok=True)
        os.makedirs(self.video_output_dir, exist_ok=True)
        
        logger.info(f"入力ディレクトリ: {self.audio_input_dir}")
        logger.info(f"出力ディレクトリ: {self.video_output_dir}")
    
    def _load_config(self, config_path: str) -> dict:
        """設定ファイルを読み込む"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _normalize_audio(self, audio_path: str, output_path: str) -> None:
        """
        音声を正規化（音量調整）
        
        Args:
            audio_path: 入力音声ファイルのパス
            output_path: 出力音声ファイルのパス
        """
        logger.info(f"音声を正規化中: {audio_path}")
        audio = AudioSegment.from_file(audio_path)
        
        # 目標音量レベル（dBFS）
        target_dbfs = -20.0
        loudness = audio.dBFS
        gain = target_dbfs - loudness
        
        # 音量調整
        if gain != 0:
            audio = audio.apply_gain(gain)
        
        # 高品質で出力
        audio.export(
            output_path,
            format='wav',
            bitrate=f"{self.config['video']['audio_bitrate']}",
            parameters=["-q:a", "9"]
        )
        logger.info(f"正規化完了: {output_path}")
    
    def _prepare_image(self, image_path: str) -> str:
        """
        画像ファイルが存在することを確認するだけ
        """
        logger.info(f"画像を準備中: {image_path}")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"画像ファイルが見つかりません: {image_path}")

        return image_path

    def _normalize_audio(self, audio_path: str, output_path: str) -> None:
        """
        音声を正規化（音量調整）して一時WAVファイルに保存
        """
        logger.info(f"音声を正規化中: {audio_path}")
        audio = AudioSegment.from_file(audio_path)

        target_dbfs = -20.0
        loudness = audio.dBFS
        gain = target_dbfs - loudness

        if gain != 0:
            audio = audio.apply_gain(gain)

        audio = audio.set_frame_rate(self.config['video']['audio_sample_rate'])
        audio = audio.set_channels(2)
        audio.export(
            output_path,
            format='wav',
            bitrate=f"{self.config['video']['audio_bitrate']}"
        )
        logger.info(f"正規化完了: {output_path}")
    
    def _get_video_dimensions(self) -> tuple:
        """動画の解像度を取得"""
        resolution = self.config['video']['resolution']
        if resolution == '720p':
            return (1280, 720)
        elif resolution == '1080p':
            return (1920, 1080)
        elif resolution == '4K':
            return (3840, 2160)
        else:
            return (1280, 720)  # デフォルト
    
    def convert_audio_to_video(self, audio_path: str) -> bool:
        """
        音声ファイルを動画に変換
        
        Args:
            audio_path: 音声ファイルのパス
            
        Returns:
            成功したかどうか
        """
        try:
            audio_filename = Path(audio_path).stem
            output_filename = f"{audio_filename}.mp4"
            output_path = os.path.join(self.video_output_dir, output_filename)
            temp_audio_path = os.path.join(self.video_output_dir, f"{audio_filename}_normalized.wav")

            logger.info(f"変換開始: {audio_path} → {output_path}")

            width, height = self._get_video_dimensions()
            fps = self.config['video']['fps']
            audio_bitrate = self.config['video']['audio_bitrate']
            video_bitrate = self.config['video']['video_bitrate']
            sample_rate = self.config['video']['audio_sample_rate']

            self._prepare_image(self.logo_path)
            self._normalize_audio(audio_path, temp_audio_path)

            logger.info(f"FFmpegで動画を生成中: {output_path}")
            ffmpeg_command = [
                'ffmpeg',
                '-y',
                '-loop', '1',
                '-i', self.logo_path,
                '-i', temp_audio_path,
                '-c:v', 'libx264',
                '-tune', 'stillimage',
                '-pix_fmt', 'yuv420p',
                '-r', str(fps),
                '-b:v', video_bitrate,
                '-c:a', 'aac',
                '-b:a', audio_bitrate,
                '-ar', str(sample_rate),
                '-shortest',
                '-movflags', '+faststart',
                '-vf', f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
                output_path
            ]

            subprocess.run(ffmpeg_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

            logger.info(f"変換成功: {output_path}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpegエラー: {audio_path} の変換に失敗しました")
            logger.error(e.stderr.decode('utf-8', errors='ignore'))
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            return False

        except Exception as e:
            logger.error(f"エラー: {audio_path} の変換に失敗しました")
            logger.error(f"詳細: {str(e)}")
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            return False
    
    def process_all_audio_files(self) -> dict:
        """
        audioディレクトリ内のすべての音声ファイルを処理
        
        Returns:
            処理結果を含む辞書
        """
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'files': []
        }
        
        if not os.path.exists(self.audio_input_dir):
            logger.error(f"入力ディレクトリが見つかりません: {self.audio_input_dir}")
            return results
        
        # サポートされているファイル形式を検索
        audio_files = []
        for ext in self.SUPPORTED_AUDIO_FORMATS:
            audio_files.extend(
                Path(self.audio_input_dir).glob(f'*{ext}')
            )
            # 大文字もサポート
            audio_files.extend(
                Path(self.audio_input_dir).glob(f'*{ext.upper()}')
            )
        
        audio_files = sorted(set(str(f) for f in audio_files))
        
        if not audio_files:
            logger.warning("処理する音声ファイルが見つかりません")
            return results
        
        logger.info(f"処理対象の音声ファイル: {len(audio_files)}個")
        
        for audio_file in audio_files:
            results['total'] += 1
            logger.info(f"処理中: {Path(audio_file).name} ({results['total']}/{len(audio_files)})")
            
            if self.convert_audio_to_video(audio_file):
                results['success'] += 1
                results['files'].append({
                    'input': audio_file,
                    'status': 'success'
                })
            else:
                results['failed'] += 1
                results['files'].append({
                    'input': audio_file,
                    'status': 'failed'
                })
        
        # 結果をログ
        logger.info("=" * 50)
        logger.info("変換完了")
        logger.info(f"総ファイル数: {results['total']}")
        logger.info(f"成功: {results['success']}")
        logger.info(f"失敗: {results['failed']}")
        logger.info("=" * 50)
        
        return results


def main():
    """メイン処理"""
    try:
        converter = AudioToVideoConverter()
        results = converter.process_all_audio_files()
        
        # 終了コード
        sys.exit(0 if results['failed'] == 0 else 1)
        
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
