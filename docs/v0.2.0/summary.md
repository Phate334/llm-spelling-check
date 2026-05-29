# v0.2.0 多模型測試摘要

日期：2026-05-29

測試資料：`data/sample_sentences.json`

本次測試使用 v0.2.0 pipeline，輪流啟動以下模型：

- `google/gemma-3-1b-pt`
- `google/gemma-3-4b-pt`
- `google/gemma-4-E2B`
- `google/gemma-4-E4B`

已移除不在本輪測試名單中的 instruction-tuned / 舊測試模型快取：

```text
models--google--gemma-3-4b-it
models--google--gemma-4-26B-A4B
```

清理後 Hugging Face cache 約 `35G`，剩下本輪需要的四個模型。

## v0.2.0 改動重點

這次 pipeline 主要調整候選品質與決策，不處理成本最佳化：

- `word_lexicon` 會先掃描全句，不再完全依賴 suspicious char threshold。
- `vllm_top_logprob` 候選只保留單一 CJK 字元，過濾 `T`、`#`、`_`、韓文等 noisy token。
- 自動修正只允許 trusted source：`word_lexicon`、`char_confusion`。
- trusted candidate 的 margin 只跟 trusted candidate 比，不被 `vllm_top_logprob` 擋掉。
- 沒有候選時回 `no_error`，但仍保留 suspicious chars 作 debug。

## 整體結果

```text
model                 corrected  uncertain  no_error  calls  prompt_chars  prompt_tokens
google/gemma-4-E2B    7          2          3         167    2716          2032
google/gemma-3-1b-pt  6          3          3         167    2714          2044
google/gemma-3-4b-pt  5          4          3         175    2830          2120
google/gemma-4-E4B    4          5          3         140    2267          1693
```

這次最佳結果是 `google/gemma-4-E2B`：9 筆錯字中自動修正 7 筆，剩下 `檢察->檢查` 與 `細結->細節` 都有正確候選但維持 `uncertain`。3 筆乾淨句都判 `no_error`。

`google/gemma-3-1b-pt` 仍然很值得保留。它只比 E2B 少自動修正一筆，而且模型小、啟動和推論成本較低。

## 與 v0.1.0 比較

```text
model                 v0.1.0 corrected  v0.2.0 corrected  status change
google/gemma-3-1b-pt  5                 6                 improved
google/gemma-3-4b-pt  4                 5                 improved
google/gemma-4-E2B    3                 7                 strongly improved
google/gemma-4-E4B    2                 4                 improved
```

```text
model                 v0.1.0 calls  v0.2.0 calls  note
google/gemma-3-1b-pt  202           167           fewer calls
google/gemma-3-4b-pt  207           175           fewer calls
google/gemma-4-E2B    202           167           fewer calls
google/gemma-4-E4B    170           140           fewer calls
```

雖然這輪沒有特別做成本最佳化，但因為 noisy top-logprob 候選被過濾、無候選時直接回 `no_error`，實際 vLLM calls 都下降。

## 案例命中狀況

標記說明：

- `C`：自動修正成功。
- `U`：有候選但未自動修正。
- `OK`：乾淨句判 `no_error`。

```text
case  expected     gemma-3-1b-pt  gemma-3-4b-pt  gemma-4-E2B  gemma-4-E4B
01    公圜->公園    C              C              C            U
02    檢察->檢查    U              U              U            U
03    抽提->抽屜    C              U              C            U
04    車戰->車站    U              U              C            U
05    信相->信箱    C              C              C            C
06    服誤->服務    C              C              C            C
07    天汽->天氣    C              C              C            C
08    整李->整理    C              C              C            C
09    細結->細節    U              U              U            U
10    clean        OK             OK             OK           OK
11    clean        OK             OK             OK           OK
12    clean        OK             OK             OK           OK
```

## 改善分析

v0.2.0 的改善主要來自兩點：

1. `word_lexicon` bypass risk 讓 `檢察->檢查` 這類低於 suspicious threshold 的詞級命中仍能被評分。它目前仍因 delta 不夠強停在 `uncertain`，但不再是 `no_error` 漏掉。
2. source-aware decision 讓可信候選不會被 `vllm_top_logprob` 的高分但不可信候選擋掉，因此 `抽提->抽屜`、`車戰->車站`、`天汽->天氣`、`整李->整理` 在部分模型上從 `uncertain` 進到 `corrected`。

乾淨句改善也明顯。v0.1.0 的 E2B / E4B 曾在 clean case 11 回 `uncertain`，v0.2.0 四個模型的三筆 clean case 全部是 `no_error`。

## 仍待處理

- `檢察->檢查` 在四個模型上都只到 `uncertain`，表示詞表命中雖然被納入，但 strong decision rule 仍偏保守。
- `細結->細節` 在四個模型上都停在 `uncertain`，delta 普遍低於 strong threshold。
- `google/gemma-3-1b-pt` 的 case 04 top candidate 仍是 `戰->上`，但因它來自 `vllm_top_logprob`，不會自動修正；正確 `戰->站` 有出現在候選中。

## 結論

v0.2.0 相比 v0.1.0 有明顯改善，且不是針對測試資料硬修：

- 四個保留模型 corrected 數都增加。
- 所有模型 vLLM calls 都下降。
- 乾淨句 false positive 消失。
- top candidate 幾乎都回到 `word_lexicon`，noisy top-logprob 對決策的干擾降低。

目前建議以 `google/gemma-4-E2B` 作為品質 baseline，以 `google/gemma-3-1b-pt` 作為低成本 baseline。
