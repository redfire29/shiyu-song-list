import Papa from 'papaparse'

export default defineEventHandler(async (event) => {
    // 這裡貼上你剛剛複製的 Google Sheet CSV 連結
    const SHEET_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRPNWnxfDY4g6QEACTULQzC1HHv8kmvUDvOX2lLHFQ9Zqo6_7QEkJe0hWc7WNUWZmBbVFASKM_L0iB2/pub?gid=1069936388&single=true&output=csv'

    try {
        // 1. 從 Google 抓取 CSV 文字檔
        const csvString = await $fetch(SHEET_URL)

        // 2. 使用 PapaParse 解析成 JSON 物件
        const { data } = Papa.parse(csvString, {
            header: true, // 使用第一行當作欄位名稱
            skipEmptyLines: true // 跳過空行
        })

        // 3. 回傳整理好的資料
        return data
    } catch (error) {
        throw createError({
            statusCode: 500,
            statusMessage: '無法讀取歌單資料',
        })
    }
})