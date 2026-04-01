# covered-call

本專案是本地互動式的 Sell Covered Call 計算機。

功能：
- 輸入股票代號，自動用 `yfinance` 抓現價與期權鏈
- 依 `Delta` 分出 `保守型 / 中庸型 / 激進型`
- 另外提供 `Call Wall基準`
- 顯示 `1週 / 2週 / 3週 / 4週 / 2個月 / 3個月` 的 covered call 候選
- 顯示權利金、建議成交價、年化報酬、OI 未平倉量、若被履約總獲利

## 安裝

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 啟動

在專案根目錄執行：

```bash
python3 covered_call/app.py
```

預設網址：

```text
http://127.0.0.1:5000
```

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

## 下一步

目前只是本地 standalone repo。

若要建立公開 GitHub repo：
1. 先完成 `gh auth login -h github.com`
2. 再建立公開 repo
3. push 上去
4. 需要手機直接使用時，再補部署設定
