# google/gemma-4-E2B v0.2.0 無查表測試結果

日期：2026-05-29

```text
corrected: 1
uncertain: 8
no_error: 3
vLLM calls: 159
```

## 每筆結果

```text
case  status      calls  top_candidate
01    uncertain   24     圜->廁 delta=1.030 source=vllm_top_logprob
02    uncertain   21     察->視 delta=0.333 source=vllm_top_logprob
03    uncertain   18     提->屜 delta=1.160 source=vllm_top_logprob
04    uncertain   11     戰->上 delta=0.853 source=vllm_top_logprob
05    corrected   11     相->箱 delta=1.469 source=vllm_top_logprob
06    uncertain   9      誤->侍 delta=1.104 source=vllm_top_logprob
07    uncertain   17     汽->氣 delta=1.420 source=vllm_top_logprob
08    uncertain   17     李->頓 delta=0.751 source=vllm_top_logprob
09    uncertain   11     結->節 delta=0.758 source=vllm_top_logprob
10    no_error    9      -
11    no_error    1      -
12    no_error    10     -
```

## 與 v0.1.0 比較

v0.1.0 是 corrected 3、uncertain 7、no_error 2、calls 202。

v0.2.0 無查表後 corrected 降到 1，修正品質退步；但 clean case 11 從 false positive 改為 `no_error`，calls 降到 159。

E2B 在查表版 v0.2.0 表現很好，但無查表後顯示 top-logprob candidate 仍不夠可靠。
