# Google Gemma 4 E2B 不量化測試報告

日期：2026-05-29

測試資料：`data/sample_sentences.json`

## 測試設定

這次測的是 `google/gemma-4-E2B`，不做量化。

```text
model: google/gemma-4-E2B
base_url: http://localhost:8000/v1
vLLM: v0.21.0
GPU: NVIDIA L4 23034 MiB
```

`compose.yaml` 的 vLLM 設定：

```text
google/gemma-4-E2B
--served-model-name google/gemma-4-E2B
--host 0.0.0.0
--language-model-only
--max-model-len 8192
--gpu-memory-utilization 0.90
--enforce-eager
```

沒有設定 `--quantization`，vLLM 實際 log 顯示：

```text
dtype=torch.bfloat16
quantization=None
```

## GPU 記憶體狀況

vLLM 載入 log：

```text
Checkpoint size: 9.54 GiB
Model loading took 8.89 GiB memory
Available KV cache memory: 9.92 GiB
GPU KV cache size: 1,062,157 tokens
Maximum concurrency for 8,192 tokens per request: 129.66x
```

結論：E2B 不量化放在 L4 很充裕。權重和 KV cache 都有足夠空間，不需要 BnB、FP8 或 CPU offload。

## Pipeline 摘要

流程跟前幾次測試相同：

1. 用 vLLM completions `prompt_logprobs` 評原句。
2. 將 token logprob 對齊回原始字元位置。
3. 計算每個字的 risk score。
4. 選出 `risk_score >= 7.0` 的 suspicious chars，最多 5 個。
5. 從以下來源產生候選：
   - word-level confusion lexicon
   - char-level confusion table
   - vLLM top prompt alternatives
6. 對原始 local window 和候選 local window 重新評分。
7. 用 `delta = candidate_score - original_score` 排序。
8. 輸出 `corrected`、`uncertain` 或 `no_error`。

每次 vLLM request：

```json
{
  "model": "google/gemma-4-E2B",
  "prompt": "...",
  "max_tokens": 1,
  "temperature": 0,
  "prompt_logprobs": 5,
  "logprobs": 1
}
```

產生出來的 1 個 completion token 不參與判斷，只使用 `prompt_logprobs`。

## 整體結果

```text
total cases: 12
vLLM calls: 202
prompt chars scored: 3260
prompt tokens returned: 2650

corrected: 3
uncertain: 7
no_error: 2
```

這次 top candidate 幾乎都來自 `word_lexicon`，沒有看到亂碼或符號候選排第一的狀況。

## 每筆結果

```text
case  status      calls  prompt_chars  prompt_tokens  output_tokens  top_candidate
01    corrected   27     434           368            27             圜->園 delta=1.674 source=word_lexicon
02    uncertain   23     396           316            23             察->查 delta=0.431 source=word_lexicon
03    uncertain   20     343           303            20             提->屜 delta=1.160 source=word_lexicon
04    uncertain   15     240           198            15             戰->站 delta=1.030 source=word_lexicon
05    corrected   11     143           123            11             相->箱 delta=1.469 source=word_lexicon
06    corrected   12     156           132            12             誤->務 delta=1.796 source=word_lexicon
07    uncertain   20     300           230            20             汽->氣 delta=1.420 source=word_lexicon
08    uncertain   21     373           275            21             李->理 delta=1.109 source=word_lexicon
09    uncertain   19     322           261            19             結->節 delta=0.758 source=word_lexicon
10    no_error    11     170           124            11             -
11    uncertain   2      33            27             2              -
12    no_error    21     350           293            21             -
```

`output_tokens` 會等於 call count，因為每次 request 都設定 `max_tokens=1`。目前程式不使用這些 completion tokens。

## 預期錯字命中狀況

```text
case  expected     result     note
01    公圜->公園    corrected  成功
02    檢察->檢查    uncertain  有抓到 察->查，但 delta 偏低
03    抽提->抽屜    uncertain  正確候選排第一，但 decision 未放行
04    車戰->車站    uncertain  正確候選排第一，但 decision 未放行
05    信相->信箱    corrected  成功
06    服誤->服務    corrected  成功
07    天汽->天氣    uncertain  正確候選排第一，但 decision 未放行
08    整李->整理    uncertain  正確候選排第一，但 decision 未放行
09    細結->細節    uncertain  正確候選排第一，但 delta 偏弱
10    clean        no_error   OK
11    clean        uncertain  false suspicious，沒有候選
12    clean        no_error   OK，但呼叫數偏多
```

## Top Suspicious Chars

```text
case  top suspicious chars
01    圜@16:19.6, 散@17:13.7, 公@15:13.0
02    這@0:10.1, 份@1:8.1, 察@8:7.8
03    提@7:12.3, 他@0:10.8, 鑰@2:10.4
04    戰@8:11.4, 我@0:11.0, 們@1:11.0
05    相@11:16.9, 請@0:11.4, 會@2:9.4
06    誤@6:15.4, 服@5:12.7, 一@7:11.3
07    汽@4:11.3, 很@5:10.6, 好@6:9.9
08    李@7:13.1, 整@6:10.4, 這@0:10.1
09    老@0:14.5, 闆@1:14.5, 結@12:14.3
10    我@0:11.2, 想@1:11.2, 先@2:8.4
11    這@0:10.1
12    可@4:14.2, 能@5:14.2, 會@6:14.2
```

## 判斷錯誤與不理想案例

### Case 02：`檢察 -> 檢查` 只到 uncertain

E2B 這次有抓到正確候選：

```text
察->查 delta=0.431
```

但 delta 只比 weak threshold 高一些，距離 strong threshold `1.0` 太遠，所以沒有自動修正。

這筆適合維持 `uncertain`，除非我們把詞表命中視為更強規則。

### Cases 03、04、07、08：正確候選排第一但沒 auto-correct

這幾筆都是 `word_lexicon` 候選排第一：

```text
抽提->抽屜 delta=1.160
車戰->車站 delta=1.030
天汽->天氣 delta=1.420
整李->整理 delta=1.109
```

照理說 delta 已經不低，但目前 decision 還要求 top1 和 top2 的 margin >= `0.4`。如果 vLLM top alternatives 很接近，仍會被打回 `uncertain`。

建議：

- `word_lexicon` 候選不要跟 `vllm_top_logprob` 候選共用同一個 margin 規則。
- 或者對 exact word confusion hit 放寬 margin。

### Case 09：`細結 -> 細節` delta 偏弱

```text
結->節 delta=0.758
```

這筆比 weak threshold 高，但還不到 strong threshold。若是 POC 追求 precision，留在 `uncertain` 合理。

### Case 11：乾淨句被判 uncertain

乾淨句：

```text
這家餐廳的牛肉麵很好吃，我下次還想再來。
```

只因句首 `這` 被打出高 risk：

```text
這 risk=10.1
```

沒有候選修正，但目前 decision 邏輯是「有 suspicious、沒候選」就回 `uncertain low`。

建議：

- 沒有任何 candidate correction 時，產品輸出應該回 `no_error`。
- suspicious chars 可以保留在 debug 訊息，不要直接變成使用者可見的錯字提示。

### Case 12：乾淨句 no_error 但成本偏高

```text
今天下午可能會下雨，出門記得帶傘。
```

最後是 `no_error`，但做了 21 次 vLLM call。主因是 `可能會` 被打成高 risk：

```text
可 risk=14.2
能 risk=14.2
會 risk=14.2
```

這會產生很多沒有價值的候選 rescoring。

建議：

- 對同一個低分 multi-char token 不要拆成多個 suspicious char 全部重跑。
- 加常見詞白名單或詞級過濾。
- 沒有 trusted candidate 時少跑或不跑 rescoring。

## 結論

`google/gemma-4-E2B` 不量化可以穩定放進 L4，資源壓力低，且目前樣本上的 candidate 品質不差。

在目前 pipeline 規則下，E2B 的主要問題不是模型亂給候選，而是 decision 規則太保守，以及 suspicious selection 對乾淨句仍會產生不必要成本。

下一步建議：

1. `word_lexicon` candidate 使用獨立 decision 規則。
2. 沒有 candidate correction 時回 `no_error`，不要回 `uncertain`。
3. 過濾或降低句首常見字的 suspicious 權重。
4. 對同一個低分 token/span 做 group，避免重複 rescoring。
