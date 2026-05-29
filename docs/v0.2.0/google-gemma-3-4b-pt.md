# google/gemma-3-4b-pt v0.2.0 測試結果

日期：2026-05-29

```text
corrected: 5
uncertain: 4
no_error: 3
vLLM calls: 175
prompt chars scored: 2830
prompt tokens returned: 2120
```

## 每筆結果

```text
case  status      calls  top_candidate
01    corrected   19     圜->園 delta=1.305 source=word_lexicon
02    uncertain   17     察->查 delta=0.675 source=word_lexicon
03    uncertain   16     提->屜 delta=0.857 source=word_lexicon
04    uncertain   16     戰->站 delta=0.722 source=word_lexicon
05    corrected   10     相->箱 delta=1.575 source=word_lexicon
06    corrected   15     誤->務 delta=1.947 source=word_lexicon
07    corrected   15     汽->氣 delta=1.796 source=word_lexicon
08    corrected   19     李->理 delta=1.003 source=word_lexicon
09    uncertain   14     結->節 delta=0.579 source=word_lexicon
10    no_error    15     -
11    no_error    11     -
12    no_error    8      -
```

## 與 v0.1.0 比較

v0.1.0 是 corrected 4、uncertain 5、no_error 3、calls 207。

v0.2.0 改善為 corrected 5、uncertain 4、no_error 3、calls 175。主要改善是 case 07 `天汽->天氣` 進到 `corrected`，case 02 的 top candidate 從 unrelated `份->篇` 變成正確的 `察->查`。

3 筆乾淨句仍全部維持 `no_error`。
