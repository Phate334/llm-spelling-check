# v0.2.2 FIM Structured Outputs 測試摘要

日期：2026-05-29

測試資料：`data/sample_sentences.json`

本次測試 v0.2.2 新增的候選來源：

- `vllm_top_logprob`：沿用 prompt logprobs top alternatives。
- `fim_structured_output`：取 suspicious char 的 local window，將目標字挖空成 `＿`，要求 vLLM Structured Outputs 回傳 JSON array 單字候選。

每份單模型報告除了候選字與分數，也依照 `AGENTS.md` 紀錄 vLLM I/O：

- `.md` 報告紀錄累計 call 數、用途分布、request/response 文字量累計。
- `*-calls.jsonl` 紀錄每次 vLLM 呼叫的用途、主要 payload 欄位、回傳摘要、輸入/輸出 bytes。

## 指標說明

- `corrected`：pipeline 自動修正。
- `uncertain`：有候選但未通過自動修正門檻。
- `no_error`：沒有產生修正。
- `ok`：輸出文字等於預期答案；乾淨句維持原文也算 ok。
- `missed`：應修正但沒有修正。
- `wrong`：自動修正成非預期答案。
- `calls`：vLLM API 呼叫總數。
- `input_chars` / `output_chars`：JSON request / response 文字長度累計，用於粗估 API I/O 量。

## 結果表

```text
model                 window  corrected  uncertain  no_error  ok  missed  wrong  calls  input_chars  output_chars
google/gemma-4-E4B    12      1          7          4         4   1       0      291    54822        1274494
google/gemma-4-E4B    24      1          6          5         4   2       0      287    54916        1367243
google/gemma-4-E2B    12      1          8          3         4   0       0      214    45696        902222
google/gemma-4-E2B    24      1          8          3         4   0       0      201    44351        871606
google/gemma-3-4b-pt  12      1          8          3         4   0       0      286    57022        1247735
google/gemma-3-4b-pt  24      1          7          4         4   1       0      263    54462        1195675
google/gemma-3-1b-pt  12      3          5          4         6   1       0      219    48054        914708
```

`google/gemma-3-1b-pt` 的 window=24 實驗在使用者要求下停止。原因是小模型 Structured Outputs 表現不可靠且耗時偏高；已完成的 window=12 結果保留。

## 主要觀察

- FIM structured candidate 沒有改善整體 corrected 數。多數 top candidate 仍來自 `vllm_top_logprob`。
- 唯一明顯補到候選的是 `google/gemma-4-E4B` window=12 的 case 01：`圜->園` 由 `fim_structured_output` 產生並排第一，但 `delta=0.823`，低於自動修正門檻，所以仍為 `uncertain`。
- window 從 12 加倍到 24 沒有改善結果。E4B 和 3-4B 反而各多一筆 missed。
- 小模型的 Structured Outputs 不穩，尤其 1B 在 structured generation 上耗時明顯，且本次完成的 window=12 也沒有看到 FIM source 成為 top candidate。
- FIM 方式大幅增加 vLLM calls 與 output payload。以 E4B window=12 為例，總 calls 為 291，其中 `fim_candidates` 52 次，`score_window` 219 次。

## 結論

v0.2.2 的模擬 FIM 方向可以讓模型參考右文並補出少數 top-logprob 找不到的候選，但目前不值得直接當預設主策略。

更可行的後續方向是把 FIM 候選作為受控補充來源，例如只在 top-logprob 沒有可信候選時啟用，或降低 suspicious 數量後再呼叫 FIM，避免 structured generation 對成本與穩定性造成太大影響。
