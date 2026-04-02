# covered-call

本專案是互動式的 Sell Covered Call 計算機，可本地執行，也可部署到 Render。

功能：
- 輸入股票代號，自動用 `yfinance` 抓現價與期權鏈
- 依 `Delta` 分出 `保守型 / 中庸型 / 激進型`
- 另外提供 `Call Wall`
- 顯示 `本週 / 下週 / 2週後 / 3週後 / 4週後 / 2個月 / 3個月` 的 covered call 候選
- 顯示權利金、建議成交價、年化報酬、OI 未平倉量、若被履約總獲利

## 安裝

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 本地啟動

在專案根目錄執行：

```bash
python3 covered_call/app.py
```

預設網址：

```text
http://127.0.0.1:5000
```

## Render 部署

本 repo 已包含：
- `requirements.txt`
- `render.yaml`

若要部署到 Render，直接使用這個 GitHub repo：

- Repository: `cfw2214/covered-call`
- Environment: `Python`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn "covered_call.app:app"`

如果你在 Render 介面中選用 Blueprint，也可直接讀取 repo 內的 `render.yaml`。

## 輸出 HTML 路徑

若有需要把 `covered_call.html` 同步到自訂資料夾，可先設定：

```bash
export COVERED_CALL_OUTPUT_DIR=/your/output/path
```

例如：

```bash
export COVERED_CALL_OUTPUT_DIR=/Users/cfw2214/Desktop/stock/covered_call
python3 covered_call/app.py
```

## 手機或外部裝置查看

這一版是本地 Flask 服務，不是公開網址。

如果要讓手機查看，有兩種方式：
- 手機與電腦在同一個區網，之後把 Flask 綁到區網 IP
- 部署到 Render / Railway / Fly.io 之類平台

目前這個 repo 先專注在本地可執行版本。

## 測試

```bash
python3 -m unittest test_covered_call_service.py test_covered_call_app.py -v
```

## 線上使用

部署完成後，Render 會提供公開網址，手機可直接打開使用。
