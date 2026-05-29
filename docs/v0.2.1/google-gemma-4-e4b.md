# google/gemma-4-E4B v0.2.1 測試結果

```text
corrected: 1
uncertain: 6
no_error: 5
calls: 318
score_calls: 278
decode_calls: 40
```

```text
case  status      calls  top_candidate
01    no_error    32     -
02    no_error    10     -
03    uncertain   35     提->屜 delta=0.992 source=vllm_top_logprob
04    uncertain   31     戰->上 delta=0.634 source=vllm_top_logprob
05    corrected   30     相->箱 delta=1.086 source=vllm_top_logprob
06    uncertain   23     誤->侍 delta=1.043 source=vllm_top_logprob
07    uncertain   28     汽->氣 delta=1.128 source=vllm_top_logprob
08    uncertain   37     李->裡 delta=0.774 source=vllm_top_logprob
09    uncertain   43     結->節 delta=0.536 source=vllm_top_logprob
10    no_error    20     -
11    no_error    1      -
12    no_error    28     -
```

v0.2.1 corrected 數與 v0.2.0 無查表版相同，仍為 1。E4B 沒有從 next-token decoding 得到更好的 top candidate。
