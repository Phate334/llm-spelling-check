# google/gemma-3-4b-pt v0.2.1 測試結果

```text
corrected: 1
uncertain: 8
no_error: 3
calls: 389
score_calls: 342
decode_calls: 47
```

```text
case  status      calls  top_candidate
01    uncertain   35     圜->廁 delta=0.685 source=vllm_top_logprob
02    uncertain   33     份->篇 delta=0.393 source=vllm_top_logprob
03    uncertain   33     提->屜 delta=0.857 source=vllm_top_logprob
04    uncertain   34     戰->廠 delta=0.608 source=vllm_top_logprob
05    corrected   31     相->箱 delta=1.575 source=vllm_top_logprob
06    uncertain   30     誤->侍 delta=1.062 source=vllm_top_logprob
07    uncertain   32     汽->氣 delta=1.796 source=vllm_top_logprob
08    uncertain   39     李->編 delta=0.600 source=vllm_top_logprob
09    uncertain   33     結->節 delta=0.579 source=vllm_top_logprob
10    no_error    34     -
11    no_error    22     -
12    no_error    33     -
```

v0.2.1 corrected 數與 v0.2.0 無查表版相同，仍為 1。新增 next-token decoding 沒有改善 top candidate。
