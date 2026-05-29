# gemma-4-26b-a4b v0.2.2 FIM Structured Outputs 測試結果

model: `gemma-4-26b-a4b`
base_url: `http://localhost:7072/v1`
window_radius: `12`
fim_candidate_limit: `8`

測試資料：`data/sample_sentences.json`

## 結果摘要

```text
corrected: 3
uncertain: 5
no_error: 4
ok: 2
wrong: 2
missed: 3
eval_uncertain: 5
calls: 228
input_chars: 48573
output_chars: 1033130
input_bytes: 74055
output_bytes: 1073168
prompt_tokens: 10019
completion_tokens: 5928
total_tokens: 15947
```

依用途累計：

```text
{"score_original": 12, "fim_candidates": 60, "score_window": 156}
```

詳細 vLLM 每次呼叫紀錄：`gemma-4-26b-a4b-window12-calls.jsonl`

## 案例結果

```text
case  status     eval      calls top_candidate
01    corrected  wrong     25    圜->理 delta=1.230 source=vllm_top_logprob
02    uncertain  uncertain 23    察->入 delta=0.573 source=vllm_top_logprob
03    corrected  ok        13    提->屜 delta=2.488 source=vllm_top_logprob
04    corrected  wrong     24    戰->的 delta=2.324 source=vllm_top_logprob
05    no_error   missed    25    -
06    no_error   missed    14    -
07    no_error   missed    16    -
08    uncertain  uncertain 24    送->用 delta=0.549 source=vllm_top_logprob
09    uncertain  uncertain 14    不->合 delta=0.549 source=vllm_top_logprob
10    uncertain  uncertain 16    筆->對 delta=1.150 source=vllm_top_logprob
11    uncertain  uncertain 28    肉->家 delta=1.417 source=vllm_top_logprob
12    no_error   ok        6     -
```

## vLLM 輸入與輸出紀錄口徑

- 每次呼叫的用途、主要 payload 欄位、回傳重點欄位已寫入 `gemma-4-26b-a4b-window12-calls.jsonl`。
- `input_chars` / `output_chars` 為 JSON request / response 文字長度累計。
- `input_bytes` / `output_bytes` 為 UTF-8 request / response byte 數累計。
- token 統計取自 vLLM OpenAI-compatible completions response 的 `usage` 欄位。
- `fim_candidates` 呼叫的 payload 會包含 `structured_outputs=true`。

## 詳細案例

### Case 01

- input: 我今天早上喝了一杯咖啡，然後去公圜散步。
- expected: 我今天早上喝了一杯咖啡，然後去公園散步。
- status/eval: `corrected` / `wrong`
- corrected_text: 我今天早上喝了一杯咖啡，然後去公理散步。
- calls: 25
- suspicious:
  - 16 圜 risk=21.198 reason=低字元或局部 span likelihood
  - 17 散 risk=19.465 reason=低字元或局部 span likelihood
  - 14 去 risk=16.733 reason=低字元或局部 span likelihood
  - 15 公 risk=15.736 reason=低字元或局部 span likelihood
  - 13 後 risk=14.081 reason=低字元或局部 span likelihood
- top corrections:
  - 16 圜->理 delta=1.230 source=vllm_top_logprob

### Case 02

- input: 這份報告需要再檢察一次，避免留下錯字。
- expected: 這份報告需要再檢查一次，避免留下錯字。
- status/eval: `uncertain` / `uncertain`
- corrected_text: -
- calls: 23
- suspicious:
  - 9 一 risk=17.942 reason=低字元或局部 span likelihood
  - 10 次 risk=17.942 reason=低字元或局部 span likelihood
  - 8 察 risk=17.746 reason=低字元或局部 span likelihood
  - 7 檢 risk=14.643 reason=低字元或局部 span likelihood
  - 14 留 risk=12.757 reason=低字元或局部 span likelihood
- top corrections:
  - 8 察->入 delta=0.573 source=vllm_top_logprob
  - 8 察->份 delta=0.404 source=vllm_top_logprob
  - 8 察->房 delta=0.113 source=vllm_top_logprob

### Case 03

- input: 他把鑰匙放在抽提裡，出門前一直找不到。
- expected: 他把鑰匙放在抽屜裡，出門前一直找不到。
- status/eval: `corrected` / `ok`
- corrected_text: 他把鑰匙放在抽屜裡，出門前一直找不到。
- calls: 13
- suspicious:
  - 7 提 risk=19.742 reason=低字元或局部 span likelihood
  - 15 找 risk=18.497 reason=低字元或局部 span likelihood
  - 16 不 risk=18.497 reason=低字元或局部 span likelihood
  - 17 到 risk=18.497 reason=低字元或局部 span likelihood
  - 2 鑰 risk=18.038 reason=低字元或局部 span likelihood
- top corrections:
  - 7 提->屜 delta=2.488 source=vllm_top_logprob

### Case 04

- input: 我們明天早上在車戰見面，不要遲到。
- expected: 我們明天早上在車站見面，不要遲到。
- status/eval: `corrected` / `wrong`
- corrected_text: 我們明天早上在車的見面，不要遲到。
- calls: 24
- suspicious:
  - 9 見 risk=19.807 reason=低字元或局部 span likelihood
  - 14 遲 risk=19.345 reason=低字元或局部 span likelihood
  - 8 戰 risk=18.243 reason=低字元或局部 span likelihood
  - 7 車 risk=18.053 reason=低字元或局部 span likelihood
  - 2 明 risk=16.526 reason=低字元或局部 span likelihood
- top corrections:
  - 8 戰->的 delta=2.324 source=vllm_top_logprob

### Case 05

- input: 請把會議紀錄寄到我的信相。
- expected: 請把會議紀錄寄到我的信箱。
- status/eval: `no_error` / `missed`
- corrected_text: 請把會議紀錄寄到我的信相。
- calls: 25
- suspicious:
  - 4 紀 risk=16.374 reason=低字元或局部 span likelihood
  - 5 錄 risk=16.374 reason=低字元或局部 span likelihood
  - 6 寄 risk=15.566 reason=低字元或局部 span likelihood
  - 3 議 risk=14.486 reason=低字元或局部 span likelihood
  - 2 會 risk=12.599 reason=低字元或局部 span likelihood

### Case 06

- input: 這間飯店的服誤一直都很好。
- expected: 這間飯店的服務一直都很好。
- status/eval: `no_error` / `missed`
- corrected_text: 這間飯店的服誤一直都很好。
- calls: 14
- suspicious:
  - 6 誤 risk=18.969 reason=低字元或局部 span likelihood
  - 2 飯 risk=18.002 reason=低字元或局部 span likelihood
  - 3 店 risk=18.002 reason=低字元或局部 span likelihood
  - 1 間 risk=15.965 reason=低字元或局部 span likelihood
  - 7 一 risk=15.578 reason=低字元或局部 span likelihood

### Case 07

- input: 今天的天汽很好，適合出去走走。
- expected: 今天的天氣很好，適合出去走走。
- status/eval: `no_error` / `missed`
- corrected_text: 今天的天汽很好，適合出去走走。
- calls: 16
- suspicious:
  - 10 出 risk=22.253 reason=低字元或局部 span likelihood
  - 11 去 risk=22.253 reason=低字元或局部 span likelihood
  - 2 的 risk=21.657 reason=低字元或局部 span likelihood
  - 3 天 risk=21.657 reason=低字元或局部 span likelihood
  - 9 合 risk=19.666 reason=低字元或局部 span likelihood

### Case 08

- input: 這份資料已經整李好了，可以直接送出。
- expected: 這份資料已經整理好了，可以直接送出。
- status/eval: `uncertain` / `uncertain`
- corrected_text: -
- calls: 24
- suspicious:
  - 7 李 risk=14.445 reason=低字元或局部 span likelihood
  - 8 好 risk=13.164 reason=低字元或局部 span likelihood
  - 15 送 risk=12.829 reason=低字元或局部 span likelihood
  - 1 份 risk=12.126 reason=低字元或局部 span likelihood
  - 9 了 risk=11.884 reason=低字元或局部 span likelihood
- top corrections:
  - 15 送->用 delta=0.549 source=vllm_top_logprob
  - 7 李->份 delta=0.395 source=vllm_top_logprob
  - 8 好->已 delta=0.331 source=vllm_top_logprob

### Case 09

- input: 老闆提醒大家注意合約的細結，不要看漏。
- expected: 老闆提醒大家注意合約的細節，不要看漏。
- status/eval: `uncertain` / `uncertain`
- corrected_text: -
- calls: 14
- suspicious:
  - 6 注 risk=19.952 reason=低字元或局部 span likelihood
  - 7 意 risk=19.952 reason=低字元或局部 span likelihood
  - 14 不 risk=17.960 reason=低字元或局部 span likelihood
  - 15 要 risk=17.960 reason=低字元或局部 span likelihood
  - 5 家 risk=17.027 reason=低字元或局部 span likelihood
- top corrections:
  - 14 不->合 delta=0.549 source=vllm_top_logprob
  - 14 不->把 delta=0.457 source=vllm_top_logprob
  - 14 不->對 delta=-0.047 source=vllm_top_logprob

### Case 10

- input: 我想先確認一下這筆費用的金額是否正確。
- expected: 我想先確認一下這筆費用的金額是否正確。
- status/eval: `uncertain` / `uncertain`
- corrected_text: -
- calls: 16
- suspicious:
  - 3 確 risk=14.491 reason=低字元或局部 span likelihood
  - 4 認 risk=14.491 reason=低字元或局部 span likelihood
  - 8 筆 risk=13.827 reason=低字元或局部 span likelihood
  - 9 費 risk=13.823 reason=低字元或局部 span likelihood
  - 14 是 risk=13.225 reason=低字元或局部 span likelihood
- top corrections:
  - 8 筆->對 delta=1.150 source=vllm_top_logprob
  - 8 筆->兩 delta=0.840 source=vllm_top_logprob
  - 8 筆->來 delta=0.739 source=vllm_top_logprob

### Case 11

- input: 這家餐廳的牛肉麵很好吃，我下次還想再來。
- expected: 這家餐廳的牛肉麵很好吃，我下次還想再來。
- status/eval: `uncertain` / `uncertain`
- corrected_text: -
- calls: 28
- suspicious:
  - 7 麵 risk=25.058 reason=低字元或局部 span likelihood
  - 6 肉 risk=21.196 reason=低字元或局部 span likelihood
  - 8 很 risk=19.978 reason=低字元或局部 span likelihood
  - 17 再 risk=18.253 reason=低字元或局部 span likelihood
  - 18 來 risk=18.253 reason=低字元或局部 span likelihood
- top corrections:
  - 6 肉->家 delta=1.417 source=vllm_top_logprob
  - 7 麵->的 delta=1.202 source=vllm_top_logprob
  - 18 來->說 delta=1.128 source=vllm_top_logprob

### Case 12

- input: 今天下午可能會下雨，出門記得帶傘。
- expected: 今天下午可能會下雨，出門記得帶傘。
- status/eval: `no_error` / `ok`
- corrected_text: 今天下午可能會下雨，出門記得帶傘。
- calls: 6
- suspicious:
  - 2 下 risk=18.723 reason=低字元或局部 span likelihood
  - 3 午 risk=18.723 reason=低字元或局部 span likelihood
  - 4 可 risk=18.385 reason=低字元或局部 span likelihood
  - 5 能 risk=18.047 reason=低字元或局部 span likelihood
  - 6 會 risk=18.047 reason=低字元或局部 span likelihood
