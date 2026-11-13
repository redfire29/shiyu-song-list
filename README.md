# [しゆ。Song List](https://redfire29.github.io/shiyu-song-list/)

本專案收錄 VTuber「しゆ (Shiyu)」歌回曲目清單與相關工具。

---

## 🛠️ YouTube 歌回時間戳爬蟲工具 (`yt_playlist_scrapper.py`)

用來自動擷取 YouTube 歌回影片的章節、說明欄或留言中的時間軸，並輸出成 CSV 歌曲清單。

### 互動式執行方式（推薦：避免網址特殊符號跳脫問題）

終端機中若網址帶有 `?`、`&` 或 `=`，直接作為指令參數容易被 Shell 誤判或需要手動加上雙引號。使用**互動式輸入模式**最為直覺且安全。

#### 執行步驟：

1. **開啟終端機並切換至專案根目錄**：
   ```bash
   cd /Users/louis/github/shiyu-song-list-v2/shiyu-song-list
   ```

2. **執行爬蟲腳本**（不帶任何參數）：
   ```bash
   .venv/bin/python yt_playlist_scrapper.py
   ```
   > 💡 也可以先啟用虛擬環境再執行：
   > ```bash
   > source .venv/bin/activate
   > python yt_playlist_scrapper.py
   > ```

3. **貼上 YouTube 網址**：
   終端機會出現提示：
   ```text
   網址: 
   ```
   直接貼上 YouTube 影片連結（例如：`https://www.youtube.com/watch?v=xxxxxxxxxxx`），然後按下 **Enter**。

4. **確認輸出結果**：
   爬取成功後，會在專案根目錄自動產出 CSV 檔案：
   ```text
   --- 檔案已存: [YYYYMMDD]_影片標題_影片ID.csv ---
   ```
   檔案內容包含：
   - `date`：台灣時區日期（YYYY-MM-DD）
   - `title`：歌曲名稱
   - `Artist`：演唱者 / 頻道名稱
   - `link`：帶有該首歌曲開始時間點的時間戳 YouTube 連結（如 `...&t=120s`）

---

### ⚠️ 常見情況處理

- **未找到任何時間軸**：
  若該影片的官方章節、說明欄與前 100 則留言皆無人標註時間軸，終端機會顯示提示。此時可改用專案內建的 Whisper 語音轉錄工具進行聽音辨識：
  ```bash
  .venv/bin/python yt_whisper_transcriber.py "YouTube影片網址"
  ```

- **虛擬環境損毀或首次在其他機器部署**：
  若 `.venv` 遺失或缺少套件，請執行環境安裝腳本重建：
  ```bash
  ./setup_whisper.sh
  ```
