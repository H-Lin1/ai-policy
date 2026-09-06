from __future__ import annotations

import re
from datetime import UTC, date, datetime
from urllib.parse import urlsplit

from .schemas import AdminPolicyInput, MarkdownParseItem

ALLOWED_FIELDS = {"title", "document_no", "issuing_organization", "published_date", "effective_status", "source_url", "document_url"}
STATUSES = {"active", "pending", "expired", "repealed", "unknown"}
MAX_MARKDOWN_BYTES = 2 * 1024 * 1024

EXAMPLE_MARKDOWN = """---
title: 深圳市科技创新专项资金管理办法
document_no: 深科技创新规〔2026〕1号
issuing_organization: 深圳市科技创新局
published_date: 2026-08-20
effective_status: active
source_url: https://example.sz.gov.cn/policies/2026/001
document_url: https://example.sz.gov.cn/files/2026/001.pdf
---

# 深圳市科技创新专项资金管理办法

## 第一章 总则

第一条 为规范深圳市科技创新专项资金管理，提高财政资金使用效益，根据有关规定，制定本办法。

第二条 本办法适用于深圳市科技创新专项资金的申请、审核、使用和监督管理。
"""


def _scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1].strip()
    return value


def _valid_http_url(value: str | None) -> bool:
    if not value:
        return True
    parsed = urlsplit(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and not parsed.username and not parsed.password and not parsed.fragment


def parse_markdown(filename: str, content: str) -> MarkdownParseItem:
    errors: list[str] = []
    warnings: list[str] = []
    if not filename.lower().endswith(".md"):
        return MarkdownParseItem(filename=filename, status="failed", errors=["仅支持 .md 文件"])
    if len(content.encode("utf-8")) > MAX_MARKDOWN_BYTES:
        return MarkdownParseItem(filename=filename, status="failed", errors=["文件超过 2 MB"])
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", content, re.DOTALL)
    if not match:
        return MarkdownParseItem(filename=filename, status="failed", errors=["缺少有效的 YAML front matter"])
    metadata: dict[str, str] = {}
    for index, line in enumerate(match.group(1).splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"第 {index} 行不是 key: value 格式")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key not in ALLOWED_FIELDS:
            warnings.append(f"忽略未知字段：{key}")
            continue
        metadata[key] = _scalar(value)
    body = match.group(2).strip()
    for key in ("title", "issuing_organization", "published_date", "effective_status"):
        if not metadata.get(key):
            errors.append(f"缺少必填字段：{key}")
    if not body:
        errors.append("政策正文不能为空")
    try:
        published_date = date.fromisoformat(metadata.get("published_date", ""))
    except ValueError:
        published_date = datetime.now(UTC).date()
        errors.append("published_date 必须使用 YYYY-MM-DD")
    if metadata.get("effective_status") not in STATUSES:
        errors.append("effective_status 不受支持")
    for key in ("source_url", "document_url"):
        if not _valid_http_url(metadata.get(key)):
            errors.append(f"{key} 必须是有效的 HTTP(S) 地址")
    if errors:
        return MarkdownParseItem(filename=filename, status="failed", errors=errors, warnings=warnings)
    fields = AdminPolicyInput(
        title=metadata["title"], document_no=metadata.get("document_no") or None,
        issuing_organization=metadata["issuing_organization"], source_url=metadata.get("source_url") or None,
        document_url=metadata.get("document_url") or None, published_date=published_date,
        effective_status=metadata["effective_status"], content_text=body, source_type="markdown",
        original_filename=filename, raw_markdown=content,
    )
    return MarkdownParseItem(filename=filename, status="warning" if warnings else "ready", fields=fields, warnings=warnings)
