# RedHatAI Gemma 4 26B A4B NVFP4 樣本資料流分析

日期：2026-05-29

輸入資料：`data/sample_sentences.json`

這份分析是用以下模型跑出來的：

```text
model: RedHatAI/gemma-4-26B-A4B-it-NVFP4
base_url: http://localhost:8000/v1
vLLM: v0.21.0
```

compose service 已改成提供：

```text
RedHatAI/gemma-4-26B-A4B-it-NVFP4
```

vLLM logs 顯示這個模型是以 `compressed-tensors` 和 `MarlinNvFp4LinearKernel` 載入的。vLLM 也警告 GPU 沒有原生 FP4 支援，所以會透過 Marlin 使用 only-weight FP4 compression，效能可能會受影響。另一個警告提到，parallel layers 的 global NVFP4 scales 如果不同，可能會讓準確率下降。

這些結果都跟模型與目前閾值設定綁定。

## Pipeline 摘要

拼字檢查 pipeline 維持固定設定：

1. Score the full sentence with vLLM completions `prompt_logprobs`.
2. Align prompt token logprobs back to original character positions.
3. Compute character risk from token logprob and local span score.
4. Select suspicious chars with `risk_score >= 7.0`, limited to 5 chars.
5. Generate candidates from:
   - word-level confusion lexicon
   - char-level confusion table
   - vLLM top prompt alternatives
6. Rescore original and candidate local windows.
7. Rank candidates by `delta = candidate_score - original_score`.
8. 決定 `corrected`、`uncertain` 或 `no_error`。

每次 vLLM request 都會用：

```json
{
  "model": "RedHatAI/gemma-4-26B-A4B-it-NVFP4",
  "prompt": "...",
  "max_tokens": 1,
  "temperature": 0,
  "prompt_logprobs": 5,
  "logprobs": 1
}
```

生成出來的 completion token 會被忽略，真正拿來用的只有 `prompt_logprobs`。

## 整體結果

```text
total cases: 12
vLLM calls: 275
prompt chars scored: 4472
prompt tokens returned: 3377

corrected: 1
uncertain: 9
no_error: 2
```

這次在固定閾值和候選規則下，vLLM top alternatives 產生了不少不適合作為繁中修正的候選，最後決策偏不穩。

## 各案例摘要

```text
case  status      calls  prompt_chars  prompt_tokens  output_tokens  top_candidate
01    uncertain   23     389           305            23             圜->者 delta=1.372 source=vllm_top_logprob
02    uncertain   20     355           261            20             份->가 delta=1.345 source=vllm_top_logprob
03    uncertain   19     313           256            19             提->屜 delta=1.346 source=word_lexicon
04    uncertain   26     418           324            26             戰->上 delta=1.392 source=vllm_top_logprob
05    no_error    20     260           216            20             -
06    uncertain   23     299           241            23             誤->務 delta=0.828 source=word_lexicon
07    uncertain   25     375           263            25             天->_ delta=1.613 source=vllm_top_logprob
08    corrected   25     414           285            25             李->理 delta=1.347 source=word_lexicon
09    uncertain   15     273           214            15             注->로 delta=0.462 source=vllm_top_logprob
10    uncertain   24     415           273            24             筆->這 delta=0.620 source=vllm_top_logprob
11    uncertain   26     486           374            26             家-># delta=1.021 source=vllm_top_logprob
12    no_error    29     475           365            29             -
```

`output_tokens` 會等於呼叫次數，因為每次 request 都只要求 vLLM 生成 `max_tokens=1`。

## 預期修正

最後只有一個預期修正真的有自動套用：

```text
case  expected     result     note
01    公圜->公園    uncertain  top returned candidate was 圜->者
02    檢察->檢查    uncertain  top returned candidate was 份->가
03    抽提->抽屜    uncertain  correct top candidate, but still not auto-corrected
04    車戰->車站    uncertain  expected candidate appeared in returned top corrections with delta=0.979, but top was 戰->上
05    信相->信箱    no_error   expected correction not surfaced in final result
06    服誤->服務    uncertain  correct top candidate, delta below strong threshold
07    天汽->天氣    uncertain  top returned candidate was 天->_
08    整李->整理    corrected  success
09    細結->細節    uncertain  top returned candidate was 注->로
10    clean        uncertain  false positive on 筆->這
11    clean        uncertain  false positive on 家->#
12    clean        no_error   acceptable final decision, but expensive
```

注意：目前的 result object 對 `uncertain` 只保留前三個修正，對 `no_error` 則不保留 candidate details。當某個預期修正在結果裡顯示沒有出現時，它可能其實有在內部生成過，只是沒有活到最後輸出。

## 最可疑字元

```text
case  top suspicious chars
01    圜@16:21.2, 散@17:18.6, 去@14:17.9
02    一@9:16.7, 次@10:16.7, 份@1:15.5
03    提@7:20.5, 找@15:19.6, 不@16:19.6
04    遲@14:18.6, 見@9:18.5, 明@2:17.8
05    寄@6:15.2, 錄@5:15.2, 紀@4:15.1
06    飯@2:17.0, 店@3:17.0, 間@1:16.5
07    的@2:21.6, 天@3:21.6, 出@10:21.0
08    李@7:17.9, 好@8:16.6, 份@1:15.6
09    注@6:20.5, 意@7:20.5, 家@5:17.6
10    費@9:14.8, 確@3:14.4, 認@4:14.4
11    麵@7:18.4, 很@8:18.2, 好@9:18.1
12    下@2:19.3, 午@3:19.3, 可@4:18.7
```

這次的 risk scale 偏高。用目前固定的 `risk_threshold=7.0`，幾乎每句都會冒出多個 suspicious chars，而且裡面有不少其實是正常字元。

## 失敗分析

### vLLM Top Alternatives 很雜

有不少 top candidate 來自 `vllm_top_logprob`，而且對繁體中文拼字修正來說明顯不合理：

```text
份->가
天->_
注->로
家->#
```

這表示這個模型吐出來的 top-logprob alternatives 如果沒有更嚴格過濾，不能直接信。

可能的修法：

- 只保留單一個繁體中文 CJK 候選。
- 丟掉 ASCII 標點、符號、拉丁字母、韓文、假名，以及 tokenizer artifact。
- 如果 `word_lexicon` 候選和 `vllm_top_logprob` 候選同時存在，優先用前者。

### 同一組閾值不能直接沿用

同樣的 `risk_threshold=7.0` 套到這個模型後，乾淨句子或上下文合理的文字也會冒出很多 suspicious chars。

例如：

```text
case 11 clean sentence:
麵 risk=18.4
很 risk=18.2
好 risk=18.1

case 12 clean sentence:
下 risk=19.3
午 risk=19.3
可 risk=18.7
```

可能的修法：

- 針對不同模型重新校準 risk threshold。
- 改用 percentile 或相對 local ranking，不要只靠絕對閾值。
- 在挑 suspicious chars 之前，先處理句首位置和 multi-char-token 的情況。

### 正確的字詞 lexicon 候選被蓋掉或被拒掉

有些 word-lexicon 候選其實是對的，但最後還是沒進到 `corrected`：

```text
抽提->抽屜 delta=1.346, status=uncertain
服誤->服務 delta=0.828, status=uncertain
車戰->車站 delta=0.979, but top candidate was 戰->上
```

目前的 decision logic 會把所有候選來源混在一起比。很雜的 `vllm_top_logprob` 候選會把可信 lexicon 候選擠下去。

可能的修法：

- 把可信 lexicon 候選獨立排序。
- 對 `word_lexicon` 和 `vllm_top_logprob` 用不同閾值。
- 要求 `vllm_top_logprob` 候選先通過更嚴格的有效性過濾。

### 呼叫成本

這次總共跑了：

```text
275 vLLM calls
```

呼叫成本主要來自很多 suspicious chars 通過閾值，進而產生更多 candidate rescoring windows。

## 結論

以目前的 PoC 規則來看，`RedHatAI/gemma-4-26B-A4B-it-NVFP4` 在這份樣本集上的決策不穩。

問題不只是模型品質而已。pipeline 預設了固定的 logprob 閾值，也把 vLLM top alternatives 接得太寬鬆。這個模型的 risk scale 和 top alternatives 差異夠大，導致現有規則整個不穩定。

在把這個模型正式拿來跑 PoC 之前，下一步應該先做這些調整：

1. 把 `vllm_top_logprob` 候選過濾成有效的繁體中文單字替換。
2. 優先使用精準命中的字詞層級 confusion，而不是 top-logprob alternatives。
3. 依模型重新校準 `risk_threshold`、`strong_delta`、`weak_delta` 和 `margin`。
4. 降低沒有可信候選的 suspicious chars 的 rescoring 成本。
