# google/gemma-3-4b-pt v0.2.0 無查表測試結果

日期：2026-05-29

```text
corrected: 1
uncertain: 8
no_error: 3
vLLM calls: 169
```

## 每筆結果

```text
case  status      calls  top_candidate
01    uncertain   18     圜->廁 delta=0.685 source=vllm_top_logprob
02    uncertain   16     份->篇 delta=0.393 source=vllm_top_logprob
03    uncertain   16     提->屜 delta=0.857 source=vllm_top_logprob
04    uncertain   15     戰->廠 delta=0.608 source=vllm_top_logprob
05    corrected   10     相->箱 delta=1.575 source=vllm_top_logprob
06    uncertain   14     誤->侍 delta=1.062 source=vllm_top_logprob
07    uncertain   15     汽->氣 delta=1.796 source=vllm_top_logprob
08    uncertain   18     李->編 delta=0.600 source=vllm_top_logprob
09    uncertain   13     結->節 delta=0.579 source=vllm_top_logprob
10    no_error    15     -
11    no_error    11     -
12    no_error    8      -
```

## 與 v0.1.0 比較

v0.1.0 是 corrected 4、uncertain 5、no_error 3、calls 207。

v0.2.0 無查表後 corrected 降到 1，修正品質明顯退步；calls 降到 169，3 筆乾淨句仍維持 `no_error`。

主要問題是 top-logprob candidate 常不是拼字修正目標，例如 `圜->廁`、`戰->廠`、`誤->侍`。
