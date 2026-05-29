# google/gemma-3-1b-pt v0.2.0 無查表測試結果

日期：2026-05-29

```text
corrected: 3
uncertain: 5
no_error: 4
vLLM calls: 160
```

## 每筆結果

```text
case  status      calls  top_candidate
01    uncertain   19     圜->廁 delta=0.928 source=vllm_top_logprob
02    no_error    12     -
03    uncertain   17     提->屜 delta=1.061 source=vllm_top_logprob
04    uncertain   15     戰->上 delta=0.863 source=vllm_top_logprob
05    corrected   11     相->箱 delta=1.256 source=vllm_top_logprob
06    corrected   14     誤->務 delta=2.021 source=vllm_top_logprob
07    corrected   12     汽->氣 delta=2.145 source=vllm_top_logprob
08    uncertain   15     李->型 delta=0.980 source=vllm_top_logprob
09    uncertain   13     結->節 delta=0.810 source=vllm_top_logprob
10    no_error    11     -
11    no_error    13     -
12    no_error    8      -
```

## 與 v0.1.0 比較

v0.1.0 是 corrected 5、uncertain 3、no_error 4、calls 202。

v0.2.0 無查表後 corrected 降到 3，修正品質退步；但 calls 降到 160，3 筆乾淨句仍維持 `no_error`。

這個模型是無查表版本中表現最好的模型，成功修正 `信相->信箱`、`服誤->服務`、`天汽->天氣`。
