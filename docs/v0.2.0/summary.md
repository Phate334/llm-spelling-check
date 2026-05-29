# v0.2.0 多模型測試摘要

日期：2026-05-29

測試資料：`data/sample_sentences.json`

本次重測使用目前 v0.2.0 pipeline 的「無查表」版本：候選只來自 vLLM `prompt_logprobs` top alternatives，不再使用 `WORD_CONFUSIONS` 或 `CHAR_CONFUSIONS`。

測試模型：

- `google/gemma-3-1b-pt`
- `google/gemma-3-4b-pt`
- `google/gemma-4-E2B`
- `google/gemma-4-E4B`

## v0.2.0 改動重點

這版刻意移除固定錯字表，避免把拼字檢查能力建立在已知案例查表上：

- 候選只從模型回傳的 token top-logprob alternatives 產生。
- top-logprob 候選只保留單一 CJK 字元，過濾 `T`、`#`、`_`、韓文等 noisy token。
- 自動修正來源只剩 `vllm_top_logprob`。
- 沒有候選時回 `no_error`，但仍保留 suspicious chars 作 debug。

## 整體結果

```text
model                 corrected  uncertain  no_error  calls
google/gemma-3-1b-pt  3          5          4         160
google/gemma-4-E4B    1          6          5         131
google/gemma-4-E2B    1          8          3         159
google/gemma-3-4b-pt  1          8          3         169
```

無查表後，corrected 數明顯下降。這表示目前「只吃 token top-logprob alternatives」不足以穩定產生正確修正候選。

乾淨句表現仍然穩定，四個模型的 clean cases 都是 `no_error`。

## 與 v0.1.0 比較

```text
model                 v0.1.0 corrected  v0.2.0 corrected  quality
google/gemma-3-1b-pt  5                 3                 regressed
google/gemma-3-4b-pt  4                 1                 regressed
google/gemma-4-E2B    3                 1                 regressed
google/gemma-4-E4B    2                 1                 regressed
```

```text
model                 v0.1.0 calls  v0.2.0 calls
google/gemma-3-1b-pt  202           160
google/gemma-3-4b-pt  207           169
google/gemma-4-E2B    202           159
google/gemma-4-E4B    170           131
```

結論：v0.2.0 在「不靠查表」這個方向比較乾淨，但以目前候選生成方式來看，修正品質相較 v0.1.0 退步。calls 有下降，乾淨句 false positive 也改善，但這不是主要目標的充分改善。

## 案例命中狀況

標記說明：

- `C`：自動修正成功。
- `U`：有候選但未自動修正。
- `M`：漏掉或沒有有效候選。
- `OK`：乾淨句判 `no_error`。

```text
case  expected     gemma-3-1b-pt  gemma-3-4b-pt  gemma-4-E2B  gemma-4-E4B
01    公圜->公園    U              U              U            M
02    檢察->檢查    M              U              U            M
03    抽提->抽屜    U              U              U            U
04    車戰->車站    U              U              U            U
05    信相->信箱    C              C              C            C
06    服誤->服務    C              U              U            U
07    天汽->天氣    C              U              U            U
08    整李->整理    U              U              U            U
09    細結->細節    U              U              U            U
10    clean        OK             OK             OK           OK
11    clean        OK             OK             OK           OK
12    clean        OK             OK             OK           OK
```

## 主要觀察

- `信相->信箱` 是四個模型都能靠 top-logprob 自動修正的案例。
- `google/gemma-3-1b-pt` 額外能修正 `服誤->服務`、`天汽->天氣`，是目前無查表版本中 corrected 數最高的模型。
- `公圜->公園` 常被產生為 `圜->廁`，表示 top-logprob alternatives 會偏向局部 token 形似或語料常見替換，不一定是語意正確修正。
- `車戰->車站` 常出現 `戰->上`，因句子「在車上見面」也很合理，模型 likelihood 不等於拼字修正意圖。
- `整李->整理` 常出現 `李->型`、`李->頓`、`李->裡`，正確候選不穩。

## 是否比 v0.1.0 改善

整體沒有。若以拼字修正品質為主，v0.2.0 無查表版本相較 v0.1.0 是退步：

- corrected 數四個模型都下降。
- 多數錯字只能進入 `uncertain`，甚至回 `no_error`。
- top-logprob candidate 雖然提供訊號，但不是可靠的候選生成器。

有改善的部分：

- 完全移除查表，方法論比較乾淨。
- clean cases 全部 `no_error`。
- vLLM calls 下降。

下一步若要維持「不靠查表」，需要改候選生成方式，例如讓模型針對 suspicious span 生成候選字，或設計不依賴固定錯字表的 constrained candidate generation，再交給目前 rescoring/decision 流程判斷。
