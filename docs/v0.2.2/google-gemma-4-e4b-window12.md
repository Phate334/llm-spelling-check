# google/gemma-4-E4B v0.2.2 FIM Structured Outputs 測試結果

window_radius: `12`

測試資料：`data/sample_sentences.json`

本次使用 v0.2.2 實作中的兩種候選來源：

- `vllm_top_logprob`：原本 prompt logprobs top alternatives。
- `fim_structured_output`：取 suspicious char 的 local window，將目標字挖空，要求 vLLM Structured Outputs 回傳 JSON array 單字候選。

## 結果摘要

```text
corrected: 1
uncertain: 7
no_error: 4
ok: 4
wrong: 0
missed: 1
calls: 291
input_chars: 54822
output_chars: 1274494
```

依用途累計：

```text
{"score_original": 20, "fim_candidates": 52, "score_window": 219}
```

詳細 vLLM 每次呼叫紀錄：`google-gemma-4-e4b-window12-calls.jsonl`

## 案例結果

```text
case  status     eval      calls top_candidate
01    uncertain  uncertain 26    圜->園 delta=0.823 source=fim_structured_output
02    no_error   missed    14    -
03    uncertain  uncertain 33    提->屜 delta=0.992 source=vllm_top_logprob
04    uncertain  uncertain 32    戰->上 delta=0.634 source=vllm_top_logprob
05    corrected  ok        25    相->箱 delta=1.086 source=vllm_top_logprob
06    uncertain  uncertain 25    誤->侍 delta=1.043 source=vllm_top_logprob
07    uncertain  uncertain 28    汽->氣 delta=1.128 source=vllm_top_logprob
08    uncertain  uncertain 26    李->裡 delta=0.774 source=vllm_top_logprob
09    uncertain  uncertain 32    結->節 delta=0.536 source=vllm_top_logprob
10    no_error   ok        22    -
11    no_error   ok        7     -
12    no_error   ok        21    -
```

## vLLM 輸入與輸出紀錄口徑

- 每次呼叫的用途、主要 payload 欄位、回傳重點欄位已寫入 `google-gemma-4-e4b-window12-calls.jsonl`。
- `input_chars` / `output_chars` 為 JSON request / response 文字長度累計，用來粗估 vLLM API I/O 量。
- `fim_candidates` 呼叫的 payload 會包含 `structured_outputs=true`。
