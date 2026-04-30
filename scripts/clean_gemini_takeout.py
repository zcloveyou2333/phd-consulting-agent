#!/usr/bin/env python3
"""Clean Google Takeout Gemini activity into structured local files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime
from html import unescape
from pathlib import Path
from urllib.parse import unquote


MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}

RELEVANCE_KEYWORDS = [
    "博士",
    "phd",
    "申请",
    "导师",
    "套磁",
    "cv",
    "简历",
    "rp",
    "sop",
    "ps",
    "research proposal",
    "personal statement",
    "学校",
    "院校",
    "选校",
    "香港",
    "港",
    "澳门",
    "澳",
    "新加坡",
    "英国",
    "澳洲",
    "美国",
    "案例",
    "背景",
    "奖学金",
    "雅思",
    "托福",
    "gpa",
    "专业",
    "研究方向",
    "润色",
    "邮件",
    "文书",
    "家长",
    "留学",
    "全奖",
]

TASK_PATTERNS = [
    (
        "student_profile_analysis",
        ["背景分析", "这是我学生的背景", "学生的背景", "帮我分析", "背景评估"],
    ),
    (
        "school_supervisor_matching",
        ["哪些学校", "导师和项目", "帮我查所有符合", "学校有", "选校", "院校建议"],
    ),
    (
        "research_direction_design",
        ["研究方向", "推荐方向", "选题", "rp选题", "sop选题", "方向吗", "走什么方向"],
    ),
    (
        "confidence_case_generation",
        ["背景不如", "增加他的信心", "增加她的信心", "案例", "成功案例"],
    ),
    (
        "document_polishing",
        ["润色", "修改", "改一下", "重新发我", "文书", "帮我写", "发我不要表格"],
    ),
    (
        "program_fact_check",
        ["是哪年到哪年", "排名", "有这个专业吗", "都会学什么课程", "截止日期"],
    ),
    (
        "outreach_email",
        ["套磁", "邮件", "email", "回信"],
    ),
    (
        "workflow_or_skill_design",
        ["skill", "工作流", "抽象", "导出", "聊天记录", "记忆"],
    ),
]

LOCAL_ATTACHMENT_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
}

DATE_RE = re.compile(
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) "
    r"(\d{1,2}), (\d{4}), (\d{1,2}):(\d{2}):(\d{2})\s*([AP]M) "
    r"GMT([+\-]\d{2}):(\d{2})"
)


def html_to_text(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"</(p|li|h\d|div|ol|ul|tr)>", "\n", fragment, flags=re.I)
    text = unescape(re.sub(r"<[^>]+>", "", fragment))
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def parse_date(raw: str) -> str:
    match = DATE_RE.search(raw)
    if not match:
        return ""

    month, day, year, hour, minute, second, ampm, offset_hour, offset_minute = match.groups()
    hour_int = int(hour)
    if ampm == "PM" and hour_int != 12:
        hour_int += 12
    elif ampm == "AM" and hour_int == 12:
        hour_int = 0

    dt = datetime(
        int(year),
        MONTHS[month],
        int(day),
        hour_int,
        int(minute),
        int(second),
    )
    return f"{dt.isoformat()}GMT{offset_hour}:{offset_minute}"


def stable_id(created_at_raw: str, prompt: str, response: str) -> str:
    payload = f"{created_at_raw}\n{prompt}\n{response[:500]}".encode("utf-8", errors="ignore")
    return hashlib.sha1(payload).hexdigest()[:12]


def infer_task_tags(prompt: str, response: str) -> list[str]:
    del response
    combined = prompt.lower()
    tags = []
    for tag, patterns in TASK_PATTERNS:
        if any(pattern.lower() in combined for pattern in patterns):
            tags.append(tag)
    return tags or ["other"]


def split_main_fragment(chunk: str) -> str:
    start = chunk.find("Prompted")
    if start < 0:
        return ""

    fragment = chunk[start:]
    for marker in [
        '<div class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1 mdl-typography--text-right">',
        '<div class="content-cell mdl-cell mdl-cell--12-col mdl-typography--caption">',
        "<b>Products:</b>",
    ]:
        idx = fragment.find(marker)
        if idx >= 0:
            fragment = fragment[:idx]
    return fragment


def extract_links(fragment: str, base_dir: Path) -> list[dict[str, object]]:
    links = []
    for href, label in re.findall(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', fragment, flags=re.I | re.S):
        decoded_href = unquote(unescape(href))
        label_text = html_to_text(label)
        suffix = Path(decoded_href).suffix.lower()
        is_local_attachment = not decoded_href.startswith(("http://", "https://")) and suffix in LOCAL_ATTACHMENT_EXTENSIONS
        item = {
            "href": decoded_href,
            "label": label_text,
            "is_local_attachment": is_local_attachment,
            "exists": False,
            "path": "",
        }
        if is_local_attachment:
            path = base_dir / decoded_href
            item["path"] = str(path)
            item["exists"] = path.exists()
        links.append(item)
    return links


def parse_activity(html_path: Path) -> list[dict[str, object]]:
    base_dir = html_path.parent
    html = html_path.read_text(encoding="utf-8", errors="replace")
    records = []

    for chunk in html.split('<div class="outer-cell')[1:]:
        fragment = split_main_fragment(chunk)
        if not fragment:
            continue

        text = html_to_text(fragment)
        if not text.startswith("Prompted"):
            continue

        date_match = DATE_RE.search(text)
        created_at_raw = date_match.group(0) if date_match else ""
        created_at_iso = parse_date(created_at_raw) if created_at_raw else ""
        before_date = text[: date_match.start()] if date_match else text
        after_date = text[date_match.end() :] if date_match else ""

        prompt = before_date.replace("Prompted", "", 1).strip()
        prompt = re.sub(r"\s+", " ", prompt)
        response = after_date.split("Products:")[0].strip()

        # The date offset is computed on stripped text, not raw HTML. Extract
        # local file links from the whole activity body instead; Google Takeout
        # stores uploaded files as local hrefs, while response/source links are
        # usually external URLs.
        attachments = extract_links(fragment, base_dir)
        combined = f"{prompt}\n{response}".lower()
        matched_keywords = [kw for kw in RELEVANCE_KEYWORDS if kw.lower() in combined]

        record = {
            "id": stable_id(created_at_raw, prompt, response),
            "created_at_raw": created_at_raw,
            "created_at_iso": created_at_iso,
            "prompt": prompt,
            "response": response,
            "attachments": attachments,
            "attachment_count": sum(1 for link in attachments if link["is_local_attachment"]),
            "matched_keywords": matched_keywords,
            "task_tags": infer_task_tags(prompt, response),
            "is_relevant": bool(matched_keywords),
            "prompt_chars": len(prompt),
            "response_chars": len(response),
        }
        records.append(record)

    return records


def iter_files(base_dir: Path) -> list[dict[str, object]]:
    files = []
    for path in sorted(base_dir.iterdir()):
        if not path.is_file():
            continue
        files.append(
            {
                "filename": path.name,
                "path": str(path),
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
            }
        )
    return files


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_csv(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "created_at_raw",
                "created_at_iso",
                "is_relevant",
                "matched_keywords",
                "task_tags",
                "attachment_count",
                "prompt_chars",
                "response_chars",
                "prompt",
                "response",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "id": record["id"],
                    "created_at_raw": record["created_at_raw"],
                    "created_at_iso": record["created_at_iso"],
                    "is_relevant": record["is_relevant"],
                    "matched_keywords": "|".join(record["matched_keywords"]),
                    "task_tags": "|".join(record["task_tags"]),
                    "attachment_count": record["attachment_count"],
                    "prompt_chars": record["prompt_chars"],
                    "response_chars": record["response_chars"],
                    "prompt": record["prompt"],
                    "response": record["response"],
                }
            )


def write_index_csv(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "created_at_raw",
                "created_at_iso",
                "task_tags",
                "matched_keywords",
                "attachment_count",
                "prompt_chars",
                "response_chars",
                "prompt",
                "attachment_labels",
            ],
        )
        writer.writeheader()
        for record in records:
            attachment_labels = [
                attachment["label"] or attachment["href"]
                for attachment in record["attachments"]
                if attachment["is_local_attachment"]
            ]
            writer.writerow(
                {
                    "id": record["id"],
                    "created_at_raw": record["created_at_raw"],
                    "created_at_iso": record["created_at_iso"],
                    "task_tags": "|".join(record["task_tags"]),
                    "matched_keywords": "|".join(record["matched_keywords"]),
                    "attachment_count": record["attachment_count"],
                    "prompt_chars": record["prompt_chars"],
                    "response_chars": record["response_chars"],
                    "prompt": record["prompt"],
                    "attachment_labels": "|".join(attachment_labels),
                }
            )


def write_attachment_references_csv(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "record_id",
                "created_at_raw",
                "task_tags",
                "attachment_label",
                "attachment_href",
                "attachment_path",
                "attachment_exists",
                "prompt",
            ],
        )
        writer.writeheader()
        for record in records:
            for attachment in record["attachments"]:
                if not attachment["is_local_attachment"]:
                    continue
                writer.writerow(
                    {
                        "record_id": record["id"],
                        "created_at_raw": record["created_at_raw"],
                        "task_tags": "|".join(record["task_tags"]),
                        "attachment_label": attachment["label"],
                        "attachment_href": attachment["href"],
                        "attachment_path": attachment["path"],
                        "attachment_exists": attachment["exists"],
                        "prompt": record["prompt"],
                    }
                )


def write_markdown(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write("# Relevant Gemini Activity Extract\n\n")
        for record in records:
            f.write(f"## {record['created_at_raw']} · {record['id']}\n\n")
            f.write(f"Keywords: {', '.join(record['matched_keywords'])}\n\n")
            f.write(f"Task tags: {', '.join(record['task_tags'])}\n\n")
            if record["attachments"]:
                f.write("Attachments:\n")
                for attachment in record["attachments"]:
                    if attachment["is_local_attachment"]:
                        f.write(f"- {attachment['label'] or attachment['href']} ({attachment['href']})\n")
                f.write("\n")
            f.write("Prompt:\n\n")
            f.write(f"{record['prompt']}\n\n")
            f.write("Response:\n\n")
            f.write(f"{record['response']}\n\n")


def write_summary(path: Path, records: list[dict[str, object]], relevant: list[dict[str, object]], files: list[dict[str, object]]) -> None:
    extension_counts: dict[str, int] = {}
    for file in files:
        extension_counts[file["extension"] or "[no extension]"] = extension_counts.get(file["extension"] or "[no extension]", 0) + 1

    missing_attachments = [
        attachment
        for record in records
        for attachment in record["attachments"]
        if attachment["is_local_attachment"] and not attachment["exists"]
    ]
    task_counts: dict[str, int] = {}
    for record in records:
        for tag in record["task_tags"]:
            task_counts[tag] = task_counts.get(tag, 0) + 1

    summary = {
        "total_activity_records": len(records),
        "relevant_activity_records": len(relevant),
        "total_files": len(files),
        "extension_counts": extension_counts,
        "records_with_local_attachments": sum(1 for record in records if record["attachment_count"]),
        "local_attachment_references": sum(record["attachment_count"] for record in records),
        "missing_local_attachment_references": len(missing_attachments),
        "task_tag_counts": dict(sorted(task_counts.items(), key=lambda item: item[1], reverse=True)),
        "oldest_record": records[-1]["created_at_raw"] if records else "",
        "newest_record": records[0]["created_at_raw"] if records else "",
        "relevance_keywords": RELEVANCE_KEYWORDS,
    }
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir
    html_path = input_dir / "MyActivity.html"
    if not html_path.exists():
        raise SystemExit(f"MyActivity.html not found: {html_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    records = parse_activity(html_path)
    relevant = [record for record in records if record["is_relevant"]]
    files = iter_files(input_dir)

    write_jsonl(output_dir / "gemini_activity_all.jsonl", records)
    write_jsonl(output_dir / "gemini_activity_relevant.jsonl", relevant)
    write_csv(output_dir / "gemini_activity_relevant.csv", relevant)
    write_index_csv(output_dir / "gemini_activity_relevant_index.csv", relevant)
    write_attachment_references_csv(output_dir / "gemini_attachment_references.csv", records)
    write_markdown(output_dir / "gemini_activity_relevant.md", relevant)
    write_jsonl(output_dir / "gemini_files_manifest.jsonl", files)
    write_summary(output_dir / "summary.json", records, relevant, files)

    print(json.dumps(json.loads((output_dir / "summary.json").read_text(encoding="utf-8")), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
