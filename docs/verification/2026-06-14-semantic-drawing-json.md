# 验证报告: semantic-drawing-json

**日期:** 2026-06-14
**分支:** feat/llm-parsing
**基线:** cf841d6

## 验证结果: PASS

### 测试结果

| 检查项 | 结果 |
|--------|------|
| 后端单元测试 (30/30) | ✅ PASS |
| 前端构建 | ✅ PASS |
| OpenSpec 验证 | ✅ PASS |

### 覆盖场景

| Spec 场景 | 测试覆盖 |
|-----------|---------|
| Create basic shape | `test_interpret_drawing_returns_parsed_draw_envelope` |
| Standalone endpoint | `TestInterpretDrawingEndpoint` (7 tests) |
| Preserve transcript | `test_asr_returns_drawing_field_on_success` |
| Valid JSON parsing | `test_parse_model_json_accepts_valid_object` |
| Markdown fence stripping | `test_parse_model_json_strips_markdown_code_fence` |
| Non-JSON → parse_error | `test_parse_model_json_rejects_non_json_text`, `test_returns_parse_error_on_invalid_json` |
| Missing fields → parse_error | `test_interpret_drawing_returns_parse_error_on_missing_fields` |
| API failure → semantic_error | `test_returns_semantic_error_on_api_failure`, `test_asr_returns_semantic_error_when_model_fails` |
| Clarification (ambiguous) | `test_returns_clarification`, `test_interpret_drawing_returns_clarification_for_incomplete` |
| Non-drawing → no_op | `test_returns_noop`, `test_interpret_drawing_returns_noop_for_non_drawing` |
| Unsupported operation | `test_returns_unsupported` |
| Validation: unknown type | `test_validate_drawing_payload_rejects_unknown_type` |
| Validation: unknown shape | `test_validate_drawing_payload_rejects_create_with_unknown_shape` |
| Validation: unknown top-level | `test_validate_drawing_payload_rejects_unknown_top_level_field` |
| Validation: missing version | `test_validate_drawing_payload_rejects_missing_version` |

### 文件变更

- Create: `backend/drawing_interpreter.py` — Prompt + parse + validate + interpret
- Create: `backend/tests/test_drawing_interpreter.py` — 17 unit tests
- Create: `backend/tests/test_interpret_drawing_endpoint.py` — 7 endpoint tests
- Modify: `backend/main.py` — add `/api/interpret-drawing` + chain semantic in `/api/asr`
- Modify: `backend/tests/test_asr.py` — update for drawing field assertions
