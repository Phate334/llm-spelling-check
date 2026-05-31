# Changelog

## v0.2.6

- 導入 `pydantic-settings`，集中管理 `SPELLING_*` 環境變數預設值。
- CLI、WebUI 啟動參數與 API 預設 model settings 改用同一組環境設定來源。
- 更新 Docker / API 文件與 compose image tag 到 v0.2.6。

## v0.2.5

- 新增 FastAPI WebUI，可手動輸入文字或上傳 `.json` / `.sgml`。
- 新增 `spelling-check-web` script，預設可用環境變數帶入 vLLM endpoint、模型與 timeout。
- 新增 `/api/parse`、`/api/detect`、`/api/correct`、`/api/evaluate`、`/api/run` 分段 API。
- WebUI 顯示 suspicious highlight、corrected text、候選修正分數、summary 與 CSC metrics。
- 新增 Dockerfile 預設啟動 WebUI 服務。
- 新增 `docs/api.md` API reference 與 v0.2.5 summary。
- 補充 FastAPI service、API 與 Playwright WebUI smoke tests。

## v0.2.4

- 新增 `.sgml` dataset loader，支援 `ESSAY/TEXT/PASSAGE/MISTAKE/WRONG/CORRECTION` 格式。
- `.sgml` input 會自動進入 evaluation mode，輸出單一 JSON object，包含 dataset、metrics 與 cases。
- SGML gold text 由 1-based `location`、`WRONG`、`CORRECTION` 產生，並驗證 id、位置、原字與等長 replacement。
- 補充 SGML loader、metrics 與 CLI evaluation tests。
- 精簡 CLI client/config 建構與 SGML output 組裝邏輯。

## v0.2.3

- 移除 FIM / Structured Outputs candidate path，候選來源回到單一 `vllm_top_logprob` baseline。
- 移除 CLI 的 `--fim-candidate-limit`、`--fim-max-tokens`。
- 新增 scoring batch path 與 `--score-batch-size`，預設值為 `1`。
- 新增 CSC metrics helper，可計算 Detection Precision / Recall / F1、Correction Precision / Recall / F1、False Positive Rate。

## v0.2.2

- 新增 `fim_structured_output` 候選來源，透過 local window 挖空目標字並要求 vLLM Structured Outputs 回傳 JSON array 單字候選。
- `VllmClient` 與 pipeline 新增 FIM 候選整合流程，CLI 可用 `--fim-candidate-limit`、`--fim-max-tokens` 控制。
- 預設仍只使用 `vllm_top_logprob`；FIM 改為可選的補充候選來源，避免直接增加成本與不穩定性。
- 新增 `docs/v0.2.2/` 多模型測試報告與 `*-calls.jsonl`，累計紀錄 vLLM request/response I/O。
- 結論：FIM 能補到少數 top-logprob 找不到的候選，但整體 corrected 數沒有改善，不適合作為預設主策略。

## v0.2.1

- 新增 prefix next-token decoding 候選來源。
- 對 suspicious char 前文呼叫 vLLM `max_tokens=1`、`logprobs=10` 產生候選。
- 重測 `gemma-3-1b-pt`、`gemma-3-4b-pt`、`gemma-4-E2B`、`gemma-4-E4B`。
- 結論：corrected 數沒有比 v0.2.0 無查表版本改善，但 vLLM calls 明顯增加。

## v0.2.0

- 移除固定錯字表候選，不再使用 `WORD_CONFUSIONS` / `CHAR_CONFUSIONS`。
- 候選只從 vLLM `prompt_logprobs` top alternatives 產生。
- top-logprob 候選只保留單一 CJK 字元。
- 重測四個非 IT 模型並整理報告。
- 結論：方法論比查表乾淨，但修正品質相較 v0.1.0 退步；clean cases 全部維持 `no_error`。

## v0.1.0

- 建立 vLLM prompt-logprob 中文拼字檢查 PoC。
- 實作 CLI，可讀取句子、JSON array、逐行文字檔與內建 sample data。
- 使用 risk score 找 suspicious chars，再產生候選並用 local window rescoring 決策。
- 候選來源包含 `word_lexicon`、`char_confusion`、`vllm_top_logprob`。
- 整理多模型測試報告並加上 `v0.1.0` tag。
