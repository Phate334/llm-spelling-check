# google/gemma-4-E2B v0.2.2 FIM Structured Outputs 測試結果

window_radius: `24`

測試資料：`data/sample_sentences.json`

本次使用 v0.2.2 實作中的兩種候選來源：

- `vllm_top_logprob`：原本 prompt logprobs top alternatives。
- `fim_structured_output`：取 suspicious char 的 local window，將目標字挖空，要求 vLLM Structured Outputs 回傳 JSON array 單字候選。

## 結果摘要

```text
corrected: 1
uncertain: 8
no_error: 3
ok: 4
wrong: 0
missed: 0
calls: 201
input_chars: 44351
output_chars: 871606
```

依用途累計：

```text
{"score_original": 23, "fim_candidates": 55, "score_window": 123}
```

詳細 vLLM 每次呼叫紀錄：`google-gemma-4-e2b-window24-calls.jsonl`

## 案例結果

```text
case  status     eval      calls top_candidate
01    uncertain  uncertain 25    圜->廁 delta=0.871 source=vllm_top_logprob
02    uncertain  uncertain 23    察->視 delta=0.333 source=vllm_top_logprob
03    uncertain  uncertain 21    提->屜 delta=1.160 source=vllm_top_logprob
04    uncertain  uncertain 15    戰->上 delta=0.853 source=vllm_top_logprob
05    corrected  ok        16    相->箱 delta=1.469 source=vllm_top_logprob
06    uncertain  uncertain 14    誤->侍 delta=1.104 source=vllm_top_logprob
07    uncertain  uncertain 22    汽->氣 delta=1.420 source=vllm_top_logprob
08    uncertain  uncertain 22    李->頓 delta=0.751 source=vllm_top_logprob
09    uncertain  uncertain 15    結->節 delta=0.758 source=vllm_top_logprob
10    no_error   ok        12    -
11    no_error   ok        2     -
12    no_error   ok        14    -
```

## vLLM 輸入與輸出紀錄口徑

- 每次呼叫的用途、主要 payload 欄位、回傳重點欄位已寫入 `google-gemma-4-e2b-window24-calls.jsonl`。
- `input_chars` / `output_chars` 為 JSON request / response 文字長度累計，用來粗估 vLLM API I/O 量。
- `fim_candidates` 呼叫的 payload 會包含 `structured_outputs=true`。
