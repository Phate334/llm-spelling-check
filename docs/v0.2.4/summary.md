# v0.2.4 SGML 測試摘要

日期：2026-05-30

測試資料：`data/fiona_wrong_results_Training.sgml`

本輪使用 v0.2.4 的 SGML loader，將 `PASSAGE` 作為 input，依 1-based `MISTAKE location` 套用 `CORRECTION` 產生 gold text，再用 CSC metrics 評估。

## 測試設定

```text
cases: 17
gold_errors: 24
candidate_sources: vllm_top_logprob only
fim: removed
window_radius: 12
score_batch_size: 1
```

model id：

- `http://localhost:7072/v1` requested `google/gemma-4-26b-a4b`，實際使用服務註冊的 `gemma-4-26b-a4b`。
- `http://localhost:8001/v1` 使用 `google/gemma-3-270m`。

## CSC Metrics

```text
model                 det_p   det_r   det_f1  corr_p  corr_r  corr_f1  fpr
gemma-4-26b-a4b       0.1647  0.5833  0.2569  0.0000  0.0000  0.0000   0.2254
google-gemma-3-270m   0.2143  0.7500  0.3333  0.0000  0.0000  0.0000   0.2095
```

計數：

```text
model                 detected  gold_errors  correct_detected  predicted  correct_corr  false_pos
gemma-4-26b-a4b       85        24           14                5          0             71
google-gemma-3-270m   84        24           18                0          0             66
```

## Pipeline / vLLM I/O

```text
model                 corrected  uncertain  no_error  calls  prompts  prompt_tokens  total_tokens
gemma-4-26b-a4b       5          11         1         203    203      2433           2636
google-gemma-3-270m   0          12         5         226    226      2901           3127
```

vLLM calls 紀錄：

- `gemma-4-26b-a4b-sgml-calls.jsonl`
- `gemma-4-26b-a4b-sgml-results.json`
- `google-gemma-3-270m-sgml-calls.jsonl`
- `google-gemma-3-270m-sgml-results.json`

## 案例摘要

### gemma-4-26b-a4b

```text
case                    status     top_candidate
fiona_wrong_results-1   uncertain 質->照 delta=0.952 source=vllm_top_logprob
fiona_wrong_results-2   corrected 函->第 delta=1.577 source=vllm_top_logprob
fiona_wrong_results-3   corrected 貴->降 delta=2.377 source=vllm_top_logprob
fiona_wrong_results-4   uncertain 函->碼 delta=0.897 source=vllm_top_logprob
fiona_wrong_results-5   no_error  -
fiona_wrong_results-6   corrected 費->把 delta=1.708 source=vllm_top_logprob
fiona_wrong_results-7   corrected 般->今 delta=2.511 source=vllm_top_logprob
fiona_wrong_results-8   uncertain 雞->能 delta=2.060 source=vllm_top_logprob
fiona_wrong_results-9   uncertain 笑->碼 delta=1.015 source=vllm_top_logprob
fiona_wrong_results-10  uncertain 笑->度 delta=1.646 source=vllm_top_logprob
fiona_wrong_results-11  uncertain 雞->应 delta=1.912 source=vllm_top_logprob
fiona_wrong_results-12  uncertain 的->專 delta=0.526 source=vllm_top_logprob
fiona_wrong_results-13  corrected 雞->以 delta=1.406 source=vllm_top_logprob
fiona_wrong_results-14  uncertain 烏->在 delta=1.874 source=vllm_top_logprob
fiona_wrong_results-15  uncertain 挑->照 delta=0.523 source=vllm_top_logprob
fiona_wrong_results-16  uncertain 訊->把 delta=1.478 source=vllm_top_logprob
fiona_wrong_results-17  uncertain 夠->後 delta=0.979 source=vllm_top_logprob
```

### google/gemma-3-270m

```text
case                    status     top_candidate
fiona_wrong_results-1   uncertain 笑->蛋 delta=0.490 source=vllm_top_logprob
fiona_wrong_results-2   no_error  -
fiona_wrong_results-3   uncertain 文->備 delta=0.491 source=vllm_top_logprob
fiona_wrong_results-4   uncertain 貴->興 delta=0.431 source=vllm_top_logprob
fiona_wrong_results-5   uncertain 部->社 delta=0.383 source=vllm_top_logprob
fiona_wrong_results-6   no_error  -
fiona_wrong_results-7   uncertain 添->晚 delta=1.705 source=vllm_top_logprob
fiona_wrong_results-8   uncertain 笑->排 delta=1.279 source=vllm_top_logprob
fiona_wrong_results-9   uncertain 笑->翼 delta=1.309 source=vllm_top_logprob
fiona_wrong_results-10  uncertain 笑->翼 delta=1.206 source=vllm_top_logprob
fiona_wrong_results-11  uncertain 效->排 delta=0.871 source=vllm_top_logprob
fiona_wrong_results-12  uncertain 雞->质 delta=1.197 source=vllm_top_logprob
fiona_wrong_results-13  uncertain 笑->達 delta=0.861 source=vllm_top_logprob
fiona_wrong_results-14  no_error  -
fiona_wrong_results-15  uncertain 老->嘛 delta=0.532 source=vllm_top_logprob
fiona_wrong_results-16  no_error  -
fiona_wrong_results-17  no_error  -
```

## 觀察

- 26B detection recall 為 `0.5833`，270M detection recall 為 `0.7500`；兩者都漏抓不少 SGML gold positions。
- 26B correction recall 為 `0.0000`，270M correction recall 為 `0.0000`；目前自動修正能力在 SGML 資料上仍弱。
- 26B 產生 5 次 `corrected`，但沒有任何一次符合 gold correction，表示目前 decision rule 仍會放行錯誤候選。
- 270M 沒有產生自動修正，12 筆進 `uncertain`、5 筆進 `no_error`；它比 26B 更保守，但仍漏掉多個 gold correction。
- 兩個模型的 false positive rate 都偏高，延續 v0.2.3 的核心問題：`vllm_top_logprob` 單一候選來源與目前 risk selection 仍不夠穩。
- calls 數量主要由 suspicious positions 與候選 windows 數決定，不只由模型大小決定。

## 結論

v0.2.4 的 SGML loader 能正常把標註資料轉成 evaluation dataset，並讓兩個模型用同一套 CSC metrics 比較。結果顯示，目前 no-FIM / top-logprob baseline 在較多 SGML case 上仍有 detection 與 correction 兩層瓶頸；後續改善應優先處理 false positive、候選來源、scoring normalization 與 decision rule。

## SGML / Metrics 口徑

- `location` 使用 1-based character offset。
- gold text 由 `WRONG` 等長替換為 `CORRECTION` 產生。
- Detection 指標比較 `suspicious_chars` indexes 與 gold error positions。
- Correction 指標只計入 `status == corrected` 的自動修正。
- vLLM I/O JSONL 每行包含用途、主要 payload 欄位、回傳重點欄位、usage、輸入/輸出 chars/bytes。
