# v0.2.6 CLI 測試摘要

日期：2026-06-01

本輪以目前 repo 的 SGML loader 與 `data/README` 現行口徑重新評估 SGML 訓練資料。loader 目前接受：

- 同一個 `ESSAY` 含多個 `PASSAGE`
- `location` 只要落在 `WRONG` span 內即可
- `WRONG` / `CORRECTION` 維持等長替換

本摘要平行紀錄四份資料集的 batch 測試結果。表格中的 `gold_errors` 在資料覆蓋段落使用 dataset metadata；計數段落則使用 evaluation metrics 實際納入評估的 `gold_error_positions`。

## 資料覆蓋

```text
dataset                                       run     status    cases  gold_errors  avg_len  p95_len  max_len
data/spreadsheets_docs_Training.sgml          batch2  complete  49     80           12.8     38       55
data/taipei_uniform_words_sent_Training.sgml  batch2  complete  80     81           34.2     77       311
data/C1_training.sgml                         batch2  complete  342    460          47.7     76       126
data/fiona_wrong_results_Training.sgml        batch8  complete  17     24           19.9     35       42
```

四份資料共 488 cases / 645 metadata gold errors；實際 evaluation metrics 納入 643 gold error positions。

## 測試設定

```text
base_url: http://localhost:8001/v1
requested_model: gemma-3-270m
registered_model: gemma-3-270m
root_model: google/gemma-3-270m
prompt_logprobs: 5
risk_threshold: 7.0
suspicious_limit: 5
candidate_limit: 8
window_radius: 12
score_batch_size: 2 or 8, recorded per dataset in run
strong_delta: 1.0
weak_delta: 0.3
margin: 0.4
```

batching 只改變 scoring request 的分組方式，不改變 prompt 內容與 decision rule。壓縮包內的結果檔保留完整 cases、候選字、分數、pipeline 狀態與 vLLM I/O 統計。

## 目前結果

```text
dataset                                       run     status    det_p   det_r   det_f1  corr_p  corr_r  corr_f1  fpr
data/spreadsheets_docs_Training.sgml          batch2  complete  0.2844  0.7949  0.4189  0.2500  0.0385  0.0667   0.2847
data/taipei_uniform_words_sent_Training.sgml  batch2  complete  0.0997  0.4815  0.1653  0.0000  0.0000  0.0000   0.1327
data/C1_training.sgml                         batch2  complete  0.0961  0.3565  0.1514  0.5000  0.0022  0.0043   0.0973
data/fiona_wrong_results_Training.sgml        batch8  complete  0.2143  0.7500  0.3333  0.0000  0.0000  0.0000   0.2095
```

整體加總：

```text
det_p   det_r   det_f1  corr_p  corr_r  corr_f1  fpr
0.1180  0.4401  0.1861  0.2857  0.0062  0.0122   0.1092
```

計數：

```text
dataset                                       run     status    detected  gold_errors  correct_detected  predicted  correct_corr  false_pos
data/spreadsheets_docs_Training.sgml          batch2  complete  218       78           62                12         3             156
data/taipei_uniform_words_sent_Training.sgml  batch2  complete  391       81           39                0          0             352
data/C1_training.sgml                         batch2  complete  1706      460          164               2          1             1542
data/fiona_wrong_results_Training.sgml        batch8  complete  84        24           18                0          0             66
total                                         mixed   complete  2399      643          283               14         4             2116
```

## Pipeline / vLLM I/O

```text
dataset                                       run     status    corrected  uncertain  no_error  score_calls  prompts  prompt_tokens  total_tokens
data/spreadsheets_docs_Training.sgml          batch2  complete  12         34         3         362          642      6367           7009
data/taipei_uniform_words_sent_Training.sgml  batch2  complete  0          32         48        596          1083     17618          18701
data/C1_training.sgml                         batch2  complete  2          146        194       2379         4263     72902          77165
data/fiona_wrong_results_Training.sgml        batch8  complete  0          12         5         53           227      2903           3130
total                                         mixed   complete  14         224        250       3390         6215     99790          106005
```

vLLM I/O 補充：

```text
dataset                                       prompts_per_call  completion_tokens  input_bytes  output_bytes  purpose_counts
data/spreadsheets_docs_Training.sgml          1.7735            642                63362        2953367       {"score_original": 49, "score_window": 313}
data/taipei_uniform_words_sent_Training.sgml  1.8171            1083               128707       7988692       {"score_original": 80, "score_window": 516}
data/C1_training.sgml                         1.7919            4263               559231       33250154      {"score_original": 342, "score_window": 2037}
data/fiona_wrong_results_Training.sgml        4.2830            227                15078        1284902       {"score_original": 17, "score_window": 36}
total                                         1.8333            6215               766378       45477115      {"score_original": 488, "score_window": 2902}
```

累計字元量：

```text
input_chars: 518632
output_chars: 44178438
```

## 產物

```text
docs/v0.2.6/v0.2.6-results.tar.gz
```

壓縮包內容：

```text
gemma-3-270m-spreadsheets_docs_Training-batch2-results.json
gemma-3-270m-spreadsheets_docs_Training-batch2-calls.jsonl
gemma-3-270m-taipei_uniform_words_sent_Training-batch2-results.json
gemma-3-270m-taipei_uniform_words_sent_Training-batch2-calls.jsonl
gemma-3-270m-C1_training-batch2-results.json
gemma-3-270m-C1_training-batch2-calls.jsonl
gemma-3-270m-fiona_wrong_results_Training-batch8-results.json
gemma-3-270m-fiona_wrong_results_Training-batch8-calls.jsonl
```

每個 `results.json` 記錄資料集 metadata、測試設定、metrics、status counts、vLLM I/O 累計與逐 case 候選字/分數；每個 `calls.jsonl` 逐次記錄 vLLM 呼叫用途、主要 payload 欄位與回傳重點欄位。

## 總結

目前作法能在四份資料上完成同一套 pipeline 評估，並把候選字、分數、decision 狀態與 vLLM I/O 成本一起落盤。整體 detection recall 為 `0.4401`，但 detection precision 只有 `0.1180`，false positive 仍偏多；correction recall 為 `0.0062`，代表 pipeline 即使偵測到可疑位置，也很少通過目前的 correction gate 自動修正。

現階段瓶頸主要在 risk 篩選過寬與 correction 放行過保守之間的落差：`risk_threshold=7.0` 搭配 `suspicious_limit=5` 會產生大量待評分位置，而 `strong_delta=1.0`、`weak_delta=0.3`、`margin=0.4` 使最終修正非常少。下一輪若要改善，應優先調整候選產生與 correction gate，並保留本輪的 vLLM I/O 統計格式，用來比較準確率變化是否伴隨 request 與 token 成本上升。
