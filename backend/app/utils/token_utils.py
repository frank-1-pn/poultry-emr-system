"""Token 计算与 Markdown 压缩工具"""
import re

import tiktoken

# 使用 cl100k_base 编码（GPT-4 / 通用）
_encoding = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """计算文本的 token 数"""
    if not text:
        return 0
    return len(_encoding.encode(text))


def compress_markdown(content: str, budget: int) -> str:
    """按 section 裁剪 Markdown，保留标题和每段首要内容，控制在 token 预算内。

    策略：
    1. 如果原文已在预算内，直接返回原文
    2. 按 ## 标题拆分 section
    3. 保留所有标题 + 每个 section 的首段/要点
    4. 逐步裁剪直到预算内
    """
    if not content:
        return ""

    if count_tokens(content) <= budget:
        return content

    # 按 ## 标题拆分
    sections = re.split(r"(^#{1,3}\s+.+$)", content, flags=re.MULTILINE)

    # 组装 (标题, 正文) 对
    parts: list[tuple[str, str]] = []
    i = 0
    while i < len(sections):
        section = sections[i].strip()
        if re.match(r"^#{1,3}\s+", section):
            body = sections[i + 1].strip() if i + 1 < len(sections) else ""
            parts.append((section, body))
            i += 2
        else:
            if section:
                parts.append(("", section))
            i += 1

    # 第一轮：标题 + 每个 section 首段（首个非空行或首个列表项块）
    compressed_parts: list[str] = []
    for title, body in parts:
        if title:
            compressed_parts.append(title)
        if body:
            # 取首段：到第一个空行为止，或全部（如果没有空行）
            first_para = body.split("\n\n")[0].strip()
            if first_para:
                compressed_parts.append(first_para)

    result = "\n\n".join(compressed_parts)
    if count_tokens(result) <= budget:
        return result

    # 第二轮：仅保留标题 + 列表项首行（更激进的压缩）
    compressed_parts = []
    for title, body in parts:
        if title:
            compressed_parts.append(title)
        if body:
            lines = body.strip().split("\n")
            bullet_lines = [ln for ln in lines if re.match(r"^\s*[-*]\s+", ln)]
            if bullet_lines:
                compressed_parts.append("\n".join(bullet_lines[:3]))

    result = "\n\n".join(compressed_parts)
    if count_tokens(result) <= budget:
        return result

    # 第三轮：仅标题
    result = "\n\n".join(title for title, _ in parts if title)
    if count_tokens(result) <= budget:
        return result

    # 最后兜底：截断到预算
    tokens = _encoding.encode(result or content)
    return _encoding.decode(tokens[:budget])


def select_memories(entries: list, budget: int) -> tuple[str, int]:
    """按优先级选择 memory 条目并拼接为文本。

    entries 应已按 importance DESC, created_at DESC 排序。
    每个 entry 需要有 .category 和 .content 属性。

    Returns:
        (拼接后的文本, 加载的条目数)
    """
    if not entries or budget <= 0:
        return "", 0

    selected: list[str] = []
    used_tokens = 0
    loaded = 0

    for entry in entries:
        line = f"[{entry.category}] {entry.content}"
        line_tokens = count_tokens(line)
        if used_tokens + line_tokens > budget:
            break
        selected.append(line)
        used_tokens += line_tokens
        loaded += 1

    return "\n".join(selected), loaded
