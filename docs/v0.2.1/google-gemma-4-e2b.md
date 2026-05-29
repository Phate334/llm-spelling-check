# google/gemma-4-E2B v0.2.1 測試結果

```text
corrected: 1
uncertain: 8
no_error: 3
calls: 360
score_calls: 315
decode_calls: 45
```

```text
case  status      calls  top_candidate
01    uncertain   43     圜->館 delta=1.137 source=next_token_decode
02    uncertain   40     察->視 delta=0.333 source=vllm_top_logprob
03    uncertain   32     提->屜 delta=1.160 source=vllm_top_logprob
04    uncertain   25     戰->上 delta=0.853 source=vllm_top_logprob
05    corrected   30     相->箱 delta=1.469 source=vllm_top_logprob
06    uncertain   24     誤->侍 delta=1.104 source=vllm_top_logprob
07    uncertain   41     汽->氣 delta=1.420 source=vllm_top_logprob
08    uncertain   37     李->編 delta=0.764 source=next_token_decode
09    uncertain   32     結->節 delta=0.758 source=vllm_top_logprob
10    no_error    23     -
11    no_error    1      -
12    no_error    32     -
```

v0.2.1 corrected 數與 v0.2.0 無查表版相同，仍為 1。next-token decoding 讓 case 01 top candidate 變成 `圜->館`，仍不是正確修正。
