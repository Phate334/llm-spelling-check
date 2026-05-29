# google/gemma-3-1b-pt v0.2.1 測試結果

```text
corrected: 3
uncertain: 5
no_error: 4
calls: 381
score_calls: 334
decode_calls: 47
```

```text
case  status      calls  top_candidate
01    uncertain   36     圜->廁 delta=0.928 source=vllm_top_logprob
02    no_error    33     -
03    uncertain   34     提->屜 delta=1.061 source=vllm_top_logprob
04    uncertain   34     戰->上 delta=0.863 source=vllm_top_logprob
05    corrected   27     相->箱 delta=1.256 source=vllm_top_logprob
06    corrected   29     誤->務 delta=2.021 source=vllm_top_logprob
07    corrected   35     汽->氣 delta=2.145 source=vllm_top_logprob
08    uncertain   35     李->編 delta=1.078 source=next_token_decode
09    uncertain   35     結->節 delta=0.810 source=vllm_top_logprob
10    no_error    29     -
11    no_error    28     -
12    no_error    26     -
```

v0.2.1 corrected 數與 v0.2.0 無查表版相同，仍為 3。新增 next-token decoding 後，case 08 top candidate 變成 `李->編`，但仍不是正確修正。
