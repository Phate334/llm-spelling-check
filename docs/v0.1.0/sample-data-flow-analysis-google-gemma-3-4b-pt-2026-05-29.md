# Google Gemma 3 4B PT 測試報告

日期：2026-05-29

測試資料：`data/sample_sentences.json`

## 測試設定

這次測的是 pre-trained 版本：

```text
model: google/gemma-3-4b-pt
base_url: http://localhost:8000/v1
vLLM: v0.21.0
GPU: NVIDIA L4 23034 MiB
```

vLLM 啟動參數：

```text
google/gemma-3-4b-pt
--served-model-name google/gemma-3-4b-pt
--host 0.0.0.0
--language-model-only
--max-model-len 8192
--gpu-memory-utilization 0.90
--enforce-eager
```

沒有使用量化。vLLM log 顯示：

```text
dtype=torch.bfloat16
quantization=None
architecture=Gemma3ForConditionalGeneration
```

## GPU 記憶體狀況

vLLM 載入 log：

```text
Checkpoint size: 8.01 GiB
Model loading took 7.82 GiB memory
Available KV cache memory: 10.99 GiB
GPU KV cache size: 176,721 tokens
Maximum concurrency for 8,192 tokens per request: 21.57x
```

結論：`google/gemma-3-4b-pt` 不量化放在 L4 很充裕。

## Pipeline 摘要

流程維持不變：

1. 用 vLLM completions `prompt_logprobs` 評原句。
2. 將 token logprob 對齊回原始字元位置。
3. 計算每個字的 risk score。
4. 選出 `risk_score >= 7.0` 的 suspicious chars，最多 5 個。
5. 從 word lexicon、char confusion、vLLM top alternatives 產生候選。
6. 對原始 local window 和候選 local window 重新評分。
7. 用 `delta = candidate_score - original_score` 排序。
8. 輸出 `corrected`、`uncertain` 或 `no_error`。

每次 vLLM request：

```json
{
  "model": "google/gemma-3-4b-pt",
  "prompt": "...",
  "max_tokens": 1,
  "temperature": 0,
  "prompt_logprobs": 5,
  "logprobs": 1
}
```

completion token 不參與判斷，只使用 `prompt_logprobs`。

## 整體結果

```text
total cases: 12
vLLM calls: 207
prompt chars scored: 3314
prompt tokens returned: 2694

corrected: 4
uncertain: 5
no_error: 3
```

## 每筆結果

```text
case  status      calls  prompt_chars  prompt_tokens  top_candidate
01    corrected   21     345           291            圜->園 delta=1.305 source=word_lexicon
02    uncertain   17     285           228            份->篇 delta=0.393 source=vllm_top_logprob
03    uncertain   18     304           271            提->屜 delta=0.857 source=word_lexicon
04    uncertain   18     287           239            戰->站 delta=0.722 source=word_lexicon
05    corrected   10     130           110            相->箱 delta=1.575 source=word_lexicon
06    corrected   15     195           168            誤->務 delta=1.947 source=word_lexicon
07    uncertain   19     283           215            汽->氣 delta=1.796 source=word_lexicon
08    corrected   21     357           266            李->理 delta=1.003 source=word_lexicon
09    uncertain   20     341           276            結->節 delta=0.579 source=word_lexicon
10    no_error    17     271           200            -
11    no_error    12     200           166            -
12    no_error    19     316           264            -
```

## 預期錯字命中狀況

```text
case  expected     result     note
01    公圜->公園    corrected  成功
02    檢察->檢查    uncertain  沒有輸出正確候選，top 是 份->篇
03    抽提->抽屜    uncertain  正確候選排第一，但 delta 未達 strong threshold
04    車戰->車站    uncertain  正確候選排第一，但 delta 未達 strong threshold
05    信相->信箱    corrected  成功
06    服誤->服務    corrected  成功
07    天汽->天氣    uncertain  正確候選排第一，但 decision 未放行
08    整李->整理    corrected  成功
09    細結->細節    uncertain  正確候選排第一，但 delta 偏弱
10    clean        no_error   OK
11    clean        no_error   OK
12    clean        no_error   OK
```

## Top Suspicious Chars

```text
case  top suspicious chars
01    圜@16:13.3, 散@17:10.6, 公@15:10.2
02    這@0:14.2, 份@1:10.1, 需@4:9.5
03    他@0:14.7, 提@7:13.1, 鑰@2:11.2
04    我@0:16.2, 們@1:16.2, 明@2:12.4
05    相@11:19.5, 請@0:17.8, 把@1:11.7
06    這@0:14.2, 誤@6:13.5, 服@5:11.9
07    汽@4:14.5, 很@5:13.5, 好@6:12.4
08    這@0:14.2, 李@7:11.2, 整@6:10.3
09    老@0:21.3, 闆@1:21.3, 提@2:14.2
10    我@0:15.3, 想@1:15.3, 先@2:10.7
11    這@0:14.2, 家@1:8.8, 下@13:7.3
12    可@4:13.9, 能@5:13.9, 會@6:13.9
```

## 觀察

這次結果有幾個明顯特徵：

- auto-correct 4 筆。
- 3 筆乾淨句最後都判 `no_error`。
- top candidate 大多是 `word_lexicon`，只有 case 02 的 top 是 `vllm_top_logprob`。

不過 case 02 `檢察->檢查` 還是漏掉。它的 top candidate 是：

```text
份->篇 delta=0.393 source=vllm_top_logprob
```

這代表目前 suspicious selection 和 candidate ranking 還是會被句首附近的高 risk 字干擾。

## 結論

`google/gemma-3-4b-pt` 不量化可以穩定放進 L4，資源壓力低。

在目前 pipeline 規則下，這次輸出如下：

```text
corrected: 4
uncertain: 5
no_error: 3
```

主要仍需改善：

1. `vllm_top_logprob` 候選過濾，避免 `份->篇` 這類無關替換干擾。
2. `word_lexicon` 候選應該有獨立 decision rule。
3. suspicious selection 要避免句首常見字和正常詞組過度觸發。
