# Google Gemma 3 4B IT 測試報告

日期：2026-05-29

測試資料：`data/sample_sentences.json`

## 測試設定

這次測的是 instruction-tuned 版本：

```text
model: google/gemma-3-4b-it
base_url: http://localhost:8000/v1
vLLM: v0.21.0
GPU: NVIDIA L4 23034 MiB
```

vLLM 啟動參數：

```text
google/gemma-3-4b-it
--served-model-name google/gemma-3-4b-it
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

註：因為後續容器被重建，這份報告沒有保留完整的 IT 載入後 GPU memory log。checkpoint 下載時顯示約 `8.01 GiB`，L4 放得下。

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
  "model": "google/gemma-3-4b-it",
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
vLLM calls: 186
prompt chars scored: 2881
prompt tokens returned: 2334

corrected: 3
uncertain: 7
no_error: 2
```

## 每筆結果

```text
case  status      calls  prompt_chars  prompt_tokens  top_candidate
01    uncertain   19     289           238            圜->園 delta=1.725 source=word_lexicon
02    uncertain   10     161           128            份->T delta=0.997 source=vllm_top_logprob
03    uncertain   16     264           238            提->屜 delta=1.694 source=word_lexicon
04    uncertain   17     274           229            戰->上 delta=1.515 source=vllm_top_logprob
05    corrected   12     156           133            相->箱 delta=2.938 source=word_lexicon
06    corrected   16     208           179            誤->務 delta=2.841 source=word_lexicon
07    corrected   19     283           216            汽->氣 delta=2.591 source=word_lexicon
08    uncertain   15     249           181            份->T delta=1.492 source=vllm_top_logprob
09    uncertain   18     295           238            結->節 delta=1.019 source=word_lexicon
10    no_error    17     273           198            -
11    no_error    7      104           87             -
12    uncertain   20     325           269            下->T delta=0.336 source=vllm_top_logprob
```

## 預期錯字命中狀況

```text
case  expected     result     note
01    公圜->公園    uncertain  正確候選排第一，但未 auto-correct
02    檢察->檢查    uncertain  沒有輸出正確候選，top 是 份->T
03    抽提->抽屜    uncertain  正確候選排第一，但未 auto-correct
04    車戰->車站    uncertain  正確候選存在但排第 3，top 是 戰->上
05    信相->信箱    corrected  成功
06    服誤->服務    corrected  成功
07    天汽->天氣    corrected  成功
08    整李->整理    uncertain  正確候選排第 2，top 是 份->T
09    細結->細節    uncertain  正確候選排第一，但未 auto-correct
10    clean        no_error   OK
11    clean        no_error   OK
12    clean        uncertain  false positive，下->T
```

## Top Suspicious Chars

```text
case  top suspicious chars
01    今@1:19.7, 天@2:19.7, 圜@16:16.6
02    份@1:27.4, 這@0:20.0, 報@2:16.2
03    把@1:28.8, 提@7:28.5, 鑰@2:21.0
04    明@2:26.1, 天@3:26.1, 們@1:20.3
05    把@1:34.5, 相@11:34.4, 請@0:25.8
06    誤@6:20.6, 間@1:20.4, 這@0:16.5
07    的@2:31.8, 天@3:31.8, 汽@4:27.9
08    份@1:27.4, 這@0:20.0, 資@2:17.2
09    提@2:26.8, 醒@3:26.8, 闆@1:23.5
10    先@2:15.6, 想@1:15.4, 我@0:15.3
11    家@1:15.9, 這@0:14.2, 餐@2:10.7
12    下@2:25.1, 午@3:25.1, 可@4:20.3
```

## 觀察

Gemma 3 4B IT 的 risk 分數尺度偏高，很多正常字也會過 `risk_threshold=7.0`。

`vllm_top_logprob` 仍然會產生不適合作為繁中錯字修正的候選，例如：

```text
份->T
下->T
```

這會干擾排序，甚至把正確的 `word_lexicon` 候選擠到後面。

## 結論

`google/gemma-3-4b-it` 可以在 L4 上不量化執行，整體資源壓力應該不高。

就目前 pipeline 規則來看，IT 版本有幾個優點：

- 成功 auto-correct 3 筆。
- `信相->信箱`、`服誤->服務`、`天汽->天氣` 的 delta 很高。
- 乾淨句 case 10、11 都判為 `no_error`。

主要問題：

- risk threshold 需要重新校準。
- top-logprob 候選太髒，必須先過濾。
- `word_lexicon` 候選應該有獨立 decision rule，不該跟 top-logprob 候選混排。
