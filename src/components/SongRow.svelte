<script lang="ts">
  import type { Song } from "../lib/songs";

  interface Props {
    song: Song;
    indexLabel: string;
    isPlaying: boolean;
    isFavorite: boolean;
    onPlay: (song: Song) => void;
    onToggleFavorite: (song: Song) => void;
  }

  let {
    song,
    indexLabel,
    isPlaying,
    isFavorite,
    onPlay,
    onToggleFavorite,
  }: Props = $props();
</script>

<li
  class="group flex items-center pr-3 transition-all duration-300 rounded-xl shadow-sm {isPlaying
    ? 'playing-active-card bg-blue-50/60 border-2 border-blue-500 shadow-md'
    : 'bg-white border border-blue-200 hover:border-blue-400 hover:-translate-y-0.5 hover:shadow-md active:scale-[0.995]'}"
>
  <button
    type="button"
    onclick={() => onPlay(song)}
    aria-label={`${song.Title}（${song.Artist}）を再生`}
    class="flex flex-1 items-center min-w-0 px-4 py-4 text-left cursor-pointer rounded-l-xl focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-blue-600"
  >
    <!-- 番号または再生中イコライザー -->
    <div
      class="text-xs font-mono text-slate-400 w-8 font-bold flex items-center justify-start flex-shrink-0"
      aria-hidden="true"
    >
      {#if isPlaying}
        <div class="flex items-end gap-[2px] h-[18px] w-4 pr-1">
          <div class="w-[3px] bg-blue-600 rounded-full eq-bar-1"></div>
          <div class="w-[3px] bg-blue-600 rounded-full eq-bar-2"></div>
          <div class="w-[3px] bg-blue-600 rounded-full eq-bar-3"></div>
        </div>
      {:else}
        {indexLabel}
      {/if}
    </div>

    <div class="flex-1 min-w-0 ml-2">
      <div class="flex flex-col">
        <div class="flex items-center gap-2">
          <h3
            class="text-base font-black truncate transition-colors {isPlaying
              ? 'text-blue-800'
              : 'text-slate-900 group-hover:text-blue-600'}"
          >
            {song.Title}
          </h3>
          {#if song.isMemberOnly}
            <span
              class="px-1.5 py-0.5 bg-amber-100 text-amber-700 border border-amber-300 text-[10px] font-black rounded shadow-sm flex-shrink-0 tracking-widest uppercase"
              >Member</span
            >
          {/if}
        </div>
        <span
          class="text-xs font-bold text-blue-700 mt-0.5 truncate uppercase tracking-tight"
          >{song.Artist}</span
        >
      </div>
    </div>
  </button>

  <!-- 操作ボタン群：お気に入り登録 & YouTube 外部リンク -->
  <div class="flex items-center gap-1.5 ml-2 flex-shrink-0">
    <button
      type="button"
      onclick={() => onToggleFavorite(song)}
      aria-pressed={isFavorite}
      aria-label={isFavorite
        ? `${song.Title} をお気に入りから削除`
        : `${song.Title} をお気に入りに追加`}
      title={isFavorite ? "お気に入りから削除" : "お気に入りに追加"}
      class="p-2 transition-all hover:scale-110 cursor-pointer text-slate-400 hover:text-red-500 rounded-lg focus-visible:outline-2 focus-visible:outline-blue-600"
    >
      {#if isFavorite}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="w-6 h-6 text-red-500 fill-current"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
          />
        </svg>
      {:else}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="w-6 h-6 fill-none stroke-current"
          stroke-width="2"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
          />
        </svg>
      {/if}
    </button>

    <a
      href={song.Link}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`${song.Title} をYouTubeで再生`}
      title="YouTubeで再生"
      class="p-2 text-blue-500 hover:text-red-600 transition-all hover:scale-110 rounded-lg focus-visible:outline-2 focus-visible:outline-blue-600"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="w-6 h-6"
        fill="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"
        />
      </svg>
    </a>
  </div>
</li>

<style>
  @keyframes equalize-1 {
    0%,
    100% {
      height: 4px;
    }
    50% {
      height: 16px;
    }
  }
  @keyframes equalize-2 {
    0%,
    100% {
      height: 16px;
    }
    50% {
      height: 6px;
    }
  }
  @keyframes equalize-3 {
    0%,
    100% {
      height: 8px;
    }
    50% {
      height: 18px;
    }
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

