# google/gemma-3-4b-pt v0.2.2 FIM Structured Outputs 測試結果

window_radius: `12`

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
calls: 286
input_chars: 57022
output_chars: 1247735
```

依用途累計：

```text
{"score_original": 21, "fim_candidates": 59, "score_window": 206}
```

詳細 vLLM 每次呼叫紀錄：`google-gemma-3-4b-pt-window12-calls.jsonl`

## 案例結果

```text
case  status     eval      calls top_candidate
01    uncertain  uncertain 30    圜->廁 delta=0.685 source=vllm_top_logprob
02    uncertain  uncertain 28    份->篇 delta=0.393 source=vllm_top_logprob
03    uncertain  uncertain 27    提->屜 delta=0.857 source=vllm_top_logprob
04    uncertain  uncertain 25    戰->廠 delta=0.608 source=vllm_top_logprob
05    corrected  ok        21    相->箱 delta=1.575 source=vllm_top_logprob
06    uncertain  uncertain 23    誤->侍 delta=1.062 source=vllm_top_logprob
07    uncertain  uncertain 29    汽->氣 delta=1.796 source=vllm_top_logprob
08    uncertain  uncertain 27    李->編 delta=0.600 source=vllm_top_logprob
09    uncertain  uncertain 19    結->節 delta=0.579 source=vllm_top_logprob
10    no_error   ok        22    -
11    no_error   ok        16    -
12    no_error   ok        19    -
```

## vLLM 輸入與輸出紀錄口徑

- 每次呼叫的用途、主要 payload 欄位、回傳重點欄位已寫入 `google-gemma-3-4b-pt-window12-calls.jsonl`。
- `input_chars` / `output_chars` 為 JSON request / response 文字長度累計，用來粗估 vLLM API I/O 量。
- `fim_candidates` 呼叫的 payload 會包含 `structured_outputs=true`。
