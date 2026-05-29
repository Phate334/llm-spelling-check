# google/gemma-3-1b-pt v0.2.2 FIM Structured Outputs 測試結果

window_radius: `12`

測試資料：`data/sample_sentences.json`

本次使用 v0.2.2 實作中的兩種候選來源：

- `vllm_top_logprob`：原本 prompt logprobs top alternatives。
- `fim_structured_output`：取 suspicious char 的 local window，將目標字挖空，要求 vLLM Structured Outputs 回傳 JSON array 單字候選。

## 結果摘要

```text
corrected: 3
uncertain: 5
no_error: 4
ok: 6
wrong: 0
missed: 1
calls: 219
input_chars: 48054
output_chars: 914708
```

依用途累計：

```text
{"score_original": 21, "fim_candidates": 59, "score_window": 139}
```

詳細 vLLM 每次呼叫紀錄：`google-gemma-3-1b-pt-window12-calls.jsonl`

## 案例結果

```text
case  status     eval      calls top_candidate
01    uncertain  uncertain 24    圜->廁 delta=0.928 source=vllm_top_logprob
02    no_error   missed    17    -
03    uncertain  uncertain 22    提->屜 delta=1.061 source=vllm_top_logprob
04    uncertain  uncertain 20    戰->上 delta=0.863 source=vllm_top_logprob
05    corrected  ok        16    相->箱 delta=1.256 source=vllm_top_logprob
06    corrected  ok        19    誤->務 delta=2.021 source=vllm_top_logprob
07    corrected  ok        17    汽->氣 delta=2.145 source=vllm_top_logprob
08    uncertain  uncertain 20    李->型 delta=0.980 source=vllm_top_logprob
09    uncertain  uncertain 18    結->節 delta=0.810 source=vllm_top_logprob
10    no_error   ok        16    -
11    no_error   ok        17    -
12    no_error   ok        13    -
```

## vLLM 輸入與輸出紀錄口徑

- 每次呼叫的用途、主要 payload 欄位、回傳重點欄位已寫入 `google-gemma-3-1b-pt-window12-calls.jsonl`。
- `input_chars` / `output_chars` 為 JSON request / response 文字長度累計，用來粗估 vLLM API I/O 量。
- `fim_candidates` 呼叫的 payload 會包含 `structured_outputs=true`。
