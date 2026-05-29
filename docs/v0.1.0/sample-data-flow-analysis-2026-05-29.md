# Gemma 4 E4B 樣本資料流分析

日期：2026-05-29

輸入資料：`data/sample_sentences.json`

這份分析是用 Gemma 4 E4B 跑出來的。下面的分數、閾值與決策都跟本次模型設定綁定。

模型端點：

```text
model: google/gemma-4-E4B
base_url: http://localhost:8000/v1
```

## 目標

這份紀錄說明目前拼字檢查 PoC 在樣本資料上的行為：

- pipeline 會怎麼判斷修正
- 每個案例會呼叫幾次 vLLM
- 每次 vLLM 呼叫大致送了什麼、收了什麼
- 為什麼目前實作會漏掉或降級某些本來應該修掉的錯字

## Pipeline 摘要

對每個輸入句子，目前的實作會這樣跑：

1. 用 vLLM completions 的 `prompt_logprobs` 為整句原文打分。
2. 把 prompt token 的 logprob 對齊回字元位置。
3. 根據 token logprob 和局部 span 分數計算字元風險值。
4. 選出 `risk_score >= 7.0` 的可疑字元，最多 5 個。
5. 透過下列來源產生候選修正：
   - 字詞層級 confusion lexicon
   - 字元層級 confusion table
   - vLLM 的 prompt top alternatives
6. 重新計算原始 local window 與每個候選 local window 的分數。
7. 依照 `delta = candidate_score - original_score` 排序候選。
8. 做出決策：
   - `corrected`：top delta 夠強、margin 夠明顯，而且來源可信
   - `uncertain`：有合理候選，但可信度還不夠
   - `no_error`：沒有任何候選能帶來足夠改善

每次 vLLM 呼叫都會用：

```json
{
  "model": "google/gemma-4-E4B",
  "prompt": "...",
  "max_tokens": 1,
  "temperature": 0,
  "prompt_logprobs": 5,
  "logprobs": 1
}
```

實際生成的 completion token 不用來做修正。pipeline 只看 `prompt_logprobs`。

## 重要發現

在這個模型與 server 組合下，vLLM 回傳了 `prompt_token_ids: null`。

實際的 prompt token 會是每個 `prompt_logprobs` alternatives dictionary 的第一個 entry。這個 entry 不一定是 rank 1。對齊邏輯已經改成在沒有 `prompt_token_ids` 時改用第一個 entry。

如果沒有這個修正，很多 token 會被錯誤視為模型的 top alternative，導致沒辦法正確對齊回原文。

## 整體結果

```text
total cases: 12
vLLM calls: 170
prompt chars scored: 2715
prompt tokens returned: 2205

corrected: 2
uncertain: 7
no_error: 3
```

## 各案例摘要

```text
case  status      calls  prompt_chars  prompt_tokens  output_tokens  top_candidate
01    uncertain   17     280           235            17             圜->園 delta=0.823
02    no_error    5      74            59             5              -
03    uncertain   20     358           309            20             提->屜 delta=0.992
04    uncertain   18     291           238            18             戰->站 delta=0.860
05    corrected   12     156           136            12             相->箱 delta=1.086
06    corrected   15     195           166            15             誤->務 delta=1.564
07    uncertain   13     193           143            13             汽->氣 delta=1.128
08    uncertain   18     319           236            18             李->理 delta=1.087
09    uncertain   20     330           267            20             結->節 delta=0.536
10    no_error    11     170           124            11             -
11    uncertain   2      33            27             2              -
12    no_error    19     316           265            19             -
```

`output_tokens` 會永遠等於呼叫次數，因為每次 request 都只要求 vLLM 生成 `max_tokens=1`。這些生成 token 都不會被拿來用。

## 預期修正

```text
case  input issue  result     note
01    公圜->公園    uncertain  correct top candidate, delta below strong threshold
02    檢察->檢查    no_error   missed before candidate generation
03    抽提->抽屜    uncertain  correct top candidate, delta just below strong threshold
04    車戰->車站    uncertain  correct top candidate, delta below strong threshold
05    信相->信箱    corrected  success
06    服誤->服務    corrected  success
07    天汽->天氣    uncertain  correct top candidate, margin too small
08    整李->整理    uncertain  correct top candidate, margin too small
09    細結->細節    uncertain  correct top candidate, weak delta
10    clean        no_error   acceptable final decision
11    clean        uncertain  false suspicious without candidate
12    clean        no_error   acceptable final decision, but expensive
```

## 失敗分析

### Case 02：漏掉 `檢察 -> 檢查`

預期的錯字沒有通過 suspicious 閾值：

```text
檢 risk=6.550
察 risk=6.258
threshold=7.0
```

因為 suspicious selection 會先於 candidate generation，字詞層級 lexicon 裡的 `檢察 -> 檢查` 從頭到尾都沒機會被納入。

可能的修法：

- 讓字詞層級 lexicon match 即使 risk 低於閾值，也能照樣產生候選。
- 或者直接下修閾值，但這樣 false positive 和 vLLM 呼叫次數都會一起上升。

### Cases 01、03、04：候選是對的，但還是被判成 uncertain

這幾個案例的字詞 lexicon 候選其實都對：

```text
公圜->公園 delta=0.823
抽提->抽屜 delta=0.992
車戰->車站 delta=0.860
```

目前的 strong threshold 是 `1.0`，所以它們沒有達到自動修正門檻。

可能的修法：

- 對可信的 `word_lexicon` 候選使用較低的 strong threshold。
- 或者針對完全命中字詞層級 confusion 的情況，另外設一條規則。

### Cases 07、08：delta 夠強，但 margin 還是不夠

這兩個案例的 top candidate 都是正確答案，而且 delta 也大於 1.0：

```text
天汽->天氣 delta=1.128
整李->整理 delta=1.087
```

但因為第二名候選也很接近，所以最後還是被標成 `uncertain`：

```text
天汽->天气 delta=0.775
天汽->天色 delta=0.764

整李->整裡 delta=0.774
整李->整好 delta=0.642
```

可能的修法：

- 只拿可信的 word-lexicon candidates 去跟其他可信候選比。
- 如果 `vllm_top_logprob` 候選是簡體中文或語意很怪，就應該降權。

### Case 09：delta 太弱

`細結->細節` 的 top candidate 是對的，但局部 likelihood 只改善了：

```text
delta=0.536
```

這個分數高於 weak threshold，但低於 strong threshold。

可能的修法：

- 如果字詞層級 confusion table 被視為足夠可信，就保留給使用者確認。

### Case 11：假的 `uncertain`

這句乾淨的句子：

```text
這家餐廳的牛肉麵很好吃，我下次還想再來。
```

最後卻被標成：

```text
status=uncertain
confidence=low
```

原因是句首的 `這` 風險值很高：

```text
這 risk=10.093
```

雖然沒有產生任何有用候選，但目前的決策邏輯只要有 suspicious chars，就會在沒有排名候選時回 `uncertain`。

可能的修法：

- 當有 suspicious chars，但沒有任何候選修正時，直接回 `no_error`。
- 或者把它標成 diagnostic-only，不要當成產品層級的 uncertain。

### Case 12：乾淨句子，但成本很高

這句乾淨句子：

```text
今天下午可能會下雨，出門記得帶傘。
```

最後雖然是 `no_error`，但總共跑了 19 次 vLLM 呼叫。

The phrase `可能會` was scored with high risk:

```text
可 risk=13.289
能 risk=13.289
會 risk=13.289
```

這讓系統產生了很多無效候選，直到最後才判定不需要修正。

可能的修法：

- 不要把同一個低機率 multi-char token 覆蓋到的每個字元都選成 suspicious。
- 對高頻合法詞組加 stoplist 或 whitelist。
- 對沒有可信候選的 suspicious span，先要求 lexicon 支援，再去做多候選 rescoring。

## 成本觀察

目前這個 PoC 偏向高 recall，也很重 rescoring。

主要成本來源：

- 每句最多挑 5 個 suspicious chars
- 每個 suspicious char 會長出多個候選
- 每個獨立的原始或候選 local window 都會各自打一輪 vLLM
- 句首假警報，以及合法的多字詞造成的 false suspicious chars

成本最高的案例會打到 20 次呼叫。

成本最低的乾淨案例只打了 2 次，但因為決策邏輯，最後還是回了 `uncertain`。

## Suggested Next Changes

1. Generate word-lexicon candidates before or alongside suspicious selection.
2. Use different decision thresholds for `word_lexicon` vs `vllm_top_logprob`.
3. Return `no_error` when suspicious chars have no candidates.
4. Group suspicious chars by token/span to avoid redundant candidate rescoring.
5. Filter vLLM top alternatives to Traditional Chinese single-character replacements.
