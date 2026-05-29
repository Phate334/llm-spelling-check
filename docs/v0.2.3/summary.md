# v0.2.3 測試摘要

日期：2026-05-30

測試資料：`data/sample_sentences.json`

v0.2.3 是 no-FIM baseline 整理版：

- 移除 FIM / Structured Outputs candidate path。
- 候選來源只保留 `vllm_top_logprob`。
- 新增 `score_batch_size`，本輪使用預設值 `1`。
- 評估摘要改用 spelling check / CSC 常見指標。

## 指標說明

- `detection_precision`：被標成疑似錯字的位置中，有多少真的是錯字位置。這個值低代表 false positive 多。
- `detection_recall`：所有 gold 錯字位置中，有多少被系統抓到。這個值低代表漏抓錯字。
- `detection_f1`：Detection precision 與 recall 的調和平均。
- `correction_precision`：系統自動修正的位置中，有多少位置與修正字都正確。這個值低代表誤修多。
- `correction_recall`：所有 gold 錯字中，有多少被自動修正成正確字。
- `correction_f1`：Correction precision 與 recall 的調和平均。
- `false_positive_rate`：非錯字位置中，被系統標成疑似錯字的比例。

`corrected`、`uncertain`、`no_error` 仍保留作為 pipeline 狀態，但不再作為主要品質指標。

## 本輪結果

測試模型：

```text
model: gemma-4-26b-a4b
base_url: http://localhost:7072/v1
window_radius: 12
score_batch_size: 1
candidate_sources: vllm_top_logprob only
```

CSC metrics：

```text
detection_precision: 0.1000
detection_recall: 0.6667
detection_f1: 0.1739
correction_precision: 0.2500
correction_recall: 0.1111
correction_f1: 0.1538
false_positive_rate: 0.2700

detected_positions: 60
gold_error_positions: 9
correct_detected_positions: 6
predicted_corrections: 4
gold_corrections: 9
correct_corrections: 1
false_positive_positions: 54
gold_non_error_positions: 200
```

Pipeline 與 vLLM I/O：

```text
corrected: 4
uncertain: 5
no_error: 3
score_calls: 147
scored_prompts: 147
prompts_per_call: 1.0000
input_chars: 19129
output_chars: 858375
prompt_tokens: 1815
completion_tokens: 147
total_tokens: 1962
```

詳細報告：

- `gemma-4-26b-a4b-window12.md`
- `gemma-4-26b-a4b-window12-calls.jsonl`

## 與 v0.2.2 的差異

### 評估口徑改變

v0.2.2 summary 主要使用 `eval_ok`、`eval_wrong`、`eval_missed`、`eval_uncertain` 這類案例層級標記。v0.2.3 改成 CSC metrics 後，可以更清楚拆開 detection 與 correction：

- Detection recall `0.6667`：9 個 gold 錯字位置中，有 6 個被 suspicious detector 抓到。
- Detection precision `0.1000`：但總共標了 60 個 suspicious positions，只有 6 個是真錯字，false positive 很多。
- Correction precision `0.2500`：4 次自動修正中只有 1 次完全正確。
- Correction recall `0.1111`：9 個 gold 錯字中只有 1 個被自動修正正確。

這個新口徑讓問題更明確：v0.2.3 baseline 的 detection 偏寬，correction 又容易被 `vllm_top_logprob` 雜訊候選帶偏。

### FIM 已移除

v0.2.2 包含 8 輪 FIM 測試與 1 輪 no-FIM 追加測試。綜合觀察是 FIM 沒有穩定改善 corrected 數，且顯著增加 calls 與 output payload。

v0.2.3 直接移除 FIM 後，本輪 calls log 不再包含：

- `fim_candidates`
- `structured_outputs`
- JSON candidate generation

這讓 baseline 更乾淨，也比較符合後續 v0.3.0 要比較多候選來源的需求。

### 與 v0.2.2 no-FIM 追加測試相比

同樣是 `gemma-4-26b-a4b`、window=12、只用 `vllm_top_logprob`：

```text
version        corrected  uncertain  no_error  score_calls/calls  output_chars
v0.2.2 no-FIM  4          5          3         159                928889
v0.2.3         4          5          3         147                858375
```

pipeline 狀態分布沒有本質差異，仍是 4 corrected、5 uncertain、3 no_error。v0.2.3 的 call 數較低，主要是目前 pipeline 先收集同一句要評分的 windows，再去重後 scoring；`score_batch_size=1` 時仍是逐筆 request，但 `score_calls` 與 `scored_prompts` 已分開記錄。

品質觀察也沒有翻轉：

- case 03 `提->屜` 仍是唯一明確正確自動修正。
- case 04、06、07 仍有自動誤修。
- case 02、05、08、09 等仍沒有被正確自動修正。
- top candidate 仍常出現不合理替換，例如 `公->把`、`飯->一`、`汽->子`。

## 主要觀察

- v0.2.3 的清理沒有改變模型能力本身；它讓 baseline 更乾淨，但品質瓶頸仍在。
- `vllm_top_logprob` 作為唯一候選來源仍不可靠，會把不少非錯字位置推成候選。
- Detection recall 尚可，但 precision 很低，表示 risk threshold / suspicious selection 太寬。
- Correction precision 與 recall 都低，表示即使抓到錯字位置，也常缺少正確候選或候選排序不穩。
- 移除 FIM 後成本下降、流程更單純，但沒有改善正確率。
- `score_batch_size=1` 保持保守行為；後續可以提高 batch size 測試 throughput，但這只改善 request 數與速度，不會直接改善品質。

## 結論

v0.2.3 達成了整理 baseline 的目的：移除 FIM、保留單一 `vllm_top_logprob` 候選來源、改用 CSC metrics、並把 `score_calls` 與 `scored_prompts` 分開記錄。

和 v0.2.2 的核心觀察一致：主要問題不是 FIM 是否存在，而是 `vllm_top_logprob` 候選本身太雜，以及 suspicious detection false positive 過高。v0.3.0 應把重點放在更多候選來源、candidate prefilter、source-aware decision，以及和 SoftMaskedBERT 舊服務的同指標比較。
