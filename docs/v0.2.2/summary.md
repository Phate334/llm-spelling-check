# v0.2.2 測試綜合摘要

日期：2026-05-29

測試資料：`data/sample_sentences.json`

本目錄彙整 v0.2.2 的所有已完成測試報告，不只單次測試：

- 8 輪 FIM Structured Outputs 測試。
- 1 輪 no-FIM 追加測試。
- 每輪 12 個 sample cases，合計 108 個 case-run。

v0.2.2 測試的候選來源：

- `vllm_top_logprob`：沿用 prompt logprobs top alternatives。
- `fim_structured_output`：取 suspicious char 的 local window，將目標字挖空成 `＿`，要求 vLLM Structured Outputs 回傳 JSON array 單字候選。
- no-FIM 追加測試將 `fim_candidate_limit=0`，候選來源只保留 `vllm_top_logprob`。

每份單模型報告除了候選字與分數，也依照 `AGENTS.md` 紀錄 vLLM I/O：

- `.md` 報告紀錄累計 call 數、用途分布、request/response 文字量累計。
- `*-calls.jsonl` 紀錄每次 vLLM 呼叫的用途、主要 payload 欄位、回傳摘要、輸入/輸出 bytes。

## 指標說明

- `corrected`：pipeline 自動修正。
- `status_unc`：pipeline 狀態為 `uncertain`，有候選但未通過自動修正門檻。
- `no_error`：pipeline 沒有產生修正。
- `eval_ok`：輸出文字等於預期答案；乾淨句維持原文也算 ok。
- `eval_missed`：應修正但沒有修正。
- `eval_wrong`：自動修正成非預期答案。
- `eval_unc`：人工評估為不確定；通常代表候選方向可能接近，但 pipeline 沒有自動修正。
- `calls`：vLLM API 呼叫總數。
- `input_chars` / `output_chars`：JSON request / response 文字長度累計，用於粗估 API I/O 量。

## 全部結果表

```text
model                 mode    window  corrected  status_unc  no_error  eval_ok  eval_missed  eval_wrong  eval_unc  calls  input_chars  output_chars
google/gemma-4-E4B    fim     12      1          7           4         4        1            0           7         291    54822        1274494
google/gemma-4-E4B    fim     24      1          6           5         4        2            0           6         287    54916        1367243
google/gemma-4-E2B    fim     12      1          8           3         4        0            0           8         214    45696        902222
google/gemma-4-E2B    fim     24      1          8           3         4        0            0           8         201    44351        871606
google/gemma-3-4b-pt  fim     12      1          8           3         4        0            0           8         286    57022        1247735
google/gemma-3-4b-pt  fim     24      1          7           4         4        1            0           7         263    54462        1195675
google/gemma-3-1b-pt  fim     12      3          5           4         6        1            0           5         219    48054        914708
gemma-4-26b-a4b       fim     12      3          5           4         2        3            2           5         228    48573        1033130
gemma-4-26b-a4b       no-fim  12      4          5           3         3        1            3           5         159    20702        928889
```

`google/gemma-3-1b-pt` 的 window=24 實驗在使用者要求下停止。原因是小模型 Structured Outputs 表現不可靠且耗時偏高；已完成的 window=12 結果保留。

## 綜合統計

```text
scope        runs  case_runs  corrected  status_unc  no_error  eval_ok  eval_missed  eval_wrong  eval_unc  calls  input_chars  output_chars
all          9     108        16         59          33        35       9            5           59        2148   428598       9735702
fim_only     8     96         12         54          30        32       8            2           54        1989   407896       8806813
no_fim_only  1     12         4          5           3         3        1            3           5         159    20702        928889
```

整體來看：

- 全部 108 個 case-run 中，`eval_ok` 為 35，約 32.4%。
- FIM 測試 96 個 case-run 中，`eval_ok` 為 32，約 33.3%。
- no-FIM 追加測試 12 個 case-run 中，`eval_ok` 為 3，約 25.0%。
- 自動修正共 16 次，其中 5 次是誤修，整體自動修正誤修率約 31.2%。
- FIM-only 自動修正 12 次，其中 2 次誤修，誤修率約 16.7%。
- no-FIM 追加測試自動修正 4 次，其中 3 次誤修，誤修率 75.0%。

## 逐案例穩定性

```text
case  expected_error  eval_ok  eval_missed  eval_wrong  eval_unc  note
01    yes             0        1            1           7         公圜->公園 幾乎沒有穩定修好
02    yes             0        5            0           4         檢察->檢查 最常被漏判
03    yes             2        0            0           7         抽提->抽屜 有候選但多數未過自動修正門檻
04    yes             0        0            2           7         車戰->車站 沒有穩定修好，26B 兩輪還誤修
05    yes             7        1            0           1         信相->信箱 是最穩定的錯字修正
06    yes             1        1            1           6         服誤->服務 大多停在 uncertain
07    yes             1        1            1           6         天汽->天氣 大多停在 uncertain
08    yes             0        0            0           9         整李->整理 全部都未自動修正
09    yes             0        0            0           9         細結->細節 全部都未自動修正
10    no              8        0            0           1         乾淨句大多能維持不修
11    no              7        0            0           2         乾淨句大多能維持不修
12    no              9        0            0           0         最穩定的乾淨句
```

## 主要觀察

- v0.2.2 的主要問題不是「沒有候選」，而是「候選排序與自動修正門檻不夠可靠」。例如 `抽提->抽屜`、`天汽->天氣`、`細結->細節` 多輪都出現在 top candidate，但常停在 `uncertain`。
- FIM structured candidate 沒有改善整體 corrected 數。多數 top candidate 仍來自 `vllm_top_logprob`。
- 唯一明顯補到候選的是 `google/gemma-4-E4B` window=12 的 case 01：`圜->園` 由 `fim_structured_output` 產生並排第一，但 `delta=0.823`，低於自動修正門檻，所以仍為 `uncertain`。
- window 從 12 加倍到 24 沒有改善結果。E4B 和 3-4B 反而各多一筆 missed。
- 小模型的 Structured Outputs 不穩，尤其 1B 在 structured generation 上耗時明顯，且完成的 window=12 沒有看到 FIM source 成為 top candidate。
- FIM 方式大幅增加 vLLM calls 與 output payload。FIM-only 8 輪平均每輪約 248.6 calls；no-FIM 追加測試為 159 calls。
- `gemma-4-26b-a4b` 不是明顯升級。FIM 版本 `eval_ok=2`，no-FIM 版本 `eval_ok=3`，但 no-FIM 自動修正 4 次中有 3 次誤修。

## 結論

v0.2.2 的模擬 FIM 方向可以讓模型參考右文並補出少數 top-logprob 找不到的候選，但目前不值得直接當預設主策略。

綜合所有 v0.2.2 案例後，更重要的下一步不是增加候選來源，而是改善候選過濾與決策：

- 對 `vllm_top_logprob` 候選加入更嚴格的繁體中文單字有效性過濾。
- 對不同候選來源使用不同門檻，避免雜訊候選擠掉合理候選。
- 對常見錯字型態加入更可靠的 lexical 或 confusion-set 補強。
- 把 FIM 作為受控 fallback，只在 top-logprob 沒有可信候選時啟用，並限制 suspicious 數量來控制成本。
