# 真實數據說明

## 已抓取的真實數據

`data/mock_data.json` 內容已是 **2026-05-15 從 Outo Financial Dashboard Google Sheets 抓取的真實 24 個月數據**（透過 Cowork Drive connector）。

| 指標 | 來源 | 狀態 |
|---|---|---|
| Revenue（已完成營收） | Dashboard Row 6 | ✓ 真實 |
| COGS | Dashboard Row 16 | ✓ 真實 |
| Gross Profit | Dashboard Row 21 | ✓ 真實 |
| Gross Margin % | Dashboard Row 22 | ✓ 真實 |
| Operating Expenses 總額 | Dashboard Row 58 | ✓ 真實（首次抓到正確值）|
| 各 entity 現金部位 | Cash Flow 分頁當前快照 | ✓ 真實 |
| AR / AP 細部 | Dashboard Row 7/8/18/19 | ⚠ 用 2025-12 一個月，需更多月份 |
| OPEX 細部結構（廣告/薪資...）| IS All 分頁 | ⚠ 還是估算值 |

## 真實數據驗證關鍵 KPI

跑 `streamlit run app.py` 開 dashboard 後應該看到：

| KPI | 數字 |
|---|---|
| 2025-12 月營收 | NT$ 6,224,640 |
| 2025-12 毛利 | NT$ 1,730,780 |
| 2025-12 毛利率 | 27.8% |
| 2025 YTD 累計營收 | NT$ 114,353,231 |
| 2024 YTD 累計營收 | NT$ 60,913,889 |
| YoY 成長 | **+87.7%** |
| 可動用資金 | NT$ 17,318,669 |
| 12 月平均 OPEX | NT$ 2,007,442 |
| Runway 中性情境 | ∞（正現金流） |
| Runway 最差情境 | 25.1 個月 |
| Runway 最好情境 | ∞（正現金流） |

## 之後要怎麼更新真實數據

### 方法 A：你裝完 Google Service Account 後（推薦）

```bat
streamlit run app.py
```

打開 dashboard 後在 sidebar：
1. 取消勾選「使用 mock data」
2. 填入 Sheet ID（預填好）+ credentials.json 路徑
3. 點「🔄 重新載入資料」

之後每小時 streamlit 會自動重新抓資料（`@st.cache_data(ttl=3600)`）。

### 方法 B：再回來 Cowork 找我抓

如果你還沒裝好 service account，可以告訴我「請幫我重新從 Google Sheets 抓最新數據」，我會用 Drive connector 拉一次，更新 mock_data.json。

### 方法 C：手動匯出 CSV

1. Google Sheets → 檔案 → 下載 → 逗點分隔值 (.csv)
2. 把 CSV 放到 `data/dashboard.csv`
3. 跟 Claude Code 說「寫一個小 script 把 dashboard.csv 轉成 mock_data.json 格式」

## 已知限制（之後可以擴充）

1. **AR/AP 只有最新月**：之前 Dashboard row 7/8/18/19 只有 2025-12 有值（我幫你填的虛擬資料）。要做 24 個月 AR/AP 趨勢圖，需先在 Google Sheets 把這些 row 補齊歷史。
2. **各 entity 現金部位只有當前**：Cash Flow tab 只記錄當前快照，沒記每月底。要做歷史走勢，未來考慮在 Google Sheets 開一個新分頁「Cash Snapshot Monthly」每月手動或自動補一筆。
3. **OPEX 細部結構為估算**：圓餅圖目前用粗略分配（薪資 962K / 廣告 818K 等）。要精準的話，從 IS All 分頁抓各細項 row。
