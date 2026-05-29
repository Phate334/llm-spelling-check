# gemma-4-26b-a4b v0.2.3 測試結果

model: `gemma-4-26b-a4b`
base_url: `http://localhost:7072/v1`
candidate_sources: `vllm_top_logprob` only
fim: `removed`
window_radius: `12`
score_batch_size: `1`

測試資料：`data/sample_sentences.json`

## CSC Metrics

```text
detection_precision: 0.1000
detection_recall: 0.6667
detection_f1: 0.1739
correction_precision: 0.2500
correction_recall: 0.1111
correction_f1: 0.1538
false_positive_rate: 0.2700
detected_positions: 60
gold_error_positions: 9
correct_detected_positions: 6
predicted_corrections: 4
gold_corrections: 9
correct_corrections: 1
false_positive_positions: 54
gold_non_error_positions: 200
```

## Pipeline / vLLM Summary

```text
corrected: 4
uncertain: 5
no_error: 3
score_batch_size: 1
score_calls: 147
scored_prompts: 147
prompts_per_call: 1.0000
input_chars: 19129
output_chars: 858375
input_bytes: 23871
output_bytes: 881085
prompt_tokens: 1815
completion_tokens: 147
total_tokens: 1962
```

依用途累計：

```text
{"score_original": 12, "score_window": 135}
```

詳細 vLLM 每次呼叫紀錄：`gemma-4-26b-a4b-window12-calls.jsonl`

## 案例結果

```text
case  status     calls prompts top_candidate
01    uncertain  22    22      公->把 delta=1.315 source=vllm_top_logprob
02    no_error   14    14      -
03    corrected  8     8       提->屜 delta=1.403 source=vllm_top_logprob
04    corrected  15    15      戰->上 delta=1.731 source=vllm_top_logprob
05    uncertain  20    20      寄->搬 delta=0.841 source=vllm_top_logprob
06    corrected  10    10      飯->一 delta=1.341 source=vllm_top_logprob
07    corrected  10    10      汽->子 delta=1.605 source=vllm_top_logprob
08    uncertain  12    12      李->座 delta=0.781 source=vllm_top_logprob
09    uncertain  4     4       不->對 delta=0.353 source=vllm_top_logprob
10    no_error   10    10      -
11    uncertain  21    21      來->說 delta=1.338 source=vllm_top_logprob
12    no_error   1     1       -
```

## vLLM 輸入與輸出紀錄口徑

- 每次呼叫的用途、主要 payload 欄位、回傳重點欄位已寫入 `gemma-4-26b-a4b-window12-calls.jsonl`。
- 本輪不包含 FIM、`structured_outputs` 或 JSON candidate generation。
- `score_calls` 是 `/completions` HTTP request 次數；`scored_prompts` 是送入 scoring 的 prompt 數。
- `input_chars` / `output_chars` 為 JSON request / response 文字長度累計。
- token 統計取自 vLLM OpenAI-compatible completions response 的 `usage` 欄位。

## 詳細案例

### Case 01

- input: 我今天早上喝了一杯咖啡，然後去公圜散步。
- gold: 我今天早上喝了一杯咖啡，然後去公園散步。
- output: 我今天早上喝了一杯咖啡，然後去公圜散步。
- status: `uncertain`
- score_calls / scored_prompts: 22 / 22
- suspicious:
  - 16 圜 risk=22.771 reason=低字元或局部 span likelihood
  - 17 散 risk=18.905 reason=低字元或局部 span likelihood
  - 14 去 risk=16.881 reason=低字元或局部 span likelihood
  - 15 公 risk=15.974 reason=低字元或局部 span likelihood
  - 13 後 risk=14.269 reason=低字元或局部 span likelihood
- top corrections:
  - 15 公->把 delta=1.315 source=vllm_top_logprob
  - 15 公->對 delta=0.978 source=vllm_top_logprob
  - 17 散->兩 delta=0.640 source=vllm_top_logprob

### Case 02

- input: 這份報告需要再檢察一次，避免留下錯字。
- gold: 這份報告需要再檢查一次，避免留下錯字。
- output: 這份報告需要再檢察一次，避免留下錯字。
- status: `no_error`
- score_calls / scored_prompts: 14 / 14
- suspicious:
  - 14 留 risk=21.511 reason=低字元或局部 span likelihood
  - 15 下 risk=21.511 reason=低字元或局部 span likelihood
  - 16 錯 risk=16.536 reason=低字元或局部 span likelihood
  - 9 一 risk=15.602 reason=低字元或局部 span likelihood
  - 10 次 risk=15.602 reason=低字元或局部 span likelihood

### Case 03

- input: 他把鑰匙放在抽提裡，出門前一直找不到。
- gold: 他把鑰匙放在抽屜裡，出門前一直找不到。
- output: 他把鑰匙放在抽屜裡，出門前一直找不到。
- status: `corrected`
- score_calls / scored_prompts: 8 / 8
- suspicious:
  - 7 提 risk=19.818 reason=低字元或局部 span likelihood
  - 2 鑰 risk=18.311 reason=低字元或局部 span likelihood
  - 15 找 risk=18.171 reason=低字元或局部 span likelihood
  - 16 不 risk=18.171 reason=低字元或局部 span likelihood
  - 17 到 risk=18.171 reason=低字元或局部 span likelihood
- top corrections:
  - 7 提->屜 delta=1.403 source=vllm_top_logprob

### Case 04

- input: 我們明天早上在車戰見面，不要遲到。
- gold: 我們明天早上在車站見面，不要遲到。
- output: 我們明天早上在車上見面，不要遲到。
- status: `corrected`
- score_calls / scored_prompts: 15 / 15
- suspicious:
  - 9 見 risk=19.762 reason=低字元或局部 span likelihood
  - 14 遲 risk=19.439 reason=低字元或局部 span likelihood
  - 8 戰 risk=18.527 reason=低字元或局部 span likelihood
  - 2 明 risk=18.242 reason=低字元或局部 span likelihood
  - 3 天 risk=18.242 reason=低字元或局部 span likelihood
- top corrections:
  - 8 戰->上 delta=1.731 source=vllm_top_logprob

### Case 05

- input: 請把會議紀錄寄到我的信相。
- gold: 請把會議紀錄寄到我的信箱。
- output: 請把會議紀錄寄到我的信相。
- status: `uncertain`
- score_calls / scored_prompts: 20 / 20
- suspicious:
  - 4 紀 risk=17.088 reason=低字元或局部 span likelihood
  - 5 錄 risk=17.088 reason=低字元或局部 span likelihood
  - 6 寄 risk=15.665 reason=低字元或局部 span likelihood
  - 3 議 risk=14.841 reason=低字元或局部 span likelihood
  - 2 會 risk=12.595 reason=低字元或局部 span likelihood
- top corrections:
  - 6 寄->搬 delta=0.841 source=vllm_top_logprob
  - 3 議->請 delta=-1.234 source=vllm_top_logprob
  - 6 寄->把 delta=-1.270 source=vllm_top_logprob

### Case 06

- input: 這間飯店的服誤一直都很好。
- gold: 這間飯店的服務一直都很好。
- output: 這間一店的服誤一直都很好。
- status: `corrected`
- score_calls / scored_prompts: 10 / 10
- suspicious:
  - 6 誤 risk=19.291 reason=低字元或局部 span likelihood
  - 2 飯 risk=17.990 reason=低字元或局部 span likelihood
  - 3 店 risk=17.990 reason=低字元或局部 span likelihood
  - 7 一 risk=17.491 reason=低字元或局部 span likelihood
  - 8 直 risk=15.691 reason=低字元或局部 span likelihood
- top corrections:
  - 2 飯->一 delta=1.341 source=vllm_top_logprob

### Case 07

- input: 今天的天汽很好，適合出去走走。
- gold: 今天的天氣很好，適合出去走走。
- output: 今天的天子很好，適合出去走走。
- status: `corrected`
- score_calls / scored_prompts: 10 / 10
- suspicious:
  - 10 出 risk=22.631 reason=低字元或局部 span likelihood
  - 11 去 risk=22.631 reason=低字元或局部 span likelihood
  - 2 的 risk=21.496 reason=低字元或局部 span likelihood
  - 3 天 risk=21.496 reason=低字元或局部 span likelihood
  - 4 汽 risk=19.182 reason=低字元或局部 span likelihood
- top corrections:
  - 4 汽->子 delta=1.605 source=vllm_top_logprob

### Case 08

- input: 這份資料已經整李好了，可以直接送出。
- gold: 這份資料已經整理好了，可以直接送出。
- output: 這份資料已經整李好了，可以直接送出。
- status: `uncertain`
- score_calls / scored_prompts: 12 / 12
- suspicious:
  - 7 李 risk=15.340 reason=低字元或局部 span likelihood
  - 1 份 risk=15.076 reason=低字元或局部 span likelihood
  - 2 資 risk=14.704 reason=低字元或局部 span likelihood
  - 8 好 risk=14.490 reason=低字元或局部 span likelihood
  - 3 料 risk=14.333 reason=低字元或局部 span likelihood
- top corrections:
  - 7 李->座 delta=0.781 source=vllm_top_logprob
  - 8 好->完 delta=0.502 source=vllm_top_logprob
  - 8 好->已 delta=0.489 source=vllm_top_logprob

### Case 09

- input: 老闆提醒大家注意合約的細結，不要看漏。
- gold: 老闆提醒大家注意合約的細節，不要看漏。
- output: 老闆提醒大家注意合約的細結，不要看漏。
- status: `uncertain`
- score_calls / scored_prompts: 4 / 4
- suspicious:
  - 6 注 risk=20.588 reason=低字元或局部 span likelihood
  - 7 意 risk=20.588 reason=低字元或局部 span likelihood
  - 5 家 risk=17.401 reason=低字元或局部 span likelihood
  - 8 合 risk=16.713 reason=低字元或局部 span likelihood
  - 14 不 risk=16.350 reason=低字元或局部 span likelihood
- top corrections:
  - 14 不->對 delta=0.353 source=vllm_top_logprob
  - 14 不->合 delta=0.176 source=vllm_top_logprob

### Case 10

- input: 我想先確認一下這筆費用的金額是否正確。
- gold: 我想先確認一下這筆費用的金額是否正確。
- output: 我想先確認一下這筆費用的金額是否正確。
- status: `no_error`
- score_calls / scored_prompts: 10 / 10
- suspicious:
  - 3 確 risk=16.818 reason=低字元或局部 span likelihood
  - 4 認 risk=16.818 reason=低字元或局部 span likelihood
  - 5 一 risk=14.433 reason=低字元或局部 span likelihood
  - 2 先 risk=13.986 reason=低字元或局部 span likelihood
  - 9 費 risk=13.348 reason=低字元或局部 span likelihood

### Case 11

- input: 這家餐廳的牛肉麵很好吃，我下次還想再來。
- gold: 這家餐廳的牛肉麵很好吃，我下次還想再來。
- output: 這家餐廳的牛肉麵很好吃，我下次還想再來。
- status: `uncertain`
- score_calls / scored_prompts: 21 / 21
- suspicious:
  - 17 再 risk=18.115 reason=低字元或局部 span likelihood
  - 18 來 risk=18.115 reason=低字元或局部 span likelihood
  - 5 牛 risk=16.570 reason=低字元或局部 span likelihood
  - 6 肉 risk=16.570 reason=低字元或局部 span likelihood
  - 7 麵 risk=16.235 reason=低字元或局部 span likelihood
- top corrections:
  - 18 來->說 delta=1.338 source=vllm_top_logprob
  - 18 來->這 delta=1.281 source=vllm_top_logprob
  - 5 牛->家 delta=0.810 source=vllm_top_logprob

### Case 12

- input: 今天下午可能會下雨，出門記得帶傘。
- gold: 今天下午可能會下雨，出門記得帶傘。
- output: 今天下午可能會下雨，出門記得帶傘。
- status: `no_error`
- score_calls / scored_prompts: 1 / 1
- suspicious:
  - 2 下 risk=18.935 reason=低字元或局部 span likelihood
  - 3 午 risk=18.935 reason=低字元或局部 span likelihood
  - 4 可 risk=18.525 reason=低字元或局部 span likelihood
  - 5 能 risk=18.115 reason=低字元或局部 span likelihood
  - 6 會 risk=18.115 reason=低字元或局部 span likelihood
