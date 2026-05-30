# google/gemma-3-270m v0.2.3 測試結果

model: `google/gemma-3-270m`
base_url: `http://localhost:8001/v1`
candidate_sources: `vllm_top_logprob` only
fim: `removed`
window_radius: `12`
score_batch_size: `1`

測試資料：`data/sample_sentences.json`

## CSC Metrics

```text
detection_precision: 0.1525
detection_recall: 1.0000
detection_f1: 0.2647
correction_precision: 0.0000
correction_recall: 0.0000
correction_f1: 0.0000
false_positive_rate: 0.2500
detected_positions: 59
gold_error_positions: 9
correct_detected_positions: 9
predicted_corrections: 0
gold_corrections: 9
correct_corrections: 0
false_positive_positions: 50
gold_non_error_positions: 200
```

## Pipeline / vLLM Summary

```text
corrected: 0
uncertain: 9
no_error: 3
score_batch_size: 1
score_calls: 188
scored_prompts: 188
prompts_per_call: 1.0000
input_chars: 25297
output_chars: 1135652
input_bytes: 31523
output_bytes: 1167164
prompt_tokens: 2518
completion_tokens: 188
total_tokens: 2706
```

依用途累計：

```text
{"score_original": 12, "score_window": 176}
```

詳細 vLLM 每次呼叫紀錄：`google-gemma-3-270m-window12-calls.jsonl`

## 案例結果

```text
case  status     calls prompts top_candidate
01    uncertain 21    21      圜->館 delta=1.041 source=vllm_top_logprob
02    uncertain 20    20      察->索 delta=0.807 source=vllm_top_logprob
03    uncertain 17    17      提->屜 delta=1.194 source=vllm_top_logprob
04    uncertain 15    15      戰->上 delta=1.168 source=vllm_top_logprob
05    uncertain 12    12      相->箱 delta=1.154 source=vllm_top_logprob
06    uncertain 13    13      誤->裝 delta=1.634 source=vllm_top_logprob
07    uncertain 21    21      汽->氣 delta=1.854 source=vllm_top_logprob
08    uncertain 21    21      李->個 delta=1.294 source=vllm_top_logprob
09    uncertain 14    14      結->節 delta=0.748 source=vllm_top_logprob
10    no_error  16    16      -
11    no_error  12    12      -
12    no_error  6     6       -
```

## vLLM 輸入與輸出紀錄口徑

- 每次呼叫的用途、主要 payload 欄位、回傳重點欄位已寫入 `google-gemma-3-270m-window12-calls.jsonl`。
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
- score_calls / scored_prompts: 21 / 21
- suspicious:
  - 16 圜 risk=18.240 reason=低字元或局部 span likelihood
  - 15 公 risk=13.613 reason=低字元或局部 span likelihood
  - 17 散 risk=13.155 reason=低字元或局部 span likelihood
  - 14 去 risk=10.448 reason=低字元或局部 span likelihood
  - 0 我 risk=9.934 reason=低字元或局部 span likelihood
- top corrections:
  - 16 圜->館 delta=1.041 source=vllm_top_logprob
  - 16 圜->廁 delta=0.985 source=vllm_top_logprob
  - 16 圜->車 delta=0.955 source=vllm_top_logprob

### Case 02

- input: 這份報告需要再檢察一次，避免留下錯字。
- gold: 這份報告需要再檢查一次，避免留下錯字。
- output: 這份報告需要再檢察一次，避免留下錯字。
- status: `uncertain`
- score_calls / scored_prompts: 20 / 20
- suspicious:
  - 0 這 risk=13.200 reason=低字元或局部 span likelihood
  - 8 察 risk=9.240 reason=低字元或局部 span likelihood
  - 9 一 risk=9.124 reason=低字元或局部 span likelihood
  - 10 次 risk=9.008 reason=低字元或局部 span likelihood
  - 1 份 risk=8.436 reason=低字元或局部 span likelihood
- top corrections:
  - 8 察->索 delta=0.807 source=vllm_top_logprob
  - 8 察->視 delta=0.713 source=vllm_top_logprob
  - 8 察->討 delta=0.684 source=vllm_top_logprob

### Case 03

- input: 他把鑰匙放在抽提裡，出門前一直找不到。
- gold: 他把鑰匙放在抽屜裡，出門前一直找不到。
- output: 他把鑰匙放在抽提裡，出門前一直找不到。
- status: `uncertain`
- score_calls / scored_prompts: 17 / 17
- suspicious:
  - 0 他 risk=14.872 reason=低字元或局部 span likelihood
  - 7 提 risk=14.613 reason=低字元或局部 span likelihood
  - 8 裡 risk=11.537 reason=低字元或局部 span likelihood
  - 6 抽 risk=10.966 reason=低字元或局部 span likelihood
  - 2 鑰 risk=10.721 reason=低字元或局部 span likelihood
- top corrections:
  - 7 提->屜 delta=1.194 source=vllm_top_logprob
  - 7 提->屉 delta=0.985 source=vllm_top_logprob
  - 6 抽->手 delta=0.885 source=vllm_top_logprob

### Case 04

- input: 我們明天早上在車戰見面，不要遲到。
- gold: 我們明天早上在車站見面，不要遲到。
- output: 我們明天早上在車戰見面，不要遲到。
- status: `uncertain`
- score_calls / scored_prompts: 15 / 15
- suspicious:
  - 0 我 risk=15.067 reason=低字元或局部 span likelihood
  - 1 們 risk=15.067 reason=低字元或局部 span likelihood
  - 8 戰 risk=14.350 reason=低字元或局部 span likelihood
  - 9 見 risk=12.934 reason=低字元或局部 span likelihood
  - 2 明 risk=12.194 reason=低字元或局部 span likelihood
- top corrections:
  - 8 戰->上 delta=1.168 source=vllm_top_logprob
  - 8 戰->內 delta=1.032 source=vllm_top_logprob
  - 8 戰->庫 delta=0.907 source=vllm_top_logprob

### Case 05

- input: 請把會議紀錄寄到我的信相。
- gold: 請把會議紀錄寄到我的信箱。
- output: 請把會議紀錄寄到我的信相。
- status: `uncertain`
- score_calls / scored_prompts: 12 / 12
- suspicious:
  - 11 相 risk=15.252 reason=低字元或局部 span likelihood
  - 0 請 risk=14.919 reason=低字元或局部 span likelihood
  - 2 會 risk=14.309 reason=低字元或局部 span likelihood
  - 3 議 risk=14.309 reason=低字元或局部 span likelihood
  - 1 把 risk=10.889 reason=低字元或局部 span likelihood
- top corrections:
  - 11 相->箱 delta=1.154 source=vllm_top_logprob
  - 11 相->中 delta=0.761 source=vllm_top_logprob
  - 11 相->札 delta=0.750 source=vllm_top_logprob

### Case 06

- input: 這間飯店的服誤一直都很好。
- gold: 這間飯店的服務一直都很好。
- output: 這間飯店的服誤一直都很好。
- status: `uncertain`
- score_calls / scored_prompts: 13 / 13
- suspicious:
  - 6 誤 risk=18.346 reason=低字元或局部 span likelihood
  - 5 服 risk=14.356 reason=低字元或局部 span likelihood
  - 0 這 risk=13.200 reason=低字元或局部 span likelihood
  - 7 一 risk=13.096 reason=低字元或局部 span likelihood
  - 4 的 risk=10.532 reason=低字元或局部 span likelihood
- top corrections:
  - 6 誤->裝 delta=1.634 source=vllm_top_logprob
  - 6 誤->飾 delta=1.516 source=vllm_top_logprob
  - 6 誤->侍 delta=1.473 source=vllm_top_logprob

### Case 07

- input: 今天的天汽很好，適合出去走走。
- gold: 今天的天氣很好，適合出去走走。
- output: 今天的天汽很好，適合出去走走。
- status: `uncertain`
- score_calls / scored_prompts: 21 / 21
- suspicious:
  - 5 很 risk=14.006 reason=低字元或局部 span likelihood
  - 6 好 risk=14.006 reason=低字元或局部 span likelihood
  - 4 汽 risk=12.831 reason=低字元或局部 span likelihood
  - 3 天 risk=11.354 reason=低字元或局部 span likelihood
  - 8 適 risk=11.254 reason=低字元或局部 span likelihood
- top corrections:
  - 4 汽->氣 delta=1.854 source=vllm_top_logprob
  - 4 汽->气 delta=1.701 source=vllm_top_logprob
  - 4 汽->色 delta=1.358 source=vllm_top_logprob

### Case 08

- input: 這份資料已經整李好了，可以直接送出。
- gold: 這份資料已經整理好了，可以直接送出。
- output: 這份資料已經整李好了，可以直接送出。
- status: `uncertain`
- score_calls / scored_prompts: 21 / 21
- suspicious:
  - 7 李 risk=15.188 reason=低字元或局部 span likelihood
  - 8 好 risk=14.545 reason=低字元或局部 span likelihood
  - 9 了 risk=13.902 reason=低字元或局部 span likelihood
  - 0 這 risk=13.200 reason=低字元或局部 span likelihood
  - 6 整 risk=12.909 reason=低字元或局部 span likelihood
- top corrections:
  - 7 李->個 delta=1.294 source=vllm_top_logprob
  - 7 李->整 delta=1.187 source=vllm_top_logprob
  - 7 李->晚 delta=1.076 source=vllm_top_logprob

### Case 09

- input: 老闆提醒大家注意合約的細結，不要看漏。
- gold: 老闆提醒大家注意合約的細節，不要看漏。
- output: 老闆提醒大家注意合約的細結，不要看漏。
- status: `uncertain`
- score_calls / scored_prompts: 14 / 14
- suspicious:
  - 0 老 risk=19.122 reason=低字元或局部 span likelihood
  - 1 闆 risk=19.122 reason=低字元或局部 span likelihood
  - 12 結 risk=14.545 reason=低字元或局部 span likelihood
  - 2 提 risk=14.203 reason=低字元或局部 span likelihood
  - 11 細 risk=9.592 reason=低字元或局部 span likelihood
- top corrections:
  - 12 結->節 delta=0.748 source=vllm_top_logprob
  - 11 細->簽 delta=0.481 source=vllm_top_logprob
  - 12 結->面 delta=0.381 source=vllm_top_logprob

### Case 10

- input: 我想先確認一下這筆費用的金額是否正確。
- gold: 我想先確認一下這筆費用的金額是否正確。
- output: 我想先確認一下這筆費用的金額是否正確。
- status: `no_error`
- score_calls / scored_prompts: 16 / 16
- suspicious:
  - 0 我 risk=15.840 reason=低字元或局部 span likelihood
  - 1 想 risk=15.840 reason=低字元或局部 span likelihood
  - 2 先 risk=10.455 reason=低字元或局部 span likelihood
  - 3 確 risk=9.792 reason=低字元或局部 span likelihood
  - 4 認 risk=8.466 reason=低字元或局部 span likelihood

### Case 11

- input: 這家餐廳的牛肉麵很好吃，我下次還想再來。
- gold: 這家餐廳的牛肉麵很好吃，我下次還想再來。
- output: 這家餐廳的牛肉麵很好吃，我下次還想再來。
- status: `no_error`
- score_calls / scored_prompts: 12 / 12
- suspicious:
  - 0 這 risk=13.200 reason=低字元或局部 span likelihood
  - 1 家 risk=8.998 reason=低字元或局部 span likelihood
  - 13 下 risk=7.740 reason=低字元或局部 span likelihood
  - 14 次 risk=7.740 reason=低字元或局部 span likelihood

### Case 12

- input: 今天下午可能會下雨，出門記得帶傘。
- gold: 今天下午可能會下雨，出門記得帶傘。
- output: 今天下午可能會下雨，出門記得帶傘。
- status: `no_error`
- score_calls / scored_prompts: 6 / 6
- suspicious:
  - 4 可 risk=17.988 reason=低字元或局部 span likelihood
  - 5 能 risk=17.988 reason=低字元或局部 span likelihood
  - 6 會 risk=17.988 reason=低字元或局部 span likelihood
  - 7 下 risk=11.995 reason=低字元或局部 span likelihood
  - 0 今 risk=11.247 reason=低字元或局部 span likelihood
