# google/gemma-4-E4B v0.2.0 無查表測試結果

日期：2026-05-29

```text
corrected: 1
uncertain: 6
no_error: 5
vLLM calls: 131
```

## 每筆結果

```text
case  status      calls  top_candidate
01    no_error    14     -
02    no_error    4      -
03    uncertain   19     提->屜 delta=0.992 source=vllm_top_logprob
04    uncertain   14     戰->上 delta=0.634 source=vllm_top_logprob
05    corrected   12     相->箱 delta=1.086 source=vllm_top_logprob
06    uncertain   12     誤->侍 delta=1.043 source=vllm_top_logprob
07    uncertain   11     汽->氣 delta=1.128 source=vllm_top_logprob
08    uncertain   15     李->裡 delta=0.774 source=vllm_top_logprob
09    uncertain   15     結->節 delta=0.536 source=vllm_top_logprob
10    no_error    9      -
11    no_error    1      -
12    no_error    5      -
```

## 與 v0.1.0 比較

v0.1.0 是 corrected 2、uncertain 7、no_error 3、calls 170。

v0.2.0 無查表後 corrected 降到 1，修正品質退步；但 clean case 11 從 false positive 改為 `no_error`，calls 降到 131。

E4B 的 top-logprob candidate 較保守，case 01、02 直接沒有有效候選，因此回 `no_error`。
