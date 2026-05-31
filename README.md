# LLM Spelling Check

用 vLLM `prompt_logprobs` 做中文錯字偵測與修正的 POC。

## 安裝

uv sync or Docker

## 共同設定

`spelling-check` 與 `spelling-check-web` 都會先讀取環境變數作為預設值；如果有明確傳入 CLI 參數，則以 CLI 參數為準。

共享的 model / client 設定：

```text
SPELLING_BASE_URL=http://localhost:7072/v1
SPELLING_MODEL=gemma-4-26b-a4b
SPELLING_API_KEY
SPELLING_TIMEOUT=30
```

WebUI 啟動位址另外可用：

```text
SPELLING_WEB_HOST=127.0.0.1
SPELLING_WEB_PORT=8000
```

本 repo 不再追蹤 `data/` 內的資料檔；請先參考 `data/README.md` 放入自己的測試資料。

## CLI 功能

`spelling-check` 可以：

- 直接檢查一個或多個句子
- 讀取 JSON 字串陣列、逐行文字檔或 SGML 評估資料
- 讀取你自行放在 `data/` 的本機測試資料
- 輸出一般文字或 JSON Lines
- 對 `.sgml` 輸入輸出單一 JSON evaluation object 與 CSC metrics
- 調整 vLLM endpoint、模型名稱、API key 與 timeout
- 調整 prompt logprobs、risk threshold、suspicious limit、candidate limit 與 window radius
- 調整 vLLM scoring batch size，以及 strong / weak delta、margin 等修正決策門檻

## 執行範例

檢查單一句子：

```bash
uv run spelling-check "我今天想喝一杯咖非。"
```

檢查多個句子：

```bash
uv run spelling-check \
  "我今天想喝一杯咖非。" \
  "這份報告需要再檢察一次。"
```

跑你放在 `data/` 的本機測試資料：

```bash
uv run spelling-check --use-samples
```

預設會讀 `data/sample_sentences.json`；若檔案不存在，CLI 會提示你改用 `--input-file` 或先把資料放進 `data/`。

讀取檔案並輸出 JSON Lines：

```bash
uv run spelling-check --input-file data/sample_sentences.json --json
```

讀取 SGML 評估資料並輸出 metrics JSON：

```bash
uv run spelling-check --input-file data/fiona_wrong_results_Training.sgml
```

指定模型與門檻：

```bash
uv run spelling-check \
  --base-url http://localhost:8000/v1 \
  --model google/gemma-4-E4B \
  --risk-threshold 7.0 \
  --score-batch-size 1 \
  --strong-delta 1.0 \
  --weak-delta 0.3 \
  --margin 0.4 \
  "這間飯店的服誤一直都很好。"
```

## WebUI / API

啟動 FastAPI WebUI：

```bash
uv run spelling-check-web --host 127.0.0.1 --port 8090
```

共享的 model / client 設定位於前面的「共同設定」；WebUI 啟動位址可另外用 `SPELLING_WEB_HOST`、`SPELLING_WEB_PORT` 覆寫。WebUI 支援 textarea 手動輸入，以及 `.json` / `.sgml` file upload。API reference 見 `docs/api.md`。

## Docker

建置 WebUI image：

```bash
docker build -t llm-spelling-check:v0.2.6 .
```

Linux 本機開發若要讓容器連到 host 上的 vLLM，可使用 host network：

```bash
docker run --rm --network host \
  -e SPELLING_BASE_URL=http://localhost:7072/v1 \
  -e SPELLING_MODEL=gemma-4-26b-a4b \
  llm-spelling-check:v0.2.6
```

一般 bridge network 可改用容器可連到 host 的 endpoint，例如 Docker Desktop 常見的 `host.docker.internal`：

```bash
docker run --rm -p 8000:8000 \
  -e SPELLING_BASE_URL=http://host.docker.internal:7072/v1 \
  -e SPELLING_MODEL=gemma-4-26b-a4b \
  llm-spelling-check:v0.2.6
```
