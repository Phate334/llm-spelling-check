# google/gemma-4-E2B v0.2.0 測試結果

日期：2026-05-29

```text
corrected: 7
uncertain: 2
no_error: 3
vLLM calls: 167
prompt chars scored: 2716
prompt tokens returned: 2032
```

## 每筆結果

```text
case  status      calls  top_candidate
01    corrected   25     圜->園 delta=1.674 source=word_lexicon
02    uncertain   22     察->查 delta=0.431 source=word_lexicon
03    corrected   18     提->屜 delta=1.160 source=word_lexicon
04    corrected   12     戰->站 delta=1.030 source=word_lexicon
05    corrected   11     相->箱 delta=1.469 source=word_lexicon
06    corrected   12     誤->務 delta=1.796 source=word_lexicon
07    corrected   17     汽->氣 delta=1.420 source=word_lexicon
08    corrected   18     李->理 delta=1.109 source=word_lexicon
09    uncertain   12     結->節 delta=0.758 source=word_lexicon
10    no_error    9      -
11    no_error    1      -
12    no_error    10     -
```

## 與 v0.1.0 比較

v0.1.0 是 corrected 3、uncertain 7、no_error 2、calls 202。

v0.2.0 改善為 corrected 7、uncertain 2、no_error 3、calls 167。這是本輪改善幅度最大的模型。case 03、04、07、08 都從 `uncertain` 進到 `corrected`，case 11 的乾淨句 false positive 也消失。

剩下 case 02 `檢察->檢查` 與 case 09 `細結->細節` 仍維持 `uncertain`，但 top candidate 都是正確的 `word_lexicon` 候選。
