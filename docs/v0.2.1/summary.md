# v0.2.1 多模型測試摘要

日期：2026-05-29

測試資料：`data/sample_sentences.json`

本次測試在 v0.2.0 無查表版本上新增 prefix next-token decoding 候選來源：

- 先用 risk score 找 suspicious chars。
- 對每個 suspicious char 取 `text[:index]` 作為 prefix。
- 呼叫 vLLM completions：`max_tokens=1`、`temperature=0`、`logprobs=10`。
- 從 generated token 與 top logprobs 收集單一 CJK 字候選。
- 候選套回原句後，仍用 local window rescoring 和既有 decision rule 判斷。

這版仍然不使用 `WORD_CONFUSIONS` 或 `CHAR_CONFUSIONS`。

## 整體結果

```text
model                 corrected  uncertain  no_error  calls  score_calls  decode_calls
google/gemma-3-1b-pt  3          5          4         381    334          47
google/gemma-3-4b-pt  1          8          3         389    342          47
google/gemma-4-E2B    1          8          3         360    315          45
google/gemma-4-E4B    1          6          5         318    278          40
```

## 與 v0.2.0 無查表版本比較

```text
model                 v0.2.0 corrected  v0.2.1 corrected  result
google/gemma-3-1b-pt  3                 3                 same
google/gemma-3-4b-pt  1                 1                 same
google/gemma-4-E2B    1                 1                 same
google/gemma-4-E4B    1                 1                 same
```

```text
model                 v0.2.0 calls  v0.2.1 calls
google/gemma-3-1b-pt  160           381
google/gemma-3-4b-pt  169           389
google/gemma-4-E2B    159           360
google/gemma-4-E4B    131           318
```

結論：prefix next-token decoding 沒有改善 corrected 數，且 calls 增加約 2 倍以上。

## 與 v0.1.0 比較

```text
model                 v0.1.0 corrected  v0.2.1 corrected  quality
google/gemma-3-1b-pt  5                 3                 regressed
google/gemma-3-4b-pt  4                 1                 regressed
google/gemma-4-E2B    3                 1                 regressed
google/gemma-4-E4B    2                 1                 regressed
```

v0.2.1 仍然比 v0.1.0 乾淨，因為完全不靠查表；但以目前測試資料的修正結果來看，修正品質沒有超過 v0.1.0。

## 主要觀察

- prefix-only decoding 沒有看到右文，所以容易產生語境上合理但不是拼字修正的候選。
- `車戰` 前文是 `...在車`，模型傾向生成 `上`，這符合「在車上」語境，但不是目標修正 `站`。
- `google/gemma-4-E2B` 在 case 01 由 next-token 產生 `圜->館`，仍不是 `園`。
- `google/gemma-3-1b-pt` 在 case 08 由 next-token 產生 `李->編`，不是 `理`。
- 成功案例主要仍來自原本 prompt-logprob alternatives，而不是 prefix next-token decoding。

## 案例命中狀況

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

## 結論

v0.2.1 的 prefix next-token decoding 方向不值得直接當預設策略。它增加了不少成本，但 corrected 數沒有提升。

下一步若要維持不查表，候選生成需要讓模型同時看到左文與右文。vLLM OpenAI-compatible completions 不支援 `suffix` insertion，因此比較可行的方向是：

1. 用 instruction-style prompt 讓模型針對 suspicious span 輸出候選字。
2. 或用 constrained generation / structured output 產生候選，再用目前 rescoring 決策。
3. 或另外建立不含已知錯字對的通用形近音近候選產生器，再交給 LLM rescoring。
