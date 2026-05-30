# API Reference

v0.2.5 提供 FastAPI WebUI 與分段 API。範例預設使用：

```json
{
  "base_url": "http://localhost:7072/v1",
  "model": "gemma-4-26b-a4b"
}
```

`settings.api_key` 可以送入 request，但 response 的 `settings` 不會回傳 API key。

## GET /

用途：回傳 WebUI。

Response：`text/html`

## POST /api/parse

用途：把手動文字、JSON 或 SGML input 解析成 normalized cases。

Content type：`application/json` 或 `multipart/form-data`

JSON request：

```json
{
  "text": "這份報告需要再檢察一次。"
}
```

Response：

```json
{
  "cases": [
    {
      "id": "text-1",
      "input": "這份報告需要再檢察一次。",
      "gold": null,
      "source_format": "text"
    }
  ]
}
```

Multipart request 可用欄位：

- `file`: `.json`、`.sgml` 或純文字檔
- `text`: 可選；有 `file` 時以 file 為主

## POST /api/detect

用途：只跑 detection，回傳 suspicious chars 和候選數量，不做 correction decision。

Content type：`application/json`

Request：

```json
{
  "cases": [
    {
      "id": "case-1",
      "input": "我今天想喝一杯咖非。",
      "gold": null,
      "source_format": "text"
    }
  ],
  "settings": {
    "base_url": "http://localhost:7072/v1",
    "model": "gemma-4-26b-a4b",
    "config": {
      "prompt_logprobs": 5,
      "risk_threshold": 7.0,
      "suspicious_limit": 5,
      "candidate_limit": 8,
      "score_batch_size": 1
    }
  }
}
```

Response：

```json
{
  "settings": {
    "base_url": "http://localhost:7072/v1",
    "model": "gemma-4-26b-a4b",
    "timeout": 30.0,
    "config": {
      "prompt_logprobs": 5,
      "risk_threshold": 7.0,
      "suspicious_limit": 5,
      "candidate_limit": 8,
      "window_radius": 12,
      "score_batch_size": 1,
      "strong_delta": 1.0,
      "weak_delta": 0.3,
      "margin": 0.4
    }
  },
  "cases": [
    {
      "id": "case-1",
      "input": "我今天想喝一杯咖非。",
      "gold": null,
      "source_format": "text",
      "suspicious_chars": [
        {
          "index": 8,
          "char": "非",
          "risk_score": 8.0,
          "token_logprob": -8.0,
          "span_score": null,
          "reason": "低字元或局部 span likelihood"
        }
      ],
      "candidate_count": 1
    }
  ]
}
```

## POST /api/correct

用途：跑完整 spelling check pipeline，回傳 suspicious chars、corrections、candidate scores；如果所有 cases 都有 `gold`，同時回傳 CSC metrics。

Content type：`application/json`

Request：

```json
{
  "cases": [
    {
      "id": "case-1",
      "input": "我今天想喝一杯咖非。",
      "gold": "我今天想喝一杯咖啡。",
      "source_format": "json"
    }
  ],
  "settings": {
    "base_url": "http://localhost:7072/v1",
    "model": "gemma-4-26b-a4b",
    "config": {
      "risk_threshold": 7.0,
      "score_batch_size": 1
    }
  }
}
```

Response：

```json
{
  "settings": {
    "base_url": "http://localhost:7072/v1",
    "model": "gemma-4-26b-a4b",
    "timeout": 30.0,
    "config": {
      "prompt_logprobs": 5,
      "risk_threshold": 7.0,
      "suspicious_limit": 5,
      "candidate_limit": 8,
      "window_radius": 12,
      "score_batch_size": 1,
      "strong_delta": 1.0,
      "weak_delta": 0.3,
      "margin": 0.4
    }
  },
  "summary": {
    "case_count": 1,
    "corrected": 1,
    "uncertain": 0,
    "no_error": 0,
    "suspicious_count": 1,
    "candidate_count": 1
  },
  "metrics": {
    "detection_precision": 1.0,
    "detection_recall": 1.0,
    "detection_f1": 1.0,
    "correction_precision": 1.0,
    "correction_recall": 1.0,
    "correction_f1": 1.0,
    "false_positive_rate": 0.0
  },
  "cases": [
    {
      "id": "case-1",
      "input": "我今天想喝一杯咖非。",
      "gold": "我今天想喝一杯咖啡。",
      "source_format": "json",
      "status": "corrected",
      "corrected_text": "我今天想喝一杯咖啡。",
      "confidence": "high",
      "suspicious_chars": [
        {
          "index": 8,
          "char": "非",
          "risk_score": 8.0,
          "token_logprob": -8.0,
          "span_score": null,
          "reason": "低字元或局部 span likelihood"
        }
      ],
      "corrections": [
        {
          "index": 8,
          "original_char": "非",
          "candidate_char": "啡",
          "source": "vllm_top_logprob",
          "original_text": "我今天想喝一杯咖非。",
          "candidate_text": "我今天想喝一杯咖啡。",
          "original_score": -4.5,
          "candidate_score": -1.0,
          "delta": 3.5,
          "original_span": "非",
          "corrected_span": "啡"
        }
      ]
    }
  ]
}
```

## POST /api/evaluate

用途：對已完成 correction 的 cases 計算 CSC metrics。沒有 gold 或 gold 不完整時，`metrics` 會是 `null`。

Content type：`application/json`

Request：

```json
{
  "cases": [
    {
      "id": "case-1",
      "input": "咖非",
      "gold": "咖啡",
      "source_format": "json",
      "status": "corrected",
      "corrected_text": "咖啡",
      "confidence": "high",
      "suspicious_chars": [
        {
          "index": 1,
          "char": "非",
          "risk_score": 8.0,
          "token_logprob": -8.0,
          "span_score": null,
          "reason": "低字元或局部 span likelihood"
        }
      ],
      "corrections": [
        {
          "index": 1,
          "original_char": "非",
          "candidate_char": "啡",
          "source": "vllm_top_logprob",
          "original_text": "咖非",
          "candidate_text": "咖啡",
          "original_score": -4.5,
          "candidate_score": -1.0,
          "delta": 3.5,
          "original_span": "非",
          "corrected_span": "啡"
        }
      ]
    }
  ]
}
```

Response：

```json
{
  "metrics": {
    "detection_precision": 1.0,
    "detection_recall": 1.0,
    "detection_f1": 1.0,
    "correction_precision": 1.0,
    "correction_recall": 1.0,
    "correction_f1": 1.0,
    "false_positive_rate": 0.0,
    "detected_positions": 1,
    "gold_error_positions": 1,
    "correct_detected_positions": 1,
    "predicted_corrections": 1,
    "gold_corrections": 1,
    "correct_corrections": 1,
    "false_positive_positions": 0,
    "gold_non_error_positions": 1
  }
}
```

## POST /api/run

用途：WebUI 使用的一次完成 API。會 parse input，再跑 correction；有 gold 時回傳 metrics，沒有 gold 時 `metrics` 為 `null`。

Content type：`application/json` 或 `multipart/form-data`

JSON request：

```json
{
  "text": "我今天想喝一杯咖非。",
  "settings": {
    "base_url": "http://localhost:7072/v1",
    "model": "gemma-4-26b-a4b",
    "config": {
      "risk_threshold": 7.0,
      "score_batch_size": 1
    }
  }
}
```

Multipart request 可用欄位：

- `file`: `.json`、`.sgml` 或純文字檔
- `text`: 可選
- `settings`: JSON string

Response：

```json
{
  "settings": {
    "base_url": "http://localhost:7072/v1",
    "model": "gemma-4-26b-a4b",
    "timeout": 30.0,
    "config": {
      "prompt_logprobs": 5,
      "risk_threshold": 7.0,
      "suspicious_limit": 5,
      "candidate_limit": 8,
      "window_radius": 12,
      "score_batch_size": 1,
      "strong_delta": 1.0,
      "weak_delta": 0.3,
      "margin": 0.4
    }
  },
  "summary": {
    "case_count": 1,
    "corrected": 1,
    "uncertain": 0,
    "no_error": 0,
    "suspicious_count": 1,
    "candidate_count": 1
  },
  "metrics": null,
  "cases": [
    {
      "id": "text-1",
      "input": "我今天想喝一杯咖非。",
      "gold": null,
      "source_format": "text",
      "status": "corrected",
      "corrected_text": "我今天想喝一杯咖啡。",
      "confidence": "high",
      "suspicious_chars": [
        {
          "index": 8,
          "char": "非",
          "risk_score": 8.0,
          "token_logprob": -8.0,
          "span_score": null,
          "reason": "低字元或局部 span likelihood"
        }
      ],
      "corrections": [
        {
          "index": 8,
          "original_char": "非",
          "candidate_char": "啡",
          "source": "vllm_top_logprob",
          "original_text": "我今天想喝一杯咖非。",
          "candidate_text": "我今天想喝一杯咖啡。",
          "original_score": -4.5,
          "candidate_score": -1.0,
          "delta": 3.5,
          "original_span": "非",
          "corrected_span": "啡"
        }
      ]
    }
  ]
}
```
