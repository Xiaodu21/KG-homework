# back_end/llm.py
import subprocess
import sys
import re

def call_llm(question: str) -> str:
    q = question.strip()
    if not q.endswith(('?', '？', '.', '。', '!', '！')):
        prompt = q + ('谁？' if q.endswith('是') else '？')
    else:
        prompt = q

    try:
        # 使用 ollama run 直接调用（绕过 HTTP API）
        result = subprocess.run(
            ["ollama", "run", "qwen2.5:1.5b", prompt],
            capture_output=True,
            text=True,
            timeout=90,
            encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        output = result.stdout.strip()
        # 移除可能的 Thinking... 或 done thinking 提示
        output = re.sub(r'^Thinking\.\.\.\s*', '', output, flags=re.MULTILINE)
        output = re.sub(r'\.\.\.done thinking\.$', '', output, flags=re.MULTILINE)
        return output.strip()
    except Exception as e:
        print(f"【LLM ERROR】{e}")
        return ""