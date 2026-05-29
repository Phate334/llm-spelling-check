# google/gemma-4-E4B v0.2.0 測試結果

日期：2026-05-29

```text
corrected: 4
uncertain: 5
no_error: 3
vLLM calls: 140
prompt chars scored: 2267
prompt tokens returned: 1693
```

## 每筆結果

```text
case  status      calls  top_candidate
01    uncertain   15     圜->園 delta=0.823 source=word_lexicon
02    uncertain   6      察->查 delta=0.370 source=word_lexicon
03    uncertain   19     提->屜 delta=0.992 source=word_lexicon
04    uncertain   15     戰->站 delta=0.860 source=word_lexicon
05    corrected   12     相->箱 delta=1.086 source=word_lexicon
06    corrected   15     誤->務 delta=1.564 source=word_lexicon
07    corrected   11     汽->氣 delta=1.128 source=word_lexicon
08    corrected   16     李->理 delta=1.087 source=word_lexicon
09    uncertain   16     結->節 delta=0.536 source=word_lexicon
10    no_error    9      -
11    no_error    1      -
12    no_error    5      -
```

## 與 v0.1.0 比較

v0.1.0 是 corrected 2、uncertain 7、no_error 3、calls 170。

v0.2.0 改善為 corrected 4、uncertain 5、no_error 3、calls 140。主要改善是 case 07 `天汽->天氣`、case 08 `整李->整理` 進到 `corrected`，case 02 `檢察->檢查` 從漏掉變成有正確候選的 `uncertain`，case 11 的乾淨句 false positive 也消失。

E4B 仍然偏保守，case 01、03、04、09 都有正確 top candidate，但 delta 沒有通過強修正條件。
