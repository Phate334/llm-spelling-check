# 多模型測試比較摘要

日期：2026-05-29

測試資料：`data/sample_sentences.json`

這份摘要整理多次模型測試的橫向比較。單一模型的細節、每筆案例與失敗分析請看各自報告。

## 測試內容

這次測試的目標是比較不同 Gemma 系列模型接在同一套中文拼字檢查 PoC pipeline 後，對 `data/sample_sentences.json` 的輸出差異。

測試資料共有 12 筆：

- 9 筆含有預期錯字，例如 `公圜->公園`、`信相->信箱`、`服誤->服務`。
- 3 筆乾淨句，用來觀察模型和規則是否會誤報。

每個模型都使用同一套流程、同一組 threshold、同一份 confusion lexicon 與同一個 CLI 測試資料。這樣可以觀察「模型替換後，現有規則會怎麼變」，但還不能代表模型本身的最終上限，因為目前沒有針對個別模型重新校準 threshold。

## Pipeline 範圍

所有測試都使用同一套 PoC pipeline：

1. 用 vLLM completions `prompt_logprobs` 評原句。
2. 對齊 token logprob 到原始字元。
3. 以 `risk_score >= 7.0` 選 suspicious chars，最多 5 個。
4. 從 `word_lexicon`、char confusion、vLLM top alternatives 產生候選。
5. 重新評分 local window。
6. 依 delta 與 margin 決定 `corrected`、`uncertain` 或 `no_error`。

## 指標定義

`corrected`：
系統判定有足夠信心，並且自動套用修正。對含錯字案例來說，這通常是最理想結果；但仍需要看修正內容是否符合預期。

`uncertain`：
系統偵測到可疑位置，或找到候選修正，但信心不足以自動套用。這份摘要把它視為「未自動修正」或 uncorrected。對含錯字案例來說，若正確候選有出現但停在 `uncertain`，代表 pipeline 有抓到方向，但 decision rule 太保守或候選排序不夠穩。對乾淨句來說，`uncertain` 通常代表 false positive。

`no_error`：
系統最後判定不需要修正。對乾淨句來說是正確結果；對含錯字案例來說則代表漏掉。

`calls`：
本次跑完整批資料時，對 vLLM completions API 發出的 request 次數。每次 request 會要求 `max_tokens=1`，但實際判斷只使用 `prompt_logprobs`，生成出來的 completion token 不參與修正。

`prompt chars scored` 與 `prompt tokens returned`：
分別代表送進評分流程的 prompt 字元量，以及 vLLM 回傳可用 logprob 的 prompt token 數。這兩個數字主要用來觀察 rescoring 成本。

## 整體結果

```text
model                                  corrected  uncertain  no_error  calls
google/gemma-3-1b-pt                   5          3          4         202
google/gemma-3-4b-pt                   4          5          3         207
google/gemma-3-4b-it                   3          7          2         186
google/gemma-4-E2B                     3          7          2         202
google/gemma-4-E4B                     2          7          3         170
RedHatAI/gemma-4-26B-A4B-it-NVFP4      1          9          2         275
```

目前這批 sample set 裡，`google/gemma-3-1b-pt` 的自動修正筆數最高，而且 3 筆乾淨句都維持 `no_error`。`google/gemma-3-4b-pt` 也很接近，乾淨句表現穩，且 top candidate 多數來自 `word_lexicon`。

`google/gemma-4-E2B` 的候選品質不差，但 decision rule 偏保守，很多正確候選停在 `uncertain`。`RedHatAI/gemma-4-26B-A4B-it-NVFP4` 在目前規則下不建議優先採用，主要是 top alternatives 太雜，而且 vLLM log 也有 FP4 fallback 與可能影響準確率的警告。

## 案例命中狀況

標記說明：

- `C`：自動修正成功。
- `U`：有正確候選但未自動修正。
- `M`：漏掉、錯誤 top candidate，或沒有有效候選。
- `OK`：乾淨句判 `no_error`。
- `FP`：乾淨句被判 `uncertain` 或有錯誤候選。

```text
case  expected       gemma-3-1b-pt  gemma-3-4b-pt  gemma-3-4b-it  gemma-4-E2B  gemma-4-E4B  redhat-nvfp4
01    公圜->公園      C              C              U              C            U            M
02    檢察->檢查      M              M              M              U            M            M
03    抽提->抽屜      U              U              U              U            U            U
04    車戰->車站      U              U              U              U            U            M
05    信相->信箱      C              C              C              C            C            M
06    服誤->服務      C              C              C              C            C            U
07    天汽->天氣      C              U              C              U            U            M
08    整李->整理      C              C              U              U            U            C
09    細結->細節      U              U              U              U            U            M
10    clean          OK             OK             OK             OK           OK           FP
11    clean          OK             OK             OK             FP           FP           FP
12    clean          OK             OK             FP             OK           OK           OK
```

## 初步排序

1. `google/gemma-3-1b-pt`

   目前最值得繼續調 pipeline 的 baseline。模型小、成本低，這批資料上自動修正 5 筆，乾淨句也沒有被誤報。

2. `google/gemma-3-4b-pt`

   表現穩，乾淨句全數 `no_error`。自動修正 4 筆，缺點是 `檢察->檢查` 漏掉，且幾筆正確候選仍因 decision rule 卡在 `uncertain`。

3. `google/gemma-4-E2B`

   不量化可穩定放進 L4，候選品質可以，但目前 decision rule 對它偏保守。適合保留做對照。

4. `google/gemma-3-4b-it`

   可以不量化跑在 L4 上，但 top-logprob 會出現 `T` 這類不適合繁中修正的候選，需要更嚴格過濾。

5. `google/gemma-4-E4B`

   呼叫數較低，但自動修正筆數少，`檢察->檢查` 在 suspicious selection 前就被漏掉。

6. `RedHatAI/gemma-4-26B-A4B-it-NVFP4`

   不適合用目前規則直接接上。vLLM top alternatives 會出現韓文、符號、底線等候選，且 FP4 fallback 警告需要注意。

## 共同問題

- `vllm_top_logprob` 候選需要先過濾，只保留有效的繁體中文單字替換。
- `word_lexicon` 應該走獨立 decision rule，不要跟 noisy top-logprob 候選直接混排。
- `檢察->檢查` 這類字詞層級命中，不應該完全受單字 risk threshold 限制。
- 有 suspicious chars 但沒有候選時，產品輸出應該偏向 `no_error`，debug 再保留 suspicious details。
- risk threshold 和 delta threshold 會跟模型尺度綁定，後續需要 per-model calibration。

## 資源觀察

- `google/gemma-4-E2B` 不量化在 L4 上很充裕：model loading 約 `8.89 GiB`，available KV cache 約 `9.92 GiB`。
- `google/gemma-3-4b-pt` 不量化在 L4 上也很充裕：model loading 約 `7.82 GiB`，available KV cache 約 `10.99 GiB`。
- `RedHatAI/gemma-4-26B-A4B-it-NVFP4` 可以啟動，但 vLLM log 顯示沒有原生 FP4 支援，會透過 Marlin 使用 weight-only FP4 compression，且有準確率風險警告。

## 建議下一步

先以 `google/gemma-3-1b-pt` 或 `google/gemma-3-4b-pt` 作為 PoC baseline，優先修 pipeline 規則：

1. 過濾 `vllm_top_logprob` 候選。
2. 讓 `word_lexicon` 候選有較寬鬆但明確的自動修正規則。
3. 讓 word-level confusion 可以在 risk threshold 以下也產生候選。
4. 沒有可信候選時，不要回傳使用者可見的 `uncertain`。
5. 針對每個模型重新校準 risk 與 delta 閾值。
