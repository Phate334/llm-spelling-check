# google/gemma-3-1b-pt v0.2.0 測試結果

日期：2026-05-29

```text
corrected: 6
uncertain: 3
no_error: 3
vLLM calls: 167
prompt chars scored: 2714
prompt tokens returned: 2044
```

## 每筆結果

```text
case  status      calls  top_candidate
01    corrected   20     圜->園 delta=1.612 source=word_lexicon
02    uncertain   13     察->查 delta=0.378 source=word_lexicon
03    corrected   17     提->屜 delta=1.061 source=word_lexicon
04    uncertain   16     戰->上 delta=0.863 source=vllm_top_logprob
05    corrected   11     相->箱 delta=1.256 source=word_lexicon
06    corrected   16     誤->務 delta=2.021 source=word_lexicon
07    corrected   12     汽->氣 delta=2.145 source=word_lexicon
08    corrected   16     李->理 delta=1.589 source=word_lexicon
09    uncertain   14     結->節 delta=0.810 source=word_lexicon
10    no_error    11     -
11    no_error    13     -
12    no_error    8      -
```

## 與 v0.1.0 比較

v0.1.0 是 corrected 5、uncertain 3、no_error 4、calls 202。

v0.2.0 改善為 corrected 6、uncertain 3、no_error 3、calls 167。主要改善是 case 03 `抽提->抽屜` 從 `uncertain` 變成 `corrected`，case 02 `檢察->檢查` 從漏掉變成有正確候選的 `uncertain`。

3 筆乾淨句仍全部維持 `no_error`。
