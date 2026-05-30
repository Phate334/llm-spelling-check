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
- 讀取 JSON array、逐行文字檔或 SGML 評估資料
- 使用內建測試資料 `data/sample_sentences.json`
- 輸出一般文字或 JSON Lines
- 對 `.sgml` 輸入輸出單一 JSON evaluation object 與 CSC metrics
- 調整 vLLM endpoint、模型名稱、risk threshold、修正決策門檻
- 調整 vLLM scoring batch size；預設 `1`

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

## v0.2.4 SGML evaluation

v0.2.4 新增 `.sgml` dataset loader。SGML 輸入會自動進入 evaluation mode，輸出單一 JSON object，包含 dataset 摘要、CSC metrics，以及每筆 case 的 input/gold/result/candidates。

目前 SGML 支援 `ESSAY/TEXT/PASSAGE/MISTAKE/WRONG/CORRECTION` 格式，`location` 視為 1-based character offset，且只支援等長 replacement correction。

## v0.2.3 baseline

v0.2.3 移除 FIM / Structured Outputs candidate path，預設候選來源只保留 `vllm_top_logprob`。`--score-batch-size` 可以讓使用者自行提高同批送到 vLLM `/completions` 的 scoring prompt 數；預設為 `1`，保留最保守的逐筆 request 行為。

可用環境變數：

```text
SPELLING_BASE_URL
SPELLING_MODEL
SPELLING_API_KEY
SPELLING_TIMEOUT
```
