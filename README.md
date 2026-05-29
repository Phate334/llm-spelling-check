# LLM Spelling Check

用 vLLM `prompt_logprobs` 做中文錯字偵測與修正的 POC。

預設使用：

```text
model: google/gemma-4-E4B
endpoint: http://localhost:8000/v1
```

## 安裝

所有套件都用 `uv` 安裝到專案本地的 `./.venv`：

```bash
uv sync --dev --python 3.13
```

啟動 vLLM：

```bash
docker compose up vllm
```

## CLI 功能

`spelling-check` 可以：

- 直接檢查一個或多個句子
- 讀取 JSON array 或逐行文字檔
- 使用內建測試資料 `data/sample_sentences.json`
- 輸出一般文字或 JSON Lines
- 調整 vLLM endpoint、模型名稱、risk threshold、修正決策門檻

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

跑內建測試資料：

```bash
uv run spelling-check --use-samples
```

讀取檔案並輸出 JSON Lines：

```bash
uv run spelling-check --input-file data/sample_sentences.json --json
```

指定模型與門檻：

```bash
uv run spelling-check \
  --base-url http://localhost:8000/v1 \
  --model google/gemma-4-E4B \
  --risk-threshold 7.0 \
  --strong-delta 1.0 \
  --weak-delta 0.3 \
  --margin 0.4 \
  "這間飯店的服誤一直都很好。"
```

可用環境變數：

```text
SPELLING_BASE_URL
SPELLING_MODEL
SPELLING_API_KEY
SPELLING_TIMEOUT
```
