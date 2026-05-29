# Google Gemma 3 1B PT 測試報告

日期：2026-05-29

測試資料：`data/sample_sentences.json`

## 使用模型

```text
model: google/gemma-3-1b-pt
base_url: http://localhost:8000/v1
vLLM: v0.21.0
GPU: NVIDIA L4
```

## 整體結果

```text
total cases: 12
vLLM calls: 202
prompt chars scored: 3265
prompt tokens returned: 2667

corrected: 5
uncertain: 3
no_error: 4
```

## 每筆結果

```text
case  status      calls  prompt_chars  prompt_tokens  top_candidate
01    corrected   22     361           304            圜->園 delta=1.612 source=word_lexicon
02    no_error    17     297           243            -
03    uncertain   19     343           295            提->屜 delta=1.061 source=word_lexicon
04    uncertain   18     287           239            戰->上 delta=0.863 source=vllm_top_logprob
05    corrected   11     143           123            相->箱 delta=1.256 source=word_lexicon
06    corrected   17     221           191            誤->務 delta=2.021 source=word_lexicon
07    corrected   13     193           146            汽->氣 delta=2.145 source=word_lexicon
08    corrected   19     321           239            李->理 delta=1.589 source=word_lexicon
09    uncertain   20     341           276            結->節 delta=0.810 source=word_lexicon
10    no_error    13     205           150            -
11    no_error    14     237           197            -
12    no_error    19     316           264            -
```

## 預期錯字命中狀況

```text
case  expected     result     note
01    公圜->公園    corrected  成功
02    檢察->檢查    no_error   漏掉
03    抽提->抽屜    uncertain  正確候選排第一，但未 auto-correct
04    車戰->車站    uncertain  正確候選排第 2，top 是 戰->上
05    信相->信箱    corrected  成功
06    服誤->服務    corrected  成功
07    天汽->天氣    corrected  成功
08    整李->整理    corrected  成功
09    細結->細節    uncertain  正確候選排第一，但 delta 偏弱
10    clean        no_error   OK
11    clean        no_error   OK
12    clean        no_error   OK
```

## 觀察

`google/gemma-3-1b-pt` 在這批資料上結果意外不錯：

- auto-correct 5 筆。
- 3 筆乾淨句都判 `no_error`。
- 大多數正確 top candidate 都來自 `word_lexicon`。

主要問題：

- case 02 `檢察->檢查` 漏掉，最後被判 `no_error`。
- case 04 `車戰->車站` 的正確候選有出現，但被 `vllm_top_logprob` 的 `戰->上` 壓過。
- case 03、09 的正確候選排第一，但因 decision rule 太保守，仍然是 `uncertain`。

## 結論

以目前 POC 規則來看，`google/gemma-3-1b-pt` 是值得保留的候選模型。

它成本低、速度快，在 sample set 上有 5 筆自動修正與 3 筆乾淨句 `no_error`。下一步還是應該優先調整 pipeline：

1. 過濾 `vllm_top_logprob` 候選，避免不合理替換干擾。
2. 讓 `word_lexicon` 走獨立 decision rule。
3. 針對 `檢察->檢查` 這種詞表命中，允許低 risk 也產生候選。
