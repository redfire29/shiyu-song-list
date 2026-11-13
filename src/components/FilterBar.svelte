<script lang="ts">
  interface Props {
    searchQuery: string;
    selectedYear: string;
    selectedMonth: string;
    selectedDay: string;
    showOnlyFavorites: boolean;
    showOnlyMembers: boolean;
    availableYears: string[];
    availableMonths: string[];
    availableDays: string[];
    isMemberUnlocked: boolean;
    headerEl?: HTMLElement;
    onRandomPlay: () => void;
    onClearFilters: () => void;
  }

  let {
    searchQuery = $bindable(""),
    selectedYear = $bindable(""),
    selectedMonth = $bindable(""),
    selectedDay = $bindable(""),
    showOnlyFavorites = $bindable(false),
    showOnlyMembers = $bindable(false),
    availableYears,
    availableMonths,
    availableDays,
    isMemberUnlocked,
    headerEl = $bindable(),
    onRandomPlay,
    onClearFilters,
  }: Props = $props();

  const handleYearChange = () => {
    selectedMonth = "";
    selectedDay = "";
  };

  const handleMonthChange = () => {
    selectedDay = "";
  };
</script>

<div
  bind:this={headerEl}
  class="sticky top-0 z-20 pt-3 pb-4 -mx-4 px-4 bg-white/80 backdrop-blur-md border-b border-blue-100 shadow-md transition-all duration-300"
>
  <div class="max-w-2xl mx-auto">
    <div class="flex max-md:flex-col flex-wrap gap-3 md:items-end">
      <!-- 検索入力欄 -->
      <div class="flex-1 max-md:w-full min-w-[180px]">
        <label
          for="search"
          class="block text-[11px] font-black text-blue-800 uppercase mb-1 ml-1 tracking-widest"
          >Search / 検索</label
        >
        <input
          id="search"
          bind:value={searchQuery}
          type="search"
          placeholder="曲名・アーティスト名..."
          class="w-full rounded-lg border-2 border-blue-100 p-2 text-sm focus:border-blue-600 outline-none bg-white/50 text-slate-900 placeholder:text-blue-400 transition-all font-medium"
        />
      </div>

      <div class="flex flex-1 w-full sm:w-auto gap-2">
        <!-- 年フィルター -->
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
              onchange={handleYearChange}
              class="w-full rounded-lg border-2 border-blue-100 p-2 pr-8 text-sm outline-none focus:border-blue-600 bg-white/50 text-slate-900 font-bold cursor-pointer appearance-none transition-colors"
            >
              <option value="">Year</option>
              {#each availableYears as year}
                <option value={year}>{year}</option>
              {/each}
            </select>
            <div
              class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2.5 text-blue-600"
              aria-hidden="true"
            >
              <svg class="h-4 w-4 fill-current" viewBox="0 0 20 20"
                ><path
                  d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                /></svg
              >
            </div>
          </div>
        </div>

        <!-- 月フィルター -->
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
              onchange={handleMonthChange}
              class="w-full rounded-lg border-2 border-blue-100 p-2 pr-8 text-sm outline-none focus:border-blue-600 bg-white/50 text-slate-900 font-bold cursor-pointer appearance-none transition-colors"
            >
              <option value="">Month</option>
              {#each availableMonths as month}
                <option value={month}>{month}</option>
              {/each}
            </select>
            <div
              class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2.5 text-blue-600"
              aria-hidden="true"
            >
              <svg class="h-4 w-4 fill-current" viewBox="0 0 20 20"
                ><path
                  d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                /></svg
              >
            </div>
          </div>
        </div>

        <!-- 日フィルター -->
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
            <div
              class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2.5 text-blue-600"
              aria-hidden="true"
            >
              <svg class="h-4 w-4 fill-current" viewBox="0 0 20 20"
                ><path
                  d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                /></svg
              >
            </div>
          </div>
        </div>
      </div>

      <!-- アクションボタン群 -->
      <div class="flex flex-wrap items-center gap-2 max-md:w-full md:mt-0">
        <button
          type="button"
          onclick={onRandomPlay}
          class="flex-1 md:flex-none px-4 py-2.5 bg-white/50 border-2 border-blue-100 hover:border-blue-400 hover:bg-blue-50/20 text-blue-800 text-xs font-black rounded-lg transition-all active:scale-95 flex items-center justify-center gap-1.5 uppercase tracking-widest cursor-pointer"
          title="ランダムで1曲再生"
          aria-label="ランダムで1曲再生"
        >
          ランダム
        </button>

        <button
          type="button"
          onclick={() => (showOnlyFavorites = !showOnlyFavorites)}
          aria-pressed={showOnlyFavorites}
          class="flex-1 md:flex-none px-4 py-2.5 border-2 transition-all active:scale-95 flex items-center justify-center gap-1.5 text-xs font-black rounded-lg cursor-pointer {showOnlyFavorites
            ? 'border-red-200 bg-red-50/80 text-red-600 hover:bg-red-100/50'
            : 'border-blue-100 bg-white/50 text-blue-800 hover:bg-blue-50/20 hover:border-blue-400'}"
        >
          <span>{showOnlyFavorites ? "すべて表示" : "お気に入り"}</span>
        </button>

        {#if isMemberUnlocked}
          <button
            type="button"
            onclick={() => (showOnlyMembers = !showOnlyMembers)}
            aria-pressed={showOnlyMembers}
            class="flex-1 md:flex-none px-4 py-2.5 border-2 transition-all active:scale-95 flex items-center justify-center gap-1.5 text-xs font-black rounded-lg cursor-pointer {showOnlyMembers
              ? 'border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100'
              : 'border-blue-100 bg-white/50 text-blue-800 hover:bg-blue-50/20 hover:border-blue-400'}"
          >
            <span>{showOnlyMembers ? "すべて表示" : "👑 メンバー"}</span>
          </button>
        {/if}

        <button
          type="button"
          onclick={onClearFilters}
          class="flex-1 md:flex-none px-4 py-2.5 bg-blue-700 hover:bg-blue-800 text-white text-xs font-black rounded-lg transition-all shadow-md active:scale-95 uppercase tracking-widest cursor-pointer"
        >
          リセット
        </button>
      </div>
    </div>
  </div>
</div>

