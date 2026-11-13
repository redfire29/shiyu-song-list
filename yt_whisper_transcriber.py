# -*- coding: utf-8 -*-
"""
YouTube 歌回時間戳轉錄程式 (yt_whisper_transcriber.py)
功能：下載 YouTube 音訊，使用 OpenAI Whisper 進行高精度時間戳逐字稿轉錄，自動防幻覺並在完成後釋放資源與清理暫存。
"""

import os
import sys
import gc
import re
import json
import shutil
import argparse
import warnings

# 過濾 macOS LibreSSL 相關非關鍵警告
warnings.filterwarnings("ignore")

from datetime import datetime, timezone, timedelta
from pathlib import Path

# 確保系統 PATH 包含常見的 ffmpeg 安裝路徑
for path_cand in ["/usr/local/bin", "/opt/homebrew/bin"]:
    if path_cand not in os.environ.get("PATH", "") and os.path.exists(path_cand):
        os.environ["PATH"] = f"{path_cand}:{os.environ.get('PATH', '')}"

import yt_dlp
import torch
import whisper


def format_seconds(seconds: float) -> str:
    """將秒數轉換為 HH:MM:SS 格式"""
    total_sec = int(seconds)
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_taiwan_date(info: dict) -> tuple[str, str]:
    """取得台灣時間 (UTC+8) 的格式化日期字串"""
    tw_tz = timezone(timedelta(hours=8))
    ts = info.get("release_timestamp") or info.get("timestamp")

    if ts:
        dt_tw = datetime.fromtimestamp(ts, tz=tw_tz)
        return dt_tw.strftime("%Y/%m/%d"), dt_tw.strftime("%Y%m%d")

    raw_date = info.get("upload_date", "00000000")
    if len(raw_date) == 8:
        return f"{raw_date[:4]}/{raw_date[4:6]}/{raw_date[6:]}", raw_date
    return "Unknown_Date", "00000000"


def cleanup_temp_dir(temp_dir: Path):
    """清理臨時音訊目錄中的孤兒殘留檔案"""
    if temp_dir.exists():
        for f in temp_dir.glob("*"):
            if f.is_file():
                try:
                    f.unlink()
                except Exception:
                    pass


def download_audio(url: str, temp_dir: Path) -> tuple[Path, dict]:
    """使用 yt-dlp 下載音訊串流並回傳本地音檔路徑與影片資訊"""
    temp_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(temp_dir / "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "ba/ba*",
        "outtmpl": out_template,
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "mweb"]
            }
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
            }
        ],
    }

    print(f"-> 正在擷取影片資訊與音訊串流: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info.get("id")
        
        # 尋找由 FFmpeg 轉檔後的 m4a 檔案，或原始下載檔案
        audio_path = temp_dir / f"{video_id}.m4a"
        if not audio_path.exists():
            matched = list(temp_dir.glob(f"{video_id}.*"))
            if matched:
                audio_path = matched[0]
            else:
                raise FileNotFoundError(f"找不到下載的音訊檔案 (video_id: {video_id})，目錄內容: {[f.name for f in temp_dir.glob('*')]}")

        duration = info.get("duration", 0)
        print(f"   [影片標題] {info.get('title')}")
        print(f"   [影片時長] {format_seconds(duration)} ({duration} 秒)")
        return audio_path, info


def transcribe_audio(
    audio_path: Path,
    model_name: str = "small",
    language: str = "ja",
    device: str = "mps",
) -> dict:
    """使用 Whisper 執行語音轉錄（啟用抗幻覺與防漂移設定）"""
    print(f"-> 載入 Whisper 模型: '{model_name}' (運算裝置: {device})")
    model = whisper.load_model(model_name, device=device)

    print(f"-> 開始語音轉錄 (語言: {language})... 請稍候")
    # 抗幻覺參數配置：
    # 1. temperature=0.0: 最嚴格的貪婪取樣，避免發散
    # 2. condition_on_previous_text=False: 隔斷前後文依賴，避免伴奏間奏陷入重複疊字迴圈
    # 3. fp16=(device != "cpu"): CPU 執行時自動使用 FP32 避免警告
    result = model.transcribe(
        str(audio_path),
        language=language,
        temperature=0.0,
        condition_on_previous_text=False,
        fp16=(device != "cpu"),
        verbose=False,
    )
    return result


def save_transcripts(
    result: dict,
    info: dict,
    output_dir: Path,
    model_name: str,
    language: str,
) -> tuple[Path, Path]:
    """將轉錄結果分別存為精簡時間戳 .txt 與完整 .json"""
    output_dir.mkdir(parents=True, exist_ok=True)
    video_id = info.get("id")
    title = info.get("title", "Unknown_Title")
    formatted_date, file_date = get_taiwan_date(info)

    clean_title = re.sub(r'[\\/*?:"<>|]', "", title)[:25].strip()
    base_name = f"[{file_date}]_{clean_title}_{video_id}"

    txt_path = output_dir / f"{base_name}.txt"
    json_path = output_dir / f"{base_name}.json"

    segments = result.get("segments", [])

    # 1. 寫入精簡時間戳文字檔 (.txt)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"直播標題: {title}\n")
        f.write(f"直播日期: {formatted_date}\n")
        f.write(f"影片網址: https://www.youtube.com/watch?v={video_id}\n")
        f.write(f"轉錄模型: {model_name} (語言: {language})\n")
        f.write("=" * 60 + "\n\n")

        for seg in segments:
            start_str = format_seconds(seg.get("start", 0))
            end_str = format_seconds(seg.get("end", 0))
            text = seg.get("text", "").strip()
            if text:
                f.write(f"[{start_str} -> {end_str}] {text}\n")

    # 2. 寫入完整資料檔 (.json)
    json_data = {
        "video_id": video_id,
        "title": title,
        "date": formatted_date,
        "file_date": file_date,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "duration": info.get("duration", 0),
        "model": model_name,
        "language": language,
        "segments": [
            {
                "id": seg.get("id"),
                "start": round(seg.get("start", 0), 2),
                "end": round(seg.get("end", 0), 2),
                "start_time": format_seconds(seg.get("start", 0)),
                "end_time": format_seconds(seg.get("end", 0)),
                "text": seg.get("text", "").strip(),
            }
            for seg in segments
        ],
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    return txt_path, json_path


def main():
    parser = argparse.ArgumentParser(description="YouTube 歌回時間戳轉錄工具")
    parser.add_argument("url", nargs="?", help="YouTube 影片或直播網址")
    parser.add_argument("--model", default="small", choices=["tiny", "base", "small", "medium", "large-v3"], help="Whisper 模型等級 (預設: small)")
    parser.add_argument("--language", default="ja", help="預設辨識語言 (預設: ja，可選 zh, en 等)")
    parser.add_argument("--device", default=None, help="運算裝置 (預設自動檢測: mps / cpu)")
    parser.add_argument("--output-dir", default="transcripts", help="逐字稿輸出資料夾 (預設: transcripts)")
    parser.add_argument("--keep-audio", action="store_true", help="是否保留下載的音訊檔 (預設: 自動清理)")

    args = parser.parse_args()

    # 若未傳入網址，則互動式要求輸入
    target_url = args.url
    if not target_url:
        target_url = input("請輸入 YouTube 影片網址: ").strip()

    # 自動清理終端機貼上時產生的反斜線轉義字元 (如 watch\?v\= -> watch?v=)
    if target_url:
        target_url = target_url.replace(r"\?", "?").replace(r"\=", "=").replace(r"\&", "&").replace("\\", "").strip()

    if not target_url:
        print("❌ 錯誤: 網址不能為空！")
        sys.exit(1)

    # 決定運算裝置
    # 註：PyTorch 的 MPS 後端目前缺少稀疏張量 (SparseMPS) 運算子，會導致 Whisper 報錯
    # Apple M2 CPU 實測 RTF 達 0.10（30秒音訊僅需3秒），穩定性與速度極佳，預設採用 cpu
    if args.device:
        device = args.device
    elif torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"

    temp_dir = Path(".temp_audio")
    output_dir = Path(args.output_dir)

    # 啟動時先清理歷史殘留暫存檔
    cleanup_temp_dir(temp_dir)

    audio_path = None
    try:
        # 1. 下載音訊
        audio_path, info = download_audio(target_url, temp_dir)

        # 2. 執行轉錄
        result = transcribe_audio(
            audio_path=audio_path,
            model_name=args.model,
            language=args.language,
            device=device,
        )

        # 3. 儲存結果
        txt_path, json_path = save_transcripts(
            result=result,
            info=info,
            output_dir=output_dir,
            model_name=args.model,
            language=args.language,
        )

        print("\n" + "=" * 60)
        print("🎉 轉錄完成！產出檔案如下：")
        print(f"   [精簡時間戳文字檔] {txt_path}")
        print(f"   [完整資料 JSON 檔] {json_path}")
        print("=" * 60)
        print("\n💡 下一步：")
        print("   直接將上述 .txt 檔案的內容複製貼給我（或直接在對話中告知檔名），")
        print("   我將立即為您辨識歌名與原唱，並產出可直接貼入 songs.csv 的標準格式！\n")

    except Exception as e:
        print(f"\n❌ 轉錄過程中發生錯誤: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        # 強制清理暫存音訊檔
        if not args.keep_audio and audio_path and audio_path.exists():
            try:
                audio_path.unlink()
                print("✓ 暫存音訊檔已自動清理完畢。")
            except Exception:
                pass

        # 釋放記憶體與 GPU 快取
        gc.collect()
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()


if __name__ == "__main__":
    main()
