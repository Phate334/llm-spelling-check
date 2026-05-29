# Changelog

## v0.2.2

- 新增 `fim_structured_output` 候選來源，透過 local window 挖空目標字並要求 vLLM Structured Outputs 回傳 JSON array 單字候選。
- `VllmClient` 與 pipeline 新增 FIM 候選整合流程，CLI 可用 `--fim-candidate-limit`、`--fim-max-tokens` 控制。
- 預設仍只使用 `vllm_top_logprob`；FIM 改為可選的補充候選來源，避免直接增加成本與不穩定性。
- 升級專案版本到 `0.2.2`。
- 新增 `docs/v0.2.2/` 多模型測試報告與 `*-calls.jsonl`，累計紀錄 vLLM request/response I/O。
- 結論：FIM 能補到少數 top-logprob 找不到的候選，但整體 corrected 數沒有改善，不適合作為預設主策略。

## v0.2.1

- 新增 prefix next-token decoding 候選來源。
- 對 suspicious char 前文呼叫 vLLM `max_tokens=1`、`logprobs=10` 產生候選。
- 升級專案版本到 `0.2.1`。
- 重測 `gemma-3-1b-pt`、`gemma-3-4b-pt`、`gemma-4-E2B`、`gemma-4-E4B`。
- 結論：corrected 數沒有比 v0.2.0 無查表版本改善，但 vLLM calls 明顯增加。

## v0.2.0

- 移除固定錯字表候選，不再使用 `WORD_CONFUSIONS` / `CHAR_CONFUSIONS`。
- 候選只從 vLLM `prompt_logprobs` top alternatives 產生。
- top-logprob 候選只保留單一 CJK 字元。
- 升級專案版本到 `0.2.0`。
- 重測四個非 IT 模型並整理報告。
- 結論：方法論比查表乾淨，但修正品質相較 v0.1.0 退步；clean cases 全部維持 `no_error`。

## v0.1.0

- 建立 vLLM prompt-logprob 中文拼字檢查 PoC。
- 實作 CLI，可讀取句子、JSON array、逐行文字檔與內建 sample data。
- 使用 risk score 找 suspicious chars，再產生候選並用 local window rescoring 決策。
- 候選來源包含 `word_lexicon`、`char_confusion`、`vllm_top_logprob`。
- 整理多模型測試報告並加上 `v0.1.0` tag。
