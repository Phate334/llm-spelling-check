# gemma-4-26b-a4b v0.2.2 No-FIM 測試結果

model: `gemma-4-26b-a4b`
base_url: `http://localhost:7072/v1`
window_radius: `12`
fim_candidate_limit: `0`
candidate_sources: `vllm_top_logprob` only

測試資料：`data/sample_sentences.json`

## 結果摘要

```text
corrected: 4
uncertain: 5
no_error: 3
eval_ok: 3
eval_wrong: 3
eval_missed: 1
eval_uncertain: 5
calls: 159
input_chars: 20702
output_chars: 928889
input_bytes: 25854
output_bytes: 953495
prompt_tokens: 1964
completion_tokens: 159
total_tokens: 2123
```

依用途累計：

```text
{"score_original": 12, "score_window": 147}
```

詳細 vLLM 每次呼叫紀錄：`gemma-4-26b-a4b-window12-no-fim-calls.jsonl`

## 案例結果

```text
case  status     eval      calls top_candidate
01    uncertain  uncertain 21    公->會 delta=1.442 source=vllm_top_logprob
02    no_error   missed    14    -
03    corrected  ok        8     提->屜 delta=1.484 source=vllm_top_logprob
04    corrected  wrong     15    戰->上 delta=1.737 source=vllm_top_logprob
05    uncertain  uncertain 20    寄->搬 delta=0.931 source=vllm_top_logprob
06    corrected  wrong     11    飯->一 delta=1.287 source=vllm_top_logprob
07    corrected  wrong     10    汽->子 delta=1.593 source=vllm_top_logprob
08    uncertain  uncertain 13    李->器 delta=0.930 source=vllm_top_logprob
09    uncertain  uncertain 4     不->合 delta=0.832 source=vllm_top_logprob
10    no_error   ok        16    -
11    uncertain  uncertain 26    來->說 delta=1.477 source=vllm_top_logprob
12    no_error   ok        1     -
```

## vLLM 輸入與輸出紀錄口徑

- 每次呼叫的用途、主要 payload 欄位、回傳重點欄位已寫入 `gemma-4-26b-a4b-window12-no-fim-calls.jsonl`。
- `input_chars` / `output_chars` 為 JSON request / response 文字長度累計。
- `input_bytes` / `output_bytes` 為 UTF-8 request / response byte 數累計。
- token 統計取自 vLLM OpenAI-compatible completions response 的 `usage` 欄位。
- 本輪未呼叫 `fim_candidates`，也未送出 `structured_outputs` payload。

## 詳細案例

### Case 01

- input: 我今天早上喝了一杯咖啡，然後去公圜散步。
- expected: 我今天早上喝了一杯咖啡，然後去公園散步。
- status/eval: `uncertain` / `uncertain`
- corrected_text: -
- calls: 21
- suspicious:
  - 16 圜 risk=22.710 reason=低字元或局部 span likelihood
  - 17 散 risk=19.030 reason=低字元或局部 span likelihood
  - 14 去 risk=16.726 reason=低字元或局部 span likelihood
  - 15 公 risk=15.682 reason=低字元或局部 span likelihood
  - 13 後 risk=14.258 reason=低字元或局部 span likelihood
- top corrections:
  - 15 公->會 delta=1.442 source=vllm_top_logprob
  - 15 公->把 delta=1.274 source=vllm_top_logprob
  - 15 公->後 delta=0.835 source=vllm_top_logprob

### Case 02

- input: 這份報告需要再檢察一次，避免留下錯字。
- expected: 這份報告需要再檢查一次，避免留下錯字。
- status/eval: `no_error` / `missed`
- corrected_text: 這份報告需要再檢察一次，避免留下錯字。
- calls: 14
- suspicious:
  - 14 留 risk=21.510 reason=低字元或局部 span likelihood
  - 15 下 risk=21.510 reason=低字元或局部 span likelihood
  - 16 錯 risk=16.570 reason=低字元或局部 span likelihood
  - 9 一 risk=15.704 reason=低字元或局部 span likelihood
  - 10 次 risk=15.704 reason=低字元或局部 span likelihood

### Case 03

- input: 他把鑰匙放在抽提裡，出門前一直找不到。
- expected: 他把鑰匙放在抽屜裡，出門前一直找不到。
- status/eval: `corrected` / `ok`
- corrected_text: 他把鑰匙放在抽屜裡，出門前一直找不到。
- calls: 8
- suspicious:
  - 7 提 risk=19.844 reason=低字元或局部 span likelihood
  - 2 鑰 risk=18.287 reason=低字元或局部 span likelihood
  - 15 找 risk=18.173 reason=低字元或局部 span likelihood
  - 16 不 risk=18.173 reason=低字元或局部 span likelihood
  - 17 到 risk=18.173 reason=低字元或局部 span likelihood
- top corrections:
  - 7 提->屜 delta=1.484 source=vllm_top_logprob

### Case 04

- input: 我們明天早上在車戰見面，不要遲到。
- expected: 我們明天早上在車站見面，不要遲到。
- status/eval: `corrected` / `wrong`
- corrected_text: 我們明天早上在車上見面，不要遲到。
- calls: 15
- suspicious:
  - 9 見 risk=19.712 reason=低字元或局部 span likelihood
  - 14 遲 risk=19.346 reason=低字元或局部 span likelihood
  - 8 戰 risk=18.502 reason=低字元或局部 span likelihood
  - 2 明 risk=18.242 reason=低字元或局部 span likelihood
  - 3 天 risk=18.242 reason=低字元或局部 span likelihood
- top corrections:
  - 8 戰->上 delta=1.737 source=vllm_top_logprob

### Case 05

- input: 請把會議紀錄寄到我的信相。
- expected: 請把會議紀錄寄到我的信箱。
- status/eval: `uncertain` / `uncertain`
- corrected_text: -
- calls: 20
- suspicious:
  - 4 紀 risk=17.088 reason=低字元或局部 span likelihood
  - 5 錄 risk=17.088 reason=低字元或局部 span likelihood
  - 6 寄 risk=15.665 reason=低字元或局部 span likelihood
  - 3 議 risk=14.841 reason=低字元或局部 span likelihood
  - 2 會 risk=12.595 reason=低字元或局部 span likelihood
- top corrections:
  - 6 寄->搬 delta=0.931 source=vllm_top_logprob
  - 3 議->請 delta=-1.216 source=vllm_top_logprob
  - 2 會->正 delta=-1.267 source=vllm_top_logprob

### Case 06

- input: 這間飯店的服誤一直都很好。
- expected: 這間飯店的服務一直都很好。
- status/eval: `corrected` / `wrong`
- corrected_text: 這間一店的服誤一直都很好。
- calls: 11
- suspicious:
  - 6 誤 risk=19.530 reason=低字元或局部 span likelihood
  - 2 飯 risk=18.141 reason=低字元或局部 span likelihood
  - 3 店 risk=18.141 reason=低字元或局部 span likelihood
  - 7 一 risk=17.512 reason=低字元或局部 span likelihood
  - 10 很 risk=15.653 reason=低字元或局部 span likelihood
- top corrections:
  - 2 飯->一 delta=1.287 source=vllm_top_logprob

### Case 07

- input: 今天的天汽很好，適合出去走走。
- expected: 今天的天氣很好，適合出去走走。
- status/eval: `corrected` / `wrong`
- corrected_text: 今天的天子很好，適合出去走走。
- calls: 10
- suspicious:
  - 10 出 risk=22.630 reason=低字元或局部 span likelihood
  - 11 去 risk=22.630 reason=低字元或局部 span likelihood
  - 2 的 risk=21.496 reason=低字元或局部 span likelihood
  - 3 天 risk=21.496 reason=低字元或局部 span likelihood
  - 4 汽 risk=19.182 reason=低字元或局部 span likelihood
- top corrections:
  - 4 汽->子 delta=1.593 source=vllm_top_logprob

### Case 08

- input: 這份資料已經整李好了，可以直接送出。
- expected: 這份資料已經整理好了，可以直接送出。
- status/eval: `uncertain` / `uncertain`
- corrected_text: -
- calls: 13
- suspicious:
  - 1 份 risk=15.647 reason=低字元或局部 span likelihood
  - 7 李 risk=15.183 reason=低字元或局部 span likelihood
  - 2 資 risk=15.070 reason=低字元或局部 span likelihood
  - 8 好 risk=14.569 reason=低字元或局部 span likelihood
  - 3 料 risk=14.493 reason=低字元或局部 span likelihood
- top corrections:
  - 7 李->器 delta=0.930 source=vllm_top_logprob
  - 7 李->座 delta=0.900 source=vllm_top_logprob
  - 8 好->已 delta=0.527 source=vllm_top_logprob

### Case 09

- input: 老闆提醒大家注意合約的細結，不要看漏。
- expected: 老闆提醒大家注意合約的細節，不要看漏。
- status/eval: `uncertain` / `uncertain`
- corrected_text: -
- calls: 4
- suspicious:
  - 6 注 risk=20.587 reason=低字元或局部 span likelihood
  - 7 意 risk=20.587 reason=低字元或局部 span likelihood
  - 5 家 risk=17.461 reason=低字元或局部 span likelihood
  - 8 合 risk=16.687 reason=低字元或局部 span likelihood
  - 14 不 risk=16.478 reason=低字元或局部 span likelihood
- top corrections:
  - 14 不->合 delta=0.832 source=vllm_top_logprob
  - 14 不->對 delta=0.329 source=vllm_top_logprob

### Case 10

- input: 我想先確認一下這筆費用的金額是否正確。
- expected: 我想先確認一下這筆費用的金額是否正確。
- status/eval: `no_error` / `ok`
- corrected_text: 我想先確認一下這筆費用的金額是否正確。
- calls: 16
- suspicious:
  - 3 確 risk=15.478 reason=低字元或局部 span likelihood
  - 4 認 risk=15.478 reason=低字元或局部 span likelihood
  - 9 費 risk=13.778 reason=低字元或局部 span likelihood
  - 5 一 risk=13.690 reason=低字元或局部 span likelihood
  - 2 先 risk=13.242 reason=低字元或局部 span likelihood

### Case 11

- input: 這家餐廳的牛肉麵很好吃，我下次還想再來。
- expected: 這家餐廳的牛肉麵很好吃，我下次還想再來。
- status/eval: `uncertain` / `uncertain`
- corrected_text: -
- calls: 26
- suspicious:
  - 17 再 risk=18.375 reason=低字元或局部 span likelihood
  - 18 來 risk=18.375 reason=低字元或局部 span likelihood
  - 5 牛 risk=16.645 reason=低字元或局部 span likelihood
  - 6 肉 risk=16.645 reason=低字元或局部 span likelihood
  - 7 麵 risk=16.539 reason=低字元或局部 span likelihood
- top corrections:
  - 18 來->說 delta=1.477 source=vllm_top_logprob
  - 18 來->去 delta=1.369 source=vllm_top_logprob
  - 18 來->這 delta=0.954 source=vllm_top_logprob

### Case 12

- input: 今天下午可能會下雨，出門記得帶傘。
- expected: 今天下午可能會下雨，出門記得帶傘。
- status/eval: `no_error` / `ok`
- corrected_text: 今天下午可能會下雨，出門記得帶傘。
- calls: 1
- suspicious:
  - 2 下 risk=18.935 reason=低字元或局部 span likelihood
  - 3 午 risk=18.935 reason=低字元或局部 span likelihood
  - 4 可 risk=18.525 reason=低字元或局部 span likelihood
  - 5 能 risk=18.115 reason=低字元或局部 span likelihood
  - 6 會 risk=18.115 reason=低字元或局部 span likelihood
