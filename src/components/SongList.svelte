<script>
  import { onMount, tick } from "svelte";
  import Papa from "papaparse";

  // 1. 填入你提供的 CSV 連結，並在後面加上時間戳記防止快取
  const SHEET_CSV_URL =
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPNWnxfDY4g6QEACTULQzC1HHv8kmvUDvOX2lLHFQ9Zqo6_7QEkJe0hWc7WNUWZmBbVFASKM_L0iB2/pub?gid=1069936388&single=true&output=csv";

  // 會員限定 API
  const GAS_URL = "https://script.google.com/macros/s/AKfycbx-jr8pDu7g3OfM1u0_S-MLp_BslRl54Y0nruB8MMgdrsFFLZ2waqiLsEUGEFJSb6aw/exec";

  let songs = [];
  let pending = true;
  let searchQuery = "";
  let selectedYear = "";
  let selectedMonth = "";
  let selectedDay = "";
  let selectedVideoId = "";
  let isPlayerVisible = false;
  let isMinimized = false;
  let selectedStartTime = 0;

  // 新增 UI/UX 優化狀態
  let favoriteSongs = [];
  let showOnlyFavorites = false;
  let isMemberUnlocked = false;
  let showOnlyMembers = false;
  let currentPlayingLink = "";
  let currentPlayingSong = null;

  // 動態釘選高度計算
  let headerHeight = 90;
  let headerEl;

  const updateHeaderHeight = () => {
    if (headerEl) {
      headerHeight = headerEl.offsetHeight;
    }
  };

  // 當資料載入完成、實際清單渲染至 DOM 後，自動重新精確測量一次控制面板高度
  $: if (!pending) {
    tick().then(updateHeaderHeight);
  }

  const loadData = async () => {
    pending = true;
    try {
      // 加入隨機參數 t，確保每次抓取都是最新的
      const response = await fetch(`${SHEET_CSV_URL}&t=${Date.now()}`);
      const csvData = await response.text();

      const parsed = Papa.parse(csvData, {
        header: true,
        skipEmptyLines: true,
      });

      // 這裡要確保你的試算表標題是 "Date", "Title", "Artist", "Link"
      let baseSongs = parsed.data.map(s => ({ ...s, isMemberOnly: false }));

      // 檢查網址密碼並載入會員歌單
      if (typeof window !== "undefined") {
        const urlParams = new URLSearchParams(window.location.search);
        const pwd = urlParams.get("pwd");
        if (pwd) {
          try {
            const gasResponse = await fetch(`${GAS_URL}?pwd=${pwd}`);
            const gasText = await gasResponse.text();
            if (!gasText.includes("Access Denied") && gasText.trim().startsWith("[")) {
              const memberData = JSON.parse(gasText);
              const memberSongs = memberData.map(s => {
                let formattedDate = s.Date;
                // 自動處理 Google API 回傳的 ISO 時間格式 (例如 "2024-09-08T16:00:00.000Z")
                if (formattedDate && formattedDate.includes("T")) {
                  const d = new Date(formattedDate);
                  if (!isNaN(d.getTime())) {
                    const yyyy = d.getFullYear();
                    const mm = String(d.getMonth() + 1).padStart(2, '0');
                    const dd = String(d.getDate()).padStart(2, '0');
                    formattedDate = `${yyyy}/${mm}/${dd}`;
                  }
                }
                return { ...s, Date: formattedDate, isMemberOnly: true };
              });
              baseSongs = [...baseSongs, ...memberSongs];
              isMemberUnlocked = true;
            }
          } catch (e) {
            console.error("載入會員歌單失敗:", e);
          }
        }
      }

      songs = baseSongs;
    } catch (err) {
      console.error("資料抓取失敗:", err);
    } finally {
      pending = false;
    }
  };

  onMount(() => {
    loadData();
    const saved = localStorage.getItem("shiyu_favorites");
    if (saved) {
      try {
        favoriteSongs = JSON.parse(saved);
      } catch (e) {
        console.error("載入收藏夾失敗:", e);
      }
    }

    // 動態測量控制區高度，供日期標頭釘選定位使用
    updateHeaderHeight();
    window.addEventListener("resize", updateHeaderHeight);

    const observer = new ResizeObserver(updateHeaderHeight);
    if (headerEl) observer.observe(headerEl);

    // 額外延遲多次測量，雙重防護以防 initial render 時 Tailwind 樣式與 RWD 未解析完成導致高度不對
    setTimeout(updateHeaderHeight, 100);
    setTimeout(updateHeaderHeight, 300);

    return () => {
      window.removeEventListener("resize", updateHeaderHeight);
      observer.disconnect();
    };
  });

  const toggleFavorite = (song) => {
    const link = song.Link;
    if (favoriteSongs.includes(link)) {
      favoriteSongs = favoriteSongs.filter((l) => l !== link);
    } else {
      favoriteSongs = [...favoriteSongs, link];
    }
    localStorage.setItem("shiyu_favorites", JSON.stringify(favoriteSongs));
  };

  const playRandomSong = () => {
    if (filteredSongs.length === 0) return;
    const randomIndex = Math.floor(Math.random() * filteredSongs.length);
    const randomSong = filteredSongs[randomIndex];
    playVideo(randomSong);

    // 隨機選歌後，等 DOM 渲染完平滑滾動至該首歌曲卡片
    setTimeout(() => {
      const activeEl = document.querySelector(".playing-active-card");
      if (activeEl) {
        activeEl.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }, 150);
  };

  // 輔助函式：處理 yyyy/mm/dd 排序
  const getTime = (dateStr) => {
    if (!dateStr) return 0;
    return new Date(dateStr.replace(/\//g, "-")).getTime();
  };

  // 日期提取輔助
  const parseDate = (dateStr) => {
    const parts = dateStr.replace(/\//g, "-").split("-");
    if (parts.length < 3) return null;
    return {
      year: parts[0],
      month: parts[1],
      day: parts[2],
    };
  };

  // 年份下拉選單 (由新到舊)
  $: availableYears = (() => {
    if (!songs.length) return [];
    const years = new Set();
    songs.forEach((s) => {
      const d = parseDate(s.Date);
      if (d) years.add(d.year);
    });
    return [...years].sort((a, b) => Number(b) - Number(a));
  })();

  // 月份下拉選單 (根據選中的年份或是全部)
  $: availableMonths = (() => {
    const months = new Set();
    songs.forEach((s) => {
      const d = parseDate(s.Date);
      if (!d) return;
      if (selectedYear && d.year !== selectedYear) return;
      months.add(d.month);
    });
    return [...months].sort((a, b) => Number(a) - Number(b));
  })();

  // 日期下拉選單 (根據選中的年月)
  $: availableDays = (() => {
    const days = new Set();
    songs.forEach((s) => {
      const d = parseDate(s.Date);
      if (!d) return;
      if (selectedYear && d.year !== selectedYear) return;
      if (selectedMonth && d.month !== selectedMonth) return;
      days.add(d.day);
    });
    return [...days].sort((a, b) => Number(a) - Number(b));
  })();

  // 連動重置：年份改變時，清空月、日 (如果不合法)
  // 注意：這裡簡單處理，只要換年就清空月日，換月清空日，體驗比較直覺
  const handleYearChange = () => {
    selectedMonth = "";
    selectedDay = "";
  };

  const handleMonthChange = () => {
    selectedDay = "";
  };

  // 歌曲列表過濾與排序 (由新到舊)
  $: filteredSongs = (() => {
    let result = [...songs];

    // 最愛過濾
    if (showOnlyFavorites) {
      result = result.filter((s) => favoriteSongs.includes(s.Link));
    }

    if (showOnlyMembers) {
      result = result.filter((s) => s.isMemberOnly);
    }

    if (searchQuery) {
      const q = searchQuery.trim().toLowerCase();
      result = result.filter(
        (s) =>
          (s.Title || "").toLowerCase().includes(q) ||
          (s.Artist || "").toLowerCase().includes(q),
      );
    }

    if (selectedYear) {
      result = result.filter((s) => {
        const d = parseDate(s.Date);
        return d && d.year === selectedYear;
      });
    }

    if (selectedMonth) {
      result = result.filter((s) => {
        const d = parseDate(s.Date);
        return d && d.month === selectedMonth;
      });
    }

    if (selectedDay) {
      result = result.filter((s) => {
        const d = parseDate(s.Date);
        return d && d.day === selectedDay;
      });
    }

    // 確保依照日期由新到舊排序
    return result.sort((a, b) => getTime(b.Date) - getTime(a.Date));
  })();

  // 計算該日期分組內的序號 (01, 02...)
  const getDailyIndex = (currentIndex, list) => {
    const currentSong = list[currentIndex];
    if (!currentSong) return "01";
    let count = 0;
    for (let i = 0; i <= currentIndex; i++) {
      if (list[i].Date === currentSong.Date) {
        count++;
      }
    }
    return String(count).padStart(2, "0");
  };

  const clearFilters = () => {
    searchQuery = "";
    selectedYear = "";
    selectedMonth = "";
    selectedDay = "";
    showOnlyFavorites = false;
    showOnlyMembers = false;
  };

  const extractVideoId = (url) => {
    if (!url) return { id: null, time: 0 };
    const regExp =
      /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    const match = url.match(regExp);
    const id = match && match[2].length === 11 ? match[2] : null;

    // 解析時間參數 t
    let time = 0;
    const urlObj = new URL(url.replace(/&amp;/g, "&"));
    const t = urlObj.searchParams.get("t");
    if (t) {
      // 處理 1h2m3s 格式或是純秒數
      const hmsMatch = t.match(/(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?/);
      if (hmsMatch && (hmsMatch[1] || hmsMatch[2] || hmsMatch[3])) {
        time =
          (parseInt(hmsMatch[1]) || 0) * 3600 +
          (parseInt(hmsMatch[2]) || 0) * 60 +
          (parseInt(hmsMatch[3]) || 0);
      } else {
        time = parseInt(t) || 0;
      }
    }
    return { id, time };
  };

  const playVideo = (song) => {
    const link = song.Link;
    
    // 會員限定影片無法使用 iframe 嵌入，直接另開新視窗
    if (song.isMemberOnly) {
      // 關閉目前網頁上的播放器，避免聲音重疊
      isPlayerVisible = false;
      // 依然設定為目前播放歌曲，讓介面保持高亮與跳動動畫
      currentPlayingLink = link;
      currentPlayingSong = song;
      
      window.open(link, "_blank");
      return;
    }

    const { id, time } = extractVideoId(link);
    currentPlayingLink = link;
    currentPlayingSong = song;

    if (id) {
      // 如果影片 ID 相同但秒數不同，強制更新 iframe
      if (selectedVideoId === id) {
        selectedVideoId = ""; // 觸發 Svelte 重新渲染
        setTimeout(() => {
          selectedVideoId = id;
          selectedStartTime = time;
          isPlayerVisible = true;
          isMinimized = false;
        }, 10);
      } else {
        selectedVideoId = id;
        selectedStartTime = time;
        isPlayerVisible = true;
        isMinimized = false;
      }
    } else if (link) {
      window.open(link, "_blank");
    }
  };
</script>

<!-- 背景稍微調深一點點，讓白色卡片更跳脫出來 -->
<div
  class="min-h-screen bg-blue-50/80 text-slate-900 py-6 px-4 sm:px-6 font-sans"
>
  <div class="max-w-2xl mx-auto">
    <!-- 標題區 (使用深海藍，強化對比) -->
    <div class="text-center mb-8">
      <h1 class="text-4xl font-black text-blue-800 tracking-tighter">
        しゆ。Song List
      </h1>
      <a
        href="https://www.youtube.com/@shiyumarurun"
        target="_blank"
        class="inline-block text-blue-800 hover:text-red-600 transition-colors my-2"
        aria-label="YouTube Channel"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="w-10 h-10"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"
          />
        </svg>
      </a>
    </div>

    <!-- 固定在頂部的控制面板 (Glassmorphism 磨砂玻璃效果) -->
    <div
      bind:this={headerEl}
      class="sticky top-0 z-20 pt-3 pb-4 -mx-4 px-4 bg-white/80 backdrop-blur-md border-b border-blue-100 shadow-md transition-all duration-300"
    >
      <div class="max-w-2xl mx-auto">
        <div class="flex max-md:flex-col flex-wrap gap-3 md:items-end">
          <!-- 検索 (文字顏色加深) -->
          <div class="flex-1 max-md:w-full min-w-[180px]">
            <label
              for="search"
              class="block text-[11px] font-black text-blue-800 uppercase mb-1 ml-1 tracking-widest"
              >Search / 検索</label
            >
            <input
              id="search"
              bind:value={searchQuery}
              type="text"
              placeholder="曲名、アーティスト名..."
              class="w-full rounded-lg border-2 border-blue-100 p-2 text-sm focus:border-blue-600 outline-none bg-white/50 text-slate-900 placeholder:text-blue-400 transition-all font-medium"
            />
          </div>

          <div class="flex flex-1 w-full sm:w-auto gap-2">
            <!-- 年份 Filters -->
            <div class="flex-1 sm:w-24 relative">
              <label
                for="year-filter"
                class="block text-[11px] font-black text-blue-800 uppercase mb-1 ml-1 tracking-widest"
                >Year / 年</label
              >
              <div class="relative">
                <select
                  id="year-filter"
                  bind:value={selectedYear}
                  on:change={handleYearChange}
                  class="w-full rounded-lg border-2 border-blue-100 p-2 pr-8 text-sm outline-none focus:border-blue-600 bg-white/50 text-slate-900 font-bold cursor-pointer appearance-none transition-colors"
                >
                  <option value="">Year</option>
                  {#each availableYears as year}
                    <option value={year}>{year}</option>
                  {/each}
                </select>
                <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2.5 text-blue-600">
                  <svg class="h-4 w-4 fill-current" viewBox="0 0 20 20"><path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"/></svg>
                </div>
              </div>
            </div>

            <!-- 月份 Filters -->
            <div class="flex-1 sm:w-20 relative">
              <label
                for="month-filter"
                class="block text-[11px] font-black text-blue-800 uppercase mb-1 ml-1 tracking-widest"
                >Month / 月</label
              >
              <div class="relative">
                <select
                  id="month-filter"
                  bind:value={selectedMonth}
                  on:change={handleMonthChange}
                  class="w-full rounded-lg border-2 border-blue-100 p-2 pr-8 text-sm outline-none focus:border-blue-600 bg-white/50 text-slate-900 font-bold cursor-pointer appearance-none transition-colors"
                >
                  <option value="">Month</option>
                  {#each availableMonths as month}
                    <option value={month}>{month}</option>
                  {/each}
                </select>
                <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2.5 text-blue-600">
                  <svg class="h-4 w-4 fill-current" viewBox="0 0 20 20"><path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"/></svg>
                </div>
              </div>
            </div>

            <!-- 日期 Filters -->
            <div class="flex-1 sm:w-20 relative">
              <label
                for="day-filter"
                class="block text-[11px] font-black text-blue-800 uppercase mb-1 ml-1 tracking-widest"
                >Day / 日</label
              >
              <div class="relative">
                <select
                  id="day-filter"
                  bind:value={selectedDay}
                  class="w-full rounded-lg border-2 border-blue-100 p-2 pr-8 text-sm outline-none focus:border-blue-600 bg-white/50 text-slate-900 font-bold cursor-pointer appearance-none transition-colors"
                >
                  <option value="">Day</option>
                  {#each availableDays as day}
                    <option value={day}>{day}</option>
                  {/each}
                </select>
                <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2.5 text-blue-600">
                  <svg class="h-4 w-4 fill-current" viewBox="0 0 20 20"><path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"/></svg>
                </div>
              </div>
            </div>
          </div>

          <!-- 按鈕區組群 (重新設計：融入藍白色系，建立優雅的視覺主次層次) -->
          <div class="flex flex-wrap items-center gap-2 max-md:w-full md:mt-0">
            <!-- 🎲 隨機選歌 -->
            <button
              on:click={playRandomSong}
              class="flex-1 md:flex-none px-4 py-2.5 bg-white/50 border-2 border-blue-100 hover:border-blue-400 hover:bg-blue-50/20 text-blue-800 text-xs font-black rounded-lg transition-all active:scale-95 flex items-center justify-center gap-1.5 uppercase tracking-widest cursor-pointer"
              title="ランダムで1曲再生"
            >
              ランダム
            </button>

            <!-- ❤️ 僅看收藏 -->
            <button
              on:click={() => showOnlyFavorites = !showOnlyFavorites}
              class="flex-1 md:flex-none px-4 py-2.5 border-2 transition-all active:scale-95 flex items-center justify-center gap-1.5 text-xs font-black rounded-lg cursor-pointer {showOnlyFavorites ? 'border-red-200 bg-red-50/80 text-red-600 hover:bg-red-100/50' : 'border-blue-100 bg-white/50 text-blue-800 hover:bg-blue-50/20 hover:border-blue-400'}"
            >
              <span>{showOnlyFavorites ? 'すべて表示' : 'お気に入り'}</span>
            </button>

            <!-- 👑 會員專屬 -->
            {#if isMemberUnlocked}
              <button
                on:click={() => showOnlyMembers = !showOnlyMembers}
                class="flex-1 md:flex-none px-4 py-2.5 border-2 transition-all active:scale-95 flex items-center justify-center gap-1.5 text-xs font-black rounded-lg cursor-pointer {showOnlyMembers ? 'border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100' : 'border-blue-100 bg-white/50 text-blue-800 hover:bg-blue-50/20 hover:border-blue-400'}"
              >
                <span>{showOnlyMembers ? 'すべて表示' : '👑 メンバー'}</span>
              </button>
            {/if}

            <!-- リセット -->
            <button
              on:click={clearFilters}
              class="flex-1 md:flex-none px-4 py-2.5 bg-blue-700 hover:bg-blue-800 text-white text-xs font-black rounded-lg transition-all shadow-md active:scale-95 uppercase tracking-widest cursor-pointer"
            >
              リセット
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 読み込み状態 (骨架屏載入動畫) -->
    {#if pending}
      <div class="space-y-3 mt-8">
        {#each Array(6) as _, i}
          <div class="flex items-center bg-white/60 border border-blue-50/50 px-4 py-4 rounded-xl shadow-sm animate-pulse">
            <!-- 序號骨架 -->
            <div class="w-8 h-4 bg-slate-200 rounded"></div>
            <!-- 標題與歌手骨架 -->
            <div class="flex-1 ml-2 space-y-2">
              <div class="w-2/3 h-5 bg-slate-200 rounded"></div>
              <div class="w-1/4 h-3 bg-slate-200 rounded"></div>
            </div>
            <!-- 按鈕骨架 -->
            <div class="flex gap-2 ml-4">
              <div class="w-7 h-7 bg-slate-200 rounded-full"></div>
              <div class="w-7 h-7 bg-slate-200 rounded-full"></div>
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <!-- リスト表示 -->
      <div class="space-y-3 mt-8">
        {#each filteredSongs as song, index}
          <!-- 日付ヘッダー (深藍色標籤，極高對比) -->
          {#if index === 0 || song.Date !== filteredSongs[index - 1]?.Date}
            <div
              class="sticky z-10 bg-blue-50/95 py-3 border-b-2 border-blue-100 mb-2"
              style="top: {headerHeight}px;"
            >
              <div class="flex items-center gap-3">
                <div
                  class="bg-blue-800 text-white px-3 py-1 rounded text-xs font-black tracking-widest shadow-md"
                >
                  {song.Date}
                </div>
                <div class="flex-1 h-[2px] bg-blue-200"></div>
              </div>
            </div>
          {/if}

          <!-- 歌曲橫條 (純白底，深色字) -->
          <!-- svelte-ignore a11y-click-events-have-key-events -->
          <!-- svelte-ignore a11y-no-static-element-interactions -->
          <div
            class="group flex items-center px-4 py-4 transition-all duration-300 rounded-xl shadow-sm cursor-pointer {currentPlayingLink === song.Link ? 'playing-active-card bg-blue-50/60 border-2 border-blue-500 shadow-md' : 'bg-white border border-blue-200 hover:border-blue-400 hover:-translate-y-0.5 hover:shadow-md active:scale-[0.995]'}"
            on:click={() => playVideo(song)}
          >
            <!-- 序號與正在播放等化器 (調整為中灰色，正在播放時展現跳動等化器) -->
            <div class="text-xs font-mono text-slate-400 w-8 font-bold flex items-center justify-start">
              {#if currentPlayingLink === song.Link}
                <!-- 正在播放等化器 -->
                <div class="flex items-end gap-[2px] h-[18px] w-4 pr-1">
                  <div class="w-[3px] bg-blue-600 rounded-full eq-bar-1"></div>
                  <div class="w-[3px] bg-blue-600 rounded-full eq-bar-2"></div>
                  <div class="w-[3px] bg-blue-600 rounded-full eq-bar-3"></div>
                </div>
              {:else}
                {getDailyIndex(index, filteredSongs)}
              {/if}
            </div>

            <div class="flex-1 min-w-0 ml-2">
              <div class="flex flex-col">
                <!-- 歌曲標題：深色 Slate-900 -->
                <div class="flex items-center gap-2">
                  <h3
                    class="text-base font-black truncate transition-colors {currentPlayingLink === song.Link ? 'text-blue-800' : 'text-slate-900 group-hover:text-blue-600'}"
                  >
                    {song.Title}
                  </h3>
                  {#if song.isMemberOnly}
                    <span class="px-1.5 py-0.5 bg-amber-100 text-amber-700 border border-amber-300 text-[10px] font-black rounded shadow-sm flex-shrink-0 tracking-widest uppercase">Member</span>
                  {/if}
                </div>
                <!-- 歌手名稱：調深至 Blue-700 -->
                <span
                  class="text-xs font-bold text-blue-700 mt-0.5 truncate uppercase tracking-tight"
                  >{song.Artist}</span
                >
              </div>
            </div>

            <!-- 控制按鈕區：包含收藏與 YouTube 開啟 -->
            <div class="flex items-center gap-1.5 ml-4">
              <!-- ❤️ 收藏按鈕 -->
              <button
                on:click|stopPropagation={() => toggleFavorite(song)}
                class="p-2 transition-all hover:scale-110 cursor-pointer text-slate-400 hover:text-red-500"
                title={favoriteSongs.includes(song.Link) ? "取消收藏" : "加入收藏"}
              >
                {#if favoriteSongs.includes(song.Link)}
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-red-500 fill-current" viewBox="0 0 24 24">
                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                  </svg>
                {:else}
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 fill-none stroke-current" stroke-width="2" viewBox="0 0 24 24">
                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                  </svg>
                {/if}
              </button>

              <!-- YouTube 連結 (新開分頁) -->
              <a
                href={song.Link}
                target="_blank"
                class="p-2 text-blue-500 hover:text-red-600 transition-all hover:scale-110"
                title="YouTubeで再生"
                on:click|stopPropagation
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="w-6 h-6"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"
                  />
                </svg>
              </a>
            </div>
          </div>
        {/each}

        <!-- 該当なし -->
        {#if filteredSongs.length === 0}
          <div
            class="text-center py-20 text-blue-800 text-sm font-black bg-white rounded-2xl border-4 border-dashed border-blue-200 mt-4"
          >
            該当する楽曲が見つかりませんでした
          </div>
        {/if}
      </div>
    {/if}

    <!-- フッター (文字加深) -->
    <div class="mt-16 mb-20 border-t-4 border-blue-200 pt-8 text-center">
      <span
        class="text-blue-800 text-xs font-black tracking-[0.2em] uppercase bg-blue-100 px-4 py-2 rounded-full"
      >
        Total Catalog / 合計 {filteredSongs.length} 曲
      </span>
    </div>
  </div>
</div>

<!-- YouTube 影片浮動小視窗 -->
{#if isPlayerVisible && selectedVideoId}
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div
    class="fixed z-50 transition-all duration-500 ease-out bg-white/95 backdrop-blur-md shadow-[0_20px_50px_rgba(0,0,0,0.15)] border-2 border-blue-100 overflow-hidden max-sm:left-0 max-sm:right-0 max-sm:bottom-0 max-sm:w-full max-sm:rounded-t-2xl max-sm:rounded-b-none max-sm:border-x-0 max-sm:border-b-0 sm:bottom-6 sm:right-6 sm:rounded-2xl sm:w-[500px] {isMinimized ? 'max-sm:h-[50px] sm:w-[320px]' : 'max-sm:h-auto'}"
  >
    <!-- 標題欄 -->
    <div
      class="flex items-center justify-between px-4 py-3 bg-blue-800 text-white cursor-pointer select-none"
      on:click={() => (isMinimized = !isMinimized)}
      on:keydown={(e) => e.key === "Enter" && (isMinimized = !isMinimized)}
    >
      <div class="flex items-center gap-2 overflow-hidden flex-1 min-w-0 mr-3">
        <div class="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse flex-shrink-0"></div>
        <span class="text-xs font-black tracking-wide truncate"
          >{currentPlayingSong ? `${currentPlayingSong.Title} - ${currentPlayingSong.Artist}` : "Now Playing"}</span
        >
      </div>
      <div class="flex items-center gap-3 flex-shrink-0">
        <!-- 最小化/還原按鈕 -->
        <button
          on:click|stopPropagation={() => (isMinimized = !isMinimized)}
          class="text-blue-200 hover:text-white transition-colors cursor-pointer"
          title={isMinimized ? "還原" : "最小化"}
        >
          {#if isMinimized}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="w-4.5 h-4.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2.5"
                d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5"
              />
            </svg>
          {:else}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="w-4.5 h-4.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2.5"
                d="M18 12H6"
              />
            </svg>
          {/if}
        </button>
        <!-- 關閉按鈕 -->
        <button
          on:click|stopPropagation={() => (isPlayerVisible = false)}
          class="text-blue-200 hover:text-red-400 transition-colors cursor-pointer"
          aria-label="Close player"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="w-4.5 h-4.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2.5"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- 影片內容區 (最小化時保持在 DOM 中以持續播放) -->
    <div
      class="aspect-video bg-black shadow-inner {isMinimized ? 'hidden' : 'block'}"
    >
      <iframe
        title="YouTube player"
        class="w-full h-full"
        src={`https://www.youtube.com/embed/${selectedVideoId}?autoplay=1&start=${selectedStartTime}`}
        frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen
      ></iframe>
    </div>
  </div>
{/if}

<style>
  /* 正在播放的等化器跳動動畫 */
  @keyframes equalize-1 {
    0%, 100% { height: 4px; }
    50% { height: 16px; }
  }
  @keyframes equalize-2 {
    0%, 100% { height: 16px; }
    50% { height: 6px; }
  }
  @keyframes equalize-3 {
    0%, 100% { height: 8px; }
    50% { height: 18px; }
  }

  .eq-bar-1 {
    animation: equalize-1 0.8s ease-in-out infinite;
  }
  .eq-bar-2 {
    animation: equalize-2 0.8s ease-in-out infinite 0.15s;
  }
  .eq-bar-3 {
    animation: equalize-3 0.8s ease-in-out infinite 0.3s;
  }
</style>
