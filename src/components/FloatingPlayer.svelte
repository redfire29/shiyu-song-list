<script lang="ts">
  import type { Song } from "../lib/songs";

  interface Props {
    videoId: string;
    startTime: number;
    playNonce: number;
    song: Song | null;
    isMinimized: boolean;
    onClose: () => void;
  }

  let {
    videoId,
    startTime,
    playNonce,
    song,
    isMinimized = $bindable(false),
    onClose,
  }: Props = $props();
</script>

<aside
  aria-label="YouTube プレーヤー"
  class="fixed z-50 transition-all duration-500 ease-out bg-white/95 backdrop-blur-md shadow-[0_20px_50px_rgba(0,0,0,0.15)] border-2 border-blue-100 overflow-hidden max-sm:left-0 max-sm:right-0 max-sm:bottom-0 max-sm:w-full max-sm:rounded-t-2xl max-sm:rounded-b-none max-sm:border-x-0 max-sm:border-b-0 sm:bottom-6 sm:right-6 sm:rounded-2xl sm:w-[500px] {isMinimized
    ? 'max-sm:h-[50px] sm:w-[320px]'
    : 'max-sm:h-auto'}"
>
  <!-- タイトルバー -->
  <div class="flex items-center justify-between px-4 py-3 bg-blue-800 text-white">
    <button
      type="button"
      onclick={() => (isMinimized = !isMinimized)}
      aria-expanded={!isMinimized}
      aria-label={isMinimized ? "プレーヤーを展開" : "プレーヤーを最小化"}
      class="flex items-center gap-2 overflow-hidden flex-1 min-w-0 mr-3 text-left cursor-pointer select-none focus-visible:outline-2 focus-visible:outline-white rounded"
    >
      <span
        class="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse flex-shrink-0"
        aria-hidden="true"
      ></span>
      <span class="text-xs font-black tracking-wide truncate">
        {song ? `${song.Title} - ${song.Artist}` : "Now Playing"}
      </span>
    </button>

    <div class="flex items-center gap-3 flex-shrink-0">
      <button
        type="button"
        onclick={() => (isMinimized = !isMinimized)}
        class="text-blue-200 hover:text-white transition-colors cursor-pointer rounded focus-visible:outline-2 focus-visible:outline-white"
        title={isMinimized ? "元に戻す" : "最小化"}
        aria-label={isMinimized ? "元に戻す" : "最小化"}
      >
        {#if isMinimized}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="w-4.5 h-4.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
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
            aria-hidden="true"
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

      <button
        type="button"
        onclick={onClose}
        class="text-blue-200 hover:text-red-400 transition-colors cursor-pointer rounded focus-visible:outline-2 focus-visible:outline-white"
        title="閉じる"
        aria-label="プレーヤーを閉じる"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="w-4.5 h-4.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
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

  <!-- 動画コンテンツ（最小化時は非表示で再生を維持） -->
  <div class="aspect-video bg-black shadow-inner {isMinimized ? 'hidden' : 'block'}">
    {#key `${videoId}-${startTime}-${playNonce}`}
      <iframe
        title={song ? `${song.Title} - YouTube player` : "YouTube player"}
        class="w-full h-full border-0"
        src={`https://www.youtube.com/embed/${videoId}?autoplay=1&start=${startTime}`}
        referrerpolicy="strict-origin-when-cross-origin"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen
      ></iframe>
    {/key}
  </div>
</aside>

