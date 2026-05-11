# -*- coding: utf-8 -*-
import yt_dlp
import re
import pandas as pd
import sys
from datetime import datetime, timezone, timedelta

def time_to_seconds(time_str):
    parts = list(map(int, time_str.split(':')))
    if len(parts) == 2: return parts[0] * 60 + parts[1]
    elif len(parts) == 3: return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0

def get_taiwan_date(info):
    # Python 3.9+ 完美支援 timezone 物件
    tw_tz = timezone(timedelta(hours=8))
    ts = info.get('release_timestamp') or info.get('timestamp')
    
    if ts:
        dt_tw = datetime.fromtimestamp(ts, tz=tw_tz)
        print(f"   [時間偵測] 台灣(TW): {dt_tw.strftime('%Y-%m-%d %H:%M')}")
        return dt_tw.strftime('%Y-%m-%d'), dt_tw.strftime('%Y%m%d')
    
    raw_date = info.get('upload_date', '00000000')
    return f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}", raw_date

def scrape_youtube_playlist(url):
    ydl_opts = {
        'getcomments': True,
        'skip_download': True,
        'extract_flat': False,
        'max_comments': 100,
        'quiet': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            video_id = info.get('id')
            formatted_date, file_date = get_taiwan_date(info)
            artist = info.get('uploader', 'Unknown Artist')
            results = []

            # 優先讀取章節
            chapters = info.get('chapters')
            if chapters:
                for chap in chapters:
                    results.append({
                        "date": formatted_date,
                        "title": chap.get('title'),
                        "Artist": artist,
                        "link": f"https://www.youtube.com/watch?v={video_id}&t={int(chap.get('start_time'))}s"
                    })
            
            # 若無章節則掃描說明欄與留言
            if not results:
                regex = r"(\d{1,2}:\d{2}(?::\d{2})?)\s+(.*)"
                desc = info.get('description', '')
                comments = "\n".join([c.get('text', '') for c in info.get('comments', [])])
                matches = re.findall(regex, desc + "\n" + comments)
                for time_str, title in matches:
                    results.append({
                        "date": formatted_date,
                        "title": title.strip(),
                        "Artist": artist,
                        "link": f"https://www.youtube.com/watch?v={video_id}&t={time_to_seconds(time_str)}s"
                    })

            if results:
                df = pd.DataFrame(results).drop_duplicates(subset=['title'])
                clean_name = re.sub(r'[\\/*?:"<>|]', "", info.get('title', ''))[:15]
                filename = f"[{file_date}]_{clean_name}_{video_id}.csv"
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"--- 檔案已存: {filename} ---")
                return True
        except Exception as e:
            print(f"   -> 錯誤: {e}")
    return False

if __name__ == "__main__":
    # 接收參數或手動輸入
    target = sys.argv[1] if len(sys.argv) > 1 else input("網址: ")
    if target.strip():
        scrape_youtube_playlist(target.strip())