# back_end/llm.py
import requests
import json
import re
import subprocess
import sys


def call_llm(question: str) -> str:
    q = question.strip()
    if not q.endswith(('?', '？', '.', '。', '!', '！')):
        q += '？'

    full_prompt = f"问题：{q}\n回答："

    try:
        result = subprocess.run(
            ["ollama", "run", "qwen2.5:1.5b", full_prompt],
            capture_output=True,
            text=True,
            timeout=90,
            encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        output = result.stdout.strip()

        # === 关键修复：使用更健壮的解析逻辑 ===
        return parse_llm_answer(output)

    except Exception as e:
        print(f"【LLM ERROR】{e}")
        return "未知"


def parse_llm_answer(text: str) -> str:
    """
    Parses the final answer from the LLM output.
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    cleaned_lines = []
    for line in lines:
        if line.startswith("Thinking...") or "...done thinking" in line:
            continue
        cleaned_lines.append(line)

    if not cleaned_lines:
        return "未知"

    # Strategy: Combine lines unless it looks like a thinking chain that wasn't caught.
    # Simple heuristic: Just join them for now, or take the last sentence if it looks definitive.
    # The previous logic took the LAST line. Let's try to be smarter.
    # If the last line is short (< 50 chars), it might be the answer.
    # If it's long, the whole thing might be the answer.

    # For now, let's join all lines to avoid missing context,
    # but maybe strip leading "Answer:" or "回答：" labels.
    full_text = " ".join(cleaned_lines)

    # Clean up common prefixes
    full_text = re.sub(r'^(答案|回答|Answer)[:：]\s*', '', full_text, flags=re.IGNORECASE)

    # Clean markdown
    full_text = re.sub(r'\*+', '', full_text)

    return full_text