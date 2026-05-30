# v0.2.3 測試摘要

日期：2026-05-30

測試資料：`data/sample_sentences.json`

v0.2.3 是 no-FIM baseline 整理版：

- 移除 FIM / Structured Outputs candidate path。
- 候選來源只保留 `vllm_top_logprob`。
- 新增 `score_batch_size`，目前測試皆使用預設值 `1`。
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

## 測試結果

共同參數：

```text
candidate_sources: vllm_top_logprob only
fim: removed
window_radius: 12
score_batch_size: 1
```

CSC metrics：

```text
model                 det_p   det_r   det_f1  corr_p  corr_r  corr_f1  fpr
gemma-4-26b-a4b       0.1000  0.6667  0.1739  0.2500  0.1111  0.1538   0.2700
google/gemma-3-270m   0.1525  1.0000  0.2647  0.0000  0.0000  0.0000   0.2500
```

計數：

```text
model                 detected  gold_errors  correct_detected  predicted  correct_corr  false_pos
gemma-4-26b-a4b       60        9            6                 4          1             54
google/gemma-3-270m   59        9            9                 0          0             50
```

Pipeline 與 vLLM I/O：

```text
model                 corrected  uncertain  no_error  score_calls  prompts  prompt_tokens  total_tokens
gemma-4-26b-a4b       4          5          3         147          147      1815           1962
google/gemma-3-270m   0          9          3         188          188      2518           2706
```

詳細報告：

- `gemma-4-26b-a4b-window12.md`
- `gemma-4-26b-a4b-window12-calls.jsonl`
- `google-gemma-3-270m-window12.md`
- `google-gemma-3-270m-window12-calls.jsonl`

## 與 v0.2.2 的差異

### 評估口徑改變

v0.2.2 summary 主要使用 `eval_ok`、`eval_wrong`、`eval_missed`、`eval_uncertain` 這類案例層級標記。v0.2.3 改成 CSC metrics 後，可以更清楚拆開 detection 與 correction。

這個新口徑讓問題更明確：目前 baseline 的 detection 偏寬，correction 又容易被 `vllm_top_logprob` 雜訊候選帶偏。

### FIM 已移除

v0.2.2 包含 FIM 測試與 no-FIM 追加測試。綜合觀察是 FIM 沒有穩定改善 corrected 數，且顯著增加 calls 與 output payload。

v0.2.3 直接移除 FIM 後，calls log 不再包含：

- `fim_candidates`
- `structured_outputs`
- JSON candidate generation

這讓 baseline 更乾淨，也比較適合後續逐步改善候選來源、prefilter、decision rule 與評估流程。

### 與 v0.2.2 no-FIM 追加測試相比

同樣是 `gemma-4-26b-a4b`、window=12、只用 `vllm_top_logprob`：

```text
version        corrected  uncertain  no_error  score_calls/calls  output_chars
v0.2.2 no-FIM  4          5          3         159                928889
v0.2.3         4          5          3         147                858375
```

pipeline 狀態分布沒有本質差異，仍是 4 corrected、5 uncertain、3 no_error。v0.2.3 的 call 數較低，主要是目前 pipeline 先收集同一句要評分的 windows，再去重後 scoring；`score_batch_size=1` 時仍是逐筆 request，但 `score_calls` 與 `scored_prompts` 已分開記錄。

## 270M 追加觀察

本輪使用 `http://localhost:8001/v1` 上實際註冊的 model id：`google/gemma-3-270m`。

- 270M 抓到全部 9 個 gold error positions，detection recall 達 `1.0000`。
- Detection precision 仍低，59 個 suspicious positions 中只有 9 個是真錯字，FPR 為 `0.2500`。
- 270M 沒有自動修正任何案例，9 個錯字案例全部進 `uncertain`。
- 多個 top candidate 其實抓到正確字，例如 `提->屜`、`相->箱`、`汽->氣`、`結->節`，但 decision rule 沒有放行成 corrected。
- 這代表 270M 在目前流程下比較像 high-recall detector / candidate suggester，不是可直接自動修正的模型。
- 270M 的 score calls 為 `188`，高於 26B 的 `147`，原因是它產生較多可評分 windows；成本不只取決於模型大小，也取決於 suspicious/candidate 數量。

## 主要觀察

- v0.2.3 的清理沒有改變模型能力本身；它讓 baseline 更乾淨，但品質瓶頸仍在。
- `vllm_top_logprob` 作為唯一候選來源仍不可靠，會把不少非錯字位置推成候選。
- 26B 有少量自動修正，但誤修不少；270M 不自動修正，但 recall 較高且部分 correct candidate 有進入 top candidate。
- Detection precision 與 FPR 仍是最需要優先改善的問題。
- Correction precision / recall 都低，表示即使抓到錯字位置，也需要更好的候選來源、候選篩選與 decision rule。
- `score_batch_size=1` 保持保守行為；提高 batch size 只改善 request 數與速度，不會直接改善品質。

## 結論

v0.2.3 達成了整理 baseline 的目的：移除 FIM、保留單一 `vllm_top_logprob` 候選來源、改用 CSC metrics、並把 `score_calls` 與 `scored_prompts` 分開記錄。

新增 270M 測試後，結論更清楚：目前流程的差異主要來自 detection/candidate/decision 的互動，不是單純模型越大越好。v0.3.0 應先改善 false positive 控制、scoring normalization、alignment robustness、candidate budget 與可重現的 evaluation/report CLI。
