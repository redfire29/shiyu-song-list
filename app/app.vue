<template lang="pug">
//- 背景稍微調深一點點，讓白色卡片更跳脫出來
div(class="min-h-screen bg-blue-50/80 text-slate-900 py-6 px-4 sm:px-6 font-sans")
  div(class="max-w-2xl mx-auto")
    
    //- 標題區 (使用深海藍，強化對比)
    div(class="text-center mb-8")
      h1(class="text-4xl font-black text-blue-800 tracking-tighter") しゆ。Song List
      a(href="https://www.youtube.com/@shiyumarurun", target="_blank", class="text-blue-800 my-2 block text-2xl") https://www.youtube.com/@shiyumarurun
    //- 固定在頂部的控制面板 (加強邊框與對比)
    div(class="sticky top-0 z-20 pt-2 pb-4 -mx-4 px-4 bg-white border-b-4 border-blue-200 shadow-lg")
      div(class="max-w-2xl mx-auto")
        div(class="flex flex-wrap gap-3 items-end")
          
          //- 検索 (文字顏色加深)
          div(class="flex-1 min-w-[180px]")
            label(class="block text-[11px] font-black text-blue-800 uppercase mb-1 ml-1 tracking-widest") Search / 検索
            input(
              v-model="searchQuery" 
              type="text" 
              placeholder="曲名、アーティスト名..." 
              class="w-full rounded-lg border-2 border-blue-200 p-2 text-sm focus:border-blue-600 outline-none bg-blue-50/30 text-slate-900 placeholder:text-blue-400 transition-all font-medium"
            )
          
          //- 日付フィルター (文字顏色加深)
          div(class="w-full sm:w-44")
            label(class="block text-[11px] font-black text-blue-800 uppercase mb-1 ml-1 tracking-widest") Date / 日付
            select(
              v-model="selectedDate" 
              class="w-full rounded-lg border-2 border-blue-200 p-2 text-sm outline-none focus:border-blue-600 bg-blue-50/30 text-slate-900 font-bold cursor-pointer appearance-none"
            )
              option(value="") すべて表示 ({{ availableDates.length }})
              option(v-for="date in availableDates" :key="date" :value="date") {{ date }}
          
          //- リセット (按鈕顏色加強)
          button(
            @click="clearFilters" 
            class="px-5 py-2.5 bg-blue-700 hover:bg-blue-800 text-white text-xs font-black rounded-lg transition-all shadow-md active:scale-95 uppercase tracking-widest"
          ) リセット

    //- 読み込み状態 (使用深藍色)
    div(v-if="pending" class="text-center py-20 text-blue-800 font-black")
      p(class="animate-pulse") 読み込み中...
    
    //- リスト表示
    div(v-else class="space-y-3 mt-8")
      template(v-for="(song, index) in filteredSongs" :key="index")
        
        //- 日付ヘッダー (深藍色標籤，極高對比)
        div(v-if="isNewDate(index)" class="sticky top-[90px] z-10 bg-blue-50/95 py-3 border-b-2 border-blue-100 mb-2")
          div(class="flex items-center gap-3")
            div(class="bg-blue-800 text-white px-3 py-1 rounded text-xs font-black tracking-widest shadow-md")
              | {{ song.Date }}
            div(class="flex-1 h-[2px] bg-blue-200")

        //- 歌曲橫條 (純白底，深色字)
        div(class="group flex items-center bg-white border border-blue-200 hover:border-blue-600 px-4 py-4 transition-all rounded-xl shadow-sm hover:shadow-md")
          //- 序號 (調整為中灰色，避免干擾閱讀但保持可見)
          div(class="text-xs font-mono text-slate-400 w-6 font-bold") {{ getDailyIndex(index) }}
          
          div(class="flex-1 min-w-0 ml-3")
            div(class="flex flex-col")
              //- 歌曲標題：深色 Slate-900
              h3(class="text-base font-black text-slate-900 truncate group-hover:text-blue-700 transition-colors") {{ song.Title }}
              //- 歌手名稱：調深至 Blue-700
              span(class="text-xs font-bold text-blue-700 mt-1 truncate uppercase tracking-tight") {{ song.Artist }}
          
          //- YouTube 連結 (顏色調深)
          a(
            :href="song.Link" 
            target="_blank" 
            class="ml-4 p-2 text-blue-500 hover:text-red-600 transition-colors"
            title="YouTubeで再生"
          )
            svg(xmlns="http://www.w3.org/2000/svg" class="w-7 h-7" fill="currentColor" viewBox="0 0 24 24")
              path(d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z")

      //- 該当なし
      div(v-if="filteredSongs.length === 0" class="text-center py-20 text-blue-800 text-sm font-black bg-white rounded-2xl border-4 border-dashed border-blue-200 mt-4")
        | 該当する楽曲が見つかりませんでした

    //- フッター (文字加深)
    div(class="mt-16 mb-20 border-t-4 border-blue-200 pt-8 text-center")
      span(class="text-blue-800 text-xs font-black tracking-[0.2em] uppercase bg-blue-100 px-4 py-2 rounded-full") 
        | Total Catalog / 合計 {{ filteredSongs.length }} 曲
</template>

<script setup>
import Papa from 'papaparse'

// 1. 填入你提供的 CSV 連結，並在後面加上時間戳記防止快取
const SHEET_CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRPNWnxfDY4g6QEACTULQzC1HHv8kmvUDvOX2lLHFQ9Zqo6_7QEkJe0hWc7WNUWZmBbVFASKM_L0iB2/pub?gid=1069936388&single=true&output=csv'

// 2. 使用 $fetch 代替 useFetch 來獲取原始文字，避免 Nuxt 誤判格式
const songs = ref([])
const pending = ref(true)

const loadData = async () => {
  pending.value = true
  try {
    // 加入隨機參數 t，確保每次抓取都是最新的
    const csvData = await $fetch(`${SHEET_CSV_URL}&t=${Date.now()}`)
    
    const parsed = Papa.parse(csvData, {
      header: true,
      skipEmptyLines: true
    })
    
    // 這裡要確保你的試算表標題是 "Date", "Title", "Artist", "Link"
    songs.value = parsed.data
  } catch (err) {
    console.error('資料抓取失敗:', err)
  } finally {
    pending.value = false
  }
}

// 初始讀取
onMounted(() => {
  loadData()
})

const searchQuery = ref('')
const selectedDate = ref('')

// 輔助函式：處理 yyyy/mm/dd 排序
const getTime = (dateStr) => {
  if (!dateStr) return 0
  return new Date(dateStr.replace(/\//g, '-')).getTime()
}

// 日期下拉選單排序 (由新到舊)
const availableDates = computed(() => {
  if (!songs.value.length) return []
  const dates = [...new Set(songs.value.map(s => s.Date).filter(Boolean))]
  return dates.sort((a, b) => getTime(b) - getTime(a))
})

// 歌曲列表過濾與排序 (由新到舊)
const filteredSongs = computed(() => {
  let result = [...songs.value]

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(s => 
      (s.Title?.toLowerCase().includes(q)) || 
      (s.Artist?.toLowerCase().includes(q))
    )
  }

  if (selectedDate.value) {
    result = result.filter(s => s.Date === selectedDate.value)
  }

  // 確保依照日期由新到舊排序
  return result.sort((a, b) => getTime(b.Date) - getTime(a.Date))
})

// 計算該日期分組內的序號 (01, 02...)
const getDailyIndex = (currentIndex) => {
  const currentSong = filteredSongs.value[currentIndex]
  if (!currentSong) return '01'
  let count = 0
  for (let i = 0; i <= currentIndex; i++) {
    if (filteredSongs.value[i].Date === currentSong.Date) {
      count++
    }
  }
  return String(count).padStart(2, '0')
}

const isNewDate = (index) => {
  if (index === 0) return true
  return filteredSongs.value[index].Date !== filteredSongs.value[index - 1].Date
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedDate.value = ''
}
</script>