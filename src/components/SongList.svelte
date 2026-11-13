<script lang="ts">
  import { onMount, tick } from "svelte";
  import FilterBar from "./FilterBar.svelte";
  import FloatingPlayer from "./FloatingPlayer.svelte";
  import SongRow from "./SongRow.svelte";
  import {
    extractVideoId,
    fetchAllSongs,
    getDateTimestamp,
    groupSongsByDate,
    loadFavorites,
    parseDateParts,
    saveFavorites,
    type Song,
  } from "../lib/songs";

  let songs = $state<Song[]>([]);
  let pending = $state(true);
  let loadError = $state<string | null>(null);

  let searchQuery = $state("");
  let selectedYear = $state("");
  let selectedMonth = $state("");
  let selectedDay = $state("");
  let showOnlyFavorites = $state(false);
  let showOnlyMembers = $state(false);

  let favoriteSongs = $state<string[]>([]);
  let isMemberUnlocked = $state(false);

  let selectedVideoId = $state("");
  let selectedStartTime = $state(0);
  let playNonce = $state(0);
  let isPlayerVisible = $state(false);
  let isMinimized = $state(false);
  let currentPlayingLink = $state("");
  let currentPlayingSong = $state<Song | null>(null);

  let headerHeight = $state(90);
  let headerEl = $state<HTMLElement | undefined>(undefined);

  const favoriteSet = $derived(new Set(favoriteSongs));

  const updateHeaderHeight = () => {
    if (headerEl) {
      headerHeight = headerEl.offsetHeight;
    }
  };

  $effect(() => {
    if (!pending) {
      tick().then(updateHeaderHeight);
    }
  });

  const loadData = async () => {
    pending = true;
    loadError = null;
    try {
      const pwd =
        typeof window !== "undefined"
          ? new URLSearchParams(window.location.search).get("pwd")
          : null;
      const result = await fetchAllSongs(pwd);
      songs = result.songs;
      isMemberUnlocked = result.isMemberUnlocked;
    } catch (err) {
      console.error("データの取得に失敗しました:", err);
      loadError = "楽曲リストの読み込みに失敗しました。通信環境をご確認のうえ再度お試しください。";
    } finally {
      pending = false;
    }
  };

  onMount(() => {
    loadData();
    favoriteSongs = loadFavorites();

    updateHeaderHeight();
    window.addEventListener("resize", updateHeaderHeight);

    const observer = new ResizeObserver(updateHeaderHeight);
    if (headerEl) observer.observe(headerEl);

    const timer1 = setTimeout(updateHeaderHeight, 100);
    const timer2 = setTimeout(updateHeaderHeight, 300);

    return () => {
      window.removeEventListener("resize", updateHeaderHeight);
      observer.disconnect();
      clearTimeout(timer1);
      clearTimeout(timer2);
    };
  });

  const availableYears = $derived.by(() => {
    if (!songs.length) return [] as string[];
    const years = new Set<string>();
    for (const s of songs) {
      const d = parseDateParts(s.Date);
      if (d) years.add(d.year);
    }
    return [...years].sort((a, b) => Number(b) - Number(a));
  });

  const availableMonths = $derived.by(() => {
    const months = new Set<string>();
    for (const s of songs) {
      const d = parseDateParts(s.Date);
      if (!d) continue;
      if (selectedYear && d.year !== selectedYear) continue;
      months.add(d.month);
    }
    return [...months].sort((a, b) => Number(a) - Number(b));
  });

  const availableDays = $derived.by(() => {
    const days = new Set<string>();
    for (const s of songs) {
      const d = parseDateParts(s.Date);
      if (!d) continue;
      if (selectedYear && d.year !== selectedYear) continue;
      if (selectedMonth && d.month !== selectedMonth) continue;
      days.add(d.day);
    }
    return [...days].sort((a, b) => Number(a) - Number(b));
  });

  const filteredSongs = $derived.by(() => {
    let result = songs;

    if (showOnlyFavorites) {
      result = result.filter((s) => favoriteSet.has(s.Link));
    }

    if (showOnlyMembers) {
      result = result.filter((s) => s.isMemberOnly);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase();
      result = result.filter(
        (s) =>
          s.Title.toLowerCase().includes(q) ||
          s.Artist.toLowerCase().includes(q),
      );
    }

    if (selectedYear) {
      result = result.filter((s) => {
        const d = parseDateParts(s.Date);
        return d?.year === selectedYear;
      });
    }

    if (selectedMonth) {
      result = result.filter((s) => {
        const d = parseDateParts(s.Date);
        return d?.month === selectedMonth;
      });
    }

    if (selectedDay) {
      result = result.filter((s) => {
        const d = parseDateParts(s.Date);
        return d?.day === selectedDay;
      });
    }

    return [...result].sort(
      (a, b) => getDateTimestamp(b.Date) - getDateTimestamp(a.Date),
    );
  });

  const groupedSongs = $derived(groupSongsByDate(filteredSongs));

  const toggleFavorite = (song: Song) => {
    const link = song.Link;
    if (favoriteSet.has(link)) {
      favoriteSongs = favoriteSongs.filter((l) => l !== link);
    } else {
      favoriteSongs = [...favoriteSongs, link];
    }
    saveFavorites(favoriteSongs);
  };

  const playVideo = (song: Song) => {
    const link = song.Link;

    // メンバー限定動画は iframe 埋め込み不可のため別タブで開く
    if (song.isMemberOnly) {
      isPlayerVisible = false;
      selectedVideoId = "";
      currentPlayingLink = link;
      currentPlayingSong = song;
      if (link) {
        window.open(link, "_blank", "noopener,noreferrer");
      }
      return;
    }

    const { id, time } = extractVideoId(link);
    currentPlayingLink = link;
    currentPlayingSong = song;

    if (id) {
      selectedVideoId = id;
      selectedStartTime = time;
      playNonce += 1;
      isPlayerVisible = true;
      isMinimized = false;
    } else if (link) {
      window.open(link, "_blank", "noopener,noreferrer");
    }
  };

  const closePlayer = () => {
    isPlayerVisible = false;
    selectedVideoId = "";
    currentPlayingLink = "";
    currentPlayingSong = null;
  };

  const playRandomSong = async () => {
    if (filteredSongs.length === 0) return;
    const randomIndex = Math.floor(Math.random() * filteredSongs.length);
    const randomSong = filteredSongs[randomIndex];
    playVideo(randomSong);

    await tick();
    const activeEl = document.querySelector(".playing-active-card");
    if (activeEl) {
      activeEl.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  const clearFilters = () => {
    searchQuery = "";
    selectedYear = "";
    selectedMonth = "";
    selectedDay = "";
    showOnlyFavorites = false;
    showOnlyMembers = false;
  };
</script>

<div class="min-h-screen bg-blue-50/80 text-slate-900 py-6 px-4 sm:px-6 font-sans">
  <div class="max-w-2xl mx-auto">
    <!-- サイトヘッダー -->
    <header class="text-center mb-8">
      <h1 class="text-4xl font-black text-blue-800 tracking-tighter">
        しゆ。Song List
      </h1>
      <a
        href="https://www.youtube.com/@shiyumarurun"
        target="_blank"
        rel="noopener noreferrer"
        class="inline-block text-blue-800 hover:text-red-600 transition-colors my-2 rounded-lg focus-visible:outline-2 focus-visible:outline-blue-600"
        aria-label="YouTube チャンネル"
        title="YouTube チャンネル"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="w-10 h-10"
          fill="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"
          />
        </svg>
      </a>
    </header>

    <!-- 固定検索・フィルターバー -->
    <FilterBar
      bind:searchQuery
      bind:selectedYear
      bind:selectedMonth
      bind:selectedDay
      bind:showOnlyFavorites
      bind:showOnlyMembers
      bind:headerEl
      {availableYears}
      {availableMonths}
      {availableDays}
      {isMemberUnlocked}
      onRandomPlay={playRandomSong}
      onClearFilters={clearFilters}
    />

    <!-- メインコンテンツ -->
    <main class="mt-8">
      {#if pending}
        <!-- 読み込み中スケルトン -->
        <div class="space-y-3" aria-busy="true" aria-label="楽曲を読み込み中">
          {#each Array(6) as _}
            <div
              class="flex items-center bg-white/60 border border-blue-50/50 px-4 py-4 rounded-xl shadow-sm animate-pulse"
            >
              <div class="w-8 h-4 bg-slate-200 rounded"></div>
              <div class="flex-1 ml-2 space-y-2">
                <div class="w-2/3 h-5 bg-slate-200 rounded"></div>
                <div class="w-1/4 h-3 bg-slate-200 rounded"></div>
              </div>
              <div class="flex gap-2 ml-4">
                <div class="w-7 h-7 bg-slate-200 rounded-full"></div>
                <div class="w-7 h-7 bg-slate-200 rounded-full"></div>
              </div>
            </div>
          {/each}
        </div>
      {:else if loadError}
        <!-- 読み込みエラー表示 -->
        <div
          role="alert"
          class="text-center py-16 px-6 bg-white rounded-2xl border-2 border-red-200 shadow-sm mt-4 space-y-4"
        >
          <p class="text-red-700 text-sm font-bold">{loadError}</p>
          <button
            type="button"
            onclick={loadData}
            class="px-5 py-2.5 bg-blue-700 hover:bg-blue-800 text-white text-xs font-black rounded-lg transition-all shadow-md active:scale-95 uppercase tracking-widest cursor-pointer"
          >
            再読み込み
          </button>
        </div>
      {:else if groupedSongs.length === 0}
        <!-- 該当なし -->
        <div
          class="text-center py-20 text-blue-800 text-sm font-black bg-white rounded-2xl border-4 border-dashed border-blue-200 mt-4"
        >
          該当する楽曲が見つかりませんでした
        </div>
      {:else}
        <!-- 日付グループ別リスト -->
        <div class="space-y-6">
          {#each groupedSongs as group (group.date)}
            <section aria-label={group.date}>
              <div
                class="sticky z-10 bg-blue-50/95 py-3 border-b-2 border-blue-100 mb-3"
                style="top: {headerHeight}px;"
              >
                <div class="flex items-center gap-3">
                  <h2
                    class="bg-blue-800 text-white px-3 py-1 rounded text-xs font-black tracking-widest shadow-md"
                  >
                    {group.date}
                  </h2>
                  <div class="flex-1 h-[2px] bg-blue-200" aria-hidden="true"></div>
                </div>
              </div>

              <ul class="space-y-3">
                {#each group.songs as song, index (`${song.Date}-${song.Link}-${index}`)}
                  <SongRow
                    {song}
                    indexLabel={String(index + 1).padStart(2, "0")}
                    isPlaying={currentPlayingLink === song.Link}
                    isFavorite={favoriteSet.has(song.Link)}
                    onPlay={playVideo}
                    onToggleFavorite={toggleFavorite}
                  />
                {/each}
              </ul>
            </section>
          {/each}
        </div>
      {/if}
    </main>

    <!-- フッター -->
    <footer class="mt-16 mb-20 border-t-4 border-blue-200 pt-8 text-center">
      <span
        class="text-blue-800 text-xs font-black tracking-[0.2em] uppercase bg-blue-100 px-4 py-2 rounded-full"
      >
        Total Catalog / 合計 {filteredSongs.length} 曲
      </span>
    </footer>
  </div>
</div>

<!-- YouTube フローティングプレーヤー -->
{#if isPlayerVisible && selectedVideoId}
  <FloatingPlayer
    videoId={selectedVideoId}
    startTime={selectedStartTime}
    {playNonce}
    song={currentPlayingSong}
    bind:isMinimized
    onClose={closePlayer}
  />
{/if}
