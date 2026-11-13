import Papa from "papaparse";

export interface Song {
  Date: string;
  Title: string;
  Artist: string;
  Link: string;
  isMemberOnly: boolean;
}

export interface DateGroup {
  date: string;
  songs: Song[];
}

export interface DateParts {
  year: string;
  month: string;
  day: string;
}

export interface VideoInfo {
  id: string | null;
  time: number;
}

export const SHEET_CSV_URL =
  "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPNWnxfDY4g6QEACTULQzC1HHv8kmvUDvOX2lLHFQ9Zqo6_7QEkJe0hWc7WNUWZmBbVFASKM_L0iB2/pub?gid=1069936388&single=true&output=csv";

export const GAS_URL =
  "https://script.google.com/macros/s/AKfycbx-jr8pDu7g3OfM1u0_S-MLp_BslRl54Y0nruB8MMgdrsFFLZ2waqiLsEUGEFJSb6aw/exec";

const FAVORITES_STORAGE_KEY = "shiyu_favorites";

/**
 * 解析 yyyy/mm/dd 或 yyyy-mm-dd 日期字串。
 */
export function parseDateParts(dateStr: string): DateParts | null {
  if (!dateStr) return null;
  const parts = dateStr.trim().replace(/\//g, "-").split("-");
  if (parts.length < 3) return null;
  const [year, month, day] = parts;
  if (!year || !month || !day) return null;
  return { year, month, day };
}

/**
 * 將日期字串轉為毫秒時間戳，無效日期回傳 0（避免排序出現 NaN）。
 */
export function getDateTimestamp(dateStr: string): number {
  if (!dateStr) return 0;
  const timestamp = new Date(dateStr.trim().replace(/\//g, "-")).getTime();
  return Number.isNaN(timestamp) ? 0 : timestamp;
}

/**
 * 將會員 API 回傳的 ISO 時間格式轉為 yyyy/mm/dd。
 */
function formatMemberDate(rawDate: string): string {
  if (rawDate && rawDate.includes("T")) {
    const parsed = new Date(rawDate);
    if (!Number.isNaN(parsed.getTime())) {
      const yyyy = parsed.getFullYear();
      const mm = String(parsed.getMonth() + 1).padStart(2, "0");
      const dd = String(parsed.getDate()).padStart(2, "0");
      return `${yyyy}/${mm}/${dd}`;
    }
  }
  return rawDate ?? "";
}

/**
 * 從 YouTube 連結中解析影片 ID 與起始時間（秒）。
 */
export function extractVideoId(url: string): VideoInfo {
  if (!url) return { id: null, time: 0 };

  const regExp =
    /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
  const match = url.match(regExp);
  const id = match && match[2].length === 11 ? match[2] : null;

  let time = 0;
  try {
    const urlObj = new URL(url.trim().replace(/&amp;/g, "&"));
    const t = urlObj.searchParams.get("t");
    if (t) {
      const hmsMatch = t.match(/(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?/);
      if (hmsMatch && (hmsMatch[1] || hmsMatch[2] || hmsMatch[3])) {
        time =
          (parseInt(hmsMatch[1], 10) || 0) * 3600 +
          (parseInt(hmsMatch[2], 10) || 0) * 60 +
          (parseInt(hmsMatch[3], 10) || 0);
      } else {
        time = parseInt(t, 10) || 0;
      }
    }
  } catch {
    // 若網址格式不合法則退回預設起始秒數 0
  }

  return { id, time };
}

/**
 * 從 Google Sheets CSV（及選填的會員 GAS API）抓取歌單資料。
 */
export async function fetchAllSongs(
  pwd?: string | null,
): Promise<{ songs: Song[]; isMemberUnlocked: boolean }> {
  const response = await fetch(`${SHEET_CSV_URL}&t=${Date.now()}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const csvData = await response.text();
  const parsed = Papa.parse<Record<string, string>>(csvData, {
    header: true,
    skipEmptyLines: true,
  });

  let songs: Song[] = parsed.data
    .filter((row) => row.Title || row.Link)
    .map((row) => ({
      Date: (row.Date ?? "").trim(),
      Title: (row.Title ?? "").trim(),
      Artist: (row.Artist ?? "").trim(),
      Link: (row.Link ?? "").trim(),
      isMemberOnly: false,
    }));

  let isMemberUnlocked = false;

  if (pwd) {
    try {
      const gasResponse = await fetch(
        `${GAS_URL}?pwd=${encodeURIComponent(pwd)}`,
      );
      if (gasResponse.ok) {
        const gasText = await gasResponse.text();
        if (
          !gasText.includes("Access Denied") &&
          gasText.trim().startsWith("[")
        ) {
          const memberData = JSON.parse(gasText) as Array<
            Record<string, string>
          >;
          const memberSongs: Song[] = memberData.map((row) => ({
            Date: formatMemberDate(row.Date ?? ""),
            Title: (row.Title ?? "").trim(),
            Artist: (row.Artist ?? "").trim(),
            Link: (row.Link ?? "").trim(),
            isMemberOnly: true,
          }));
          songs = [...songs, ...memberSongs];
          isMemberUnlocked = true;
        }
      }
    } catch (err) {
      console.error("メンバー限定リストの読み込みに失敗しました:", err);
    }
  }

  return { songs, isMemberUnlocked };
}

/**
 * 依日期將已排序的歌曲清單進行 O(N) 分組。
 */
export function groupSongsByDate(songs: Song[]): DateGroup[] {
  const groups: DateGroup[] = [];
  for (const song of songs) {
    const lastGroup = groups[groups.length - 1];
    if (!lastGroup || lastGroup.date !== song.Date) {
      groups.push({ date: song.Date, songs: [song] });
    } else {
      lastGroup.songs.push(song);
    }
  }
  return groups;
}

/**
 * 從 localStorage 讀取收藏連結清單。
 */
export function loadFavorites(): string[] {
  try {
    const saved = localStorage.getItem(FAVORITES_STORAGE_KEY);
    if (!saved) return [];
    const parsed = JSON.parse(saved);
    return Array.isArray(parsed)
      ? parsed.filter((item): item is string => typeof item === "string")
      : [];
  } catch {
    return [];
  }
}

/**
 * 將收藏連結清單寫入 localStorage。
 */
export function saveFavorites(links: string[]): void {
  try {
    localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(links));
  } catch (err) {
    console.error("お気に入りの保存に失敗しました:", err);
  }
}

