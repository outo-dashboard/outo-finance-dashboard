# Outo Financial Dashboard (Streamlit)

仿照 [Outo CS Dashboard](https://outo-cs-dashboard-dacocj8minzjluaqjo865u.streamlit.app/) 的 Streamlit 架構建置，回答 leadership 六大問題：

1. AP/AR 現況
2. Burn rate
3. 極端情境模擬
4. 臨時大額支出評估
5. 可動用資金
6. 營業額即時監控

---

## 一、本機跑（5 分鐘）

### Step 1：安裝 Python 套件

```bat
cd outo-finance-dashboard-streamlit
pip install -r requirements.txt
```

### Step 2：啟動 Streamlit（先用 mock data）

```bat
streamlit run app.py
```

瀏覽器會自動打開 http://localhost:8501

side bar 把「使用 mock data」勾起來，立刻看到本月報表跟月趨勢兩個 tab。

### Step 3：接上真實 Google Sheets

1. 跟著 README.md（手動或請 Claude Code 協助）建 Google Service Account → 下載 `credentials.json` 放專案根目錄
2. 把 service account email 加進 Outo Financial Dashboard 的「共用」（檢視權限）
3. 把 sidebar 的「使用 mock data」**取消勾選**
4. sidebar 填入 Sheet ID（已預填）跟 credentials 路徑（已預填）
5. 點「🔄 重新載入資料」

---

## 二、Deploy 到 Streamlit Cloud（免費 + 雲端 24h）

Streamlit Cloud 直接從 GitHub repo 部署。每次 push code dashboard 自動更新。

### Step 1：把專案推到 GitHub

```bat
cd outo-finance-dashboard-streamlit
git init
git add .
git commit -m "initial commit"
git branch -M main
gh repo create outo-finance-dashboard --private --source=. --push
```

（如果還沒裝 GitHub CLI：https://cli.github.com/）

### Step 2：上 Streamlit Cloud

1. 開 https://streamlit.io/cloud → 用 GitHub 登入
2. 點「New app」
3. Repository: `outo-finance-dashboard`
4. Branch: `main`
5. Main file path: `app.py`
6. 點「Advanced settings」→「Secrets」→ 貼以下內容（內容看下方 Secrets 設定）：
   ```toml
   OUTO_SHEET_ID = "1-SQGXLw6ROXzIErBpGDXdJYRCOB6oAUAARDo6eeneJI"
   [gcp_service_account]
   type = "service_account"
   project_id = "..."
   private_key_id = "..."
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "sheets-reader@xxx.iam.gserviceaccount.com"
   ...
   ```
   把 `credentials.json` 的內容貼到 `[gcp_service_account]` section
7. Deploy

部署完成後拿到一個網址，可分享給 leadership 即時看儀表板。

### Step 3：改 data_loader 用 Streamlit Secrets（雲端用）

部署到雲端時，credentials 從 `st.secrets` 拿，不從本地 file。請 Claude Code 修改 `lib/data_loader.py`：

> 修改 `lib/data_loader.py`，當 `st.secrets` 裡有 `gcp_service_account` 時用它建 credentials，否則 fallback 用 `credentials.json` 檔案。

---

## 三、檔案結構

```
outo-finance-dashboard-streamlit/
├── README.md               (此檔)
├── requirements.txt        (Python 套件清單)
├── .env.example
├── .gitignore
├── app.py                  (主 Streamlit app)
├── lib/
│   ├── __init__.py
│   ├── data_loader.py      (Google Sheets 讀取 + mock fallback)
│   ├── metrics.py          (六大指標計算)
│   └── charts.py           (Plotly chart 函式)
├── data/
│   ├── mock_data.json      (測試用假資料)
│   └── credentials.json    (你下載的，git ignore，超機密)
└── .streamlit/
    └── config.toml         (主題 + 設定)
```

---

## 四、自動更新

Streamlit Cloud 部署後：

- **即時抓資料**：`load_from_sheets` 用 `@st.cache_data(ttl=3600)`，每小時自動重新抓 Google Sheets。
- **手動刷新**：sidebar 有「🔄 重新載入資料」按鈕清 cache。
- **每月排程**：不用設 cron。Streamlit Cloud 上的 dashboard 是即時的，使用者打開就會抓最新資料。

如果想要更頻繁的更新或 push notification，再請 Claude Code 加：

> 加一個 GitHub Action，每天早上 9 點 ping Streamlit Cloud 的 dashboard URL，並把當天 KPI 寄到 finance@outo.co

---

## 五、擴展（之後想加新資料源）

開 Claude Code 跟它說：

> 我要加一個 TapPay 資料源。寫 `lib/fetch_tappay.py`：讀 .env 的 TAPPAY_API_KEY，抓上個月所有交易，存到 data/tappay.json。並在 sidebar 加一個 expander「TapPay 對帳」顯示每天匯款金額。

> 我要加銀行 CSV 讀取功能。在 sidebar 新增一個檔案上傳元件，使用者上傳第一銀行匯出的 CSV，自動 parse 出每月底餘額，更新 dashboard 的「各 entity 現金部位」。

Claude Code 會直接幫你改。

---

## 六、安全提醒

- `credentials.json` 跟 `.env` 已加進 `.gitignore`
- 上 Streamlit Cloud 時用 Secrets 管理，**絕對不要** commit credentials.json 到 GitHub
- Service account 權限給「檢視者」就好，避免 dashboard bug 動到 Google Sheets

---

## 七、跟原 CS Dashboard 的差異

| 項目 | CS Dashboard | Finance Dashboard |
|---|---|---|
| **Sidebar 篩選** | 月份 + 國家 | 月份 + Entity |
| **資料源** | CSV 路徑 | Google Sheets ID + 憑證路徑 |
| **本月報表 KPI** | 行程管理分、NPS、訂單數... | 月營收、毛利、可動用資金、Runway... |
| **月趨勢** | NPS / CSAT 月趨勢 | 營收/毛利/AP-AR/Burn rate 月趨勢 |
| **互動模擬** | 無 | 大額支出評估 + 情境模擬 cash projection |

---

## 八、常見錯誤

**`ModuleNotFoundError: No module named 'streamlit'`**
→ 跑 `pip install -r requirements.txt`

**啟動後白畫面**
→ 等 5-10 秒，Streamlit 第一次載入需編譯。Cmd+R 重新整理。

**`SpreadsheetNotFound`**
→ Service account email 沒加進 Google Sheets 共用。回 Step 3 確認。

**Plotly chart 顯示不出來**
→ pip install plotly 然後重啟 streamlit
