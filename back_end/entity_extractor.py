# coding=utf-8
"""
实体抽取模块 - 专门用于从LLM回答中提取音乐相关实体（歌曲、专辑、人物）
通过查询知识图谱获取已知实体列表，然后在文本中匹配

新增功能：
- 基于大模型的 NER + 关系抽取（主路径）
- 关系关键词映射 + 实体匹配（fallback 路径）
- 输出结构化三元组 [(head, relation, tail)]
"""
from db import get_db, close_db
import re
import subprocess
import sys
import json
from typing import List, Dict, Tuple


class MusicEntityExtractor:
    """音乐领域实体抽取器"""

    def __init__(self):
        """初始化实体抽取器，从KG加载实体列表"""
        self.songs = set()  # 歌曲/作品名
        self.albums = set()  # 专辑名
        self.persons = set()  # 人物名
        self._load_entities_from_kg()

    def _load_entities_from_kg(self):
        """从知识图谱加载所有实体"""
        try:
            db = get_db()
            try:
                with db.session() as session:
                    result = session.run("MATCH (n:作品) RETURN n.name AS name")
                    self.songs = {record["name"] for record in result}
                    print(f"加载了 {len(self.songs)} 首歌曲")

                    result = session.run("MATCH (n:专辑) RETURN n.name AS name")
                    self.albums = {record["name"] for record in result}
                    print(f"加载了 {len(self.albums)} 个专辑")

                    result = session.run("MATCH (n:人物) RETURN n.name AS name")
                    self.persons = {record["name"] for record in result}
                    print(f"加载了 {len(self.persons)} 个人物")
            finally:
                close_db(db)
        except Exception as e:
            print(f"警告: 加载实体列表时出错: {e}")
            self.songs = set()
            self.albums = set()
            self.persons = set()

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """从文本中提取音乐相关实体（保持原逻辑不变）"""
        entities = {"songs": [], "albums": [], "persons": []}
        all_entities = {
            "songs": sorted(self.songs, key=len, reverse=True),
            "albums": sorted(self.albums, key=len, reverse=True),
            "persons": sorted(self.persons, key=len, reverse=True)
        }
        matched_positions = set()

        for entity_type in ["songs", "albums", "persons"]:
            found_entities = []
            for entity in all_entities[entity_type]:
                pattern = re.escape(entity)
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                for match in matches:
                    start, end = match.span()
                    is_overlapped = any(
                        not (end <= ms or start >= me)
                        for ms, me in matched_positions
                    )
                    if not is_overlapped:
                        found_entities.append(entity)
                        matched_positions.add((start, end))
                        break
            entities[entity_type] = list(set(found_entities))
        return entities

    def extract_all_entities(self, text: str) -> List[str]:
        """提取所有实体（不分类）"""
        entities_dict = self.extract_entities(text)
        return list(set(entities_dict["songs"] + entities_dict["albums"] + entities_dict["persons"]))


# ========== 新增：关系关键词映射==========
RELATION_KEYWORDS = {
    "歌手": ["演唱", "唱", "主唱", "由.*?演唱", "演唱者", "谁唱"],
    "作词": ["作词", "填词", "词作者", "歌词由", "作词人", "谁写的词"],
    "作曲": ["作曲", "谱曲", "曲作者", "作曲人", "谁作曲"]
}


# ========== 新增：调用 LLM 进行信息抽取 ==========
def _call_llm_for_extraction(prompt: str) -> str:
    """内部函数：调用 LLM 执行抽取"""
    try:
        result = subprocess.run(
            ["ollama", "run", "qwen3:1.7b", prompt],
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        output = result.stdout.strip()
        output = re.sub(r'^Thinking\.\.\.\s*', '', output, flags=re.MULTILINE)
        output = re.sub(r'\.{3}done thinking.*$', '', output, flags=re.MULTILINE)
        return output.split('\n')[0].strip()
    except Exception as e:
        print(f"[EXTRACTION ERROR] {e}")
        return ""


# ========== 【增强版】主三元组抽取函数 ==========
def extract_triples_from_llm_answer(llm_answer: str, question: str = "") -> List[Tuple[str, str, str]]:
    """
    从 LLM 回答中抽取三元组，使用混合策略：
    1. 主路径：调用 LLM 做 NER+RE
    2. 备用路径：使用 RELATION_KEYWORDS + KG 实体匹配
    3. 【新增】轻量规则路径：直接解析自然语言答案（如“周杰伦”）
    """
    if not llm_answer or llm_answer.strip().lower() in {"未知", "unknown", ""}:
        return []

    extractor = get_entity_extractor()

    # === 第一步：尝试用 LLM 抽取（主路径）===
    extraction_prompt = f"""Task: Extract entities and relations from the text below.
Relations allowed: 歌手 (singer), 作词 (lyricist), 作曲 (composer).
Output format: Entity1 | Relation | Entity2
Only output the triples. Do not add any explanation.

Example:
Input: 《七里香》由周杰伦演唱，方文山作词。
Output:
七里香 | 歌手 | 周杰伦
七里香 | 作词 | 方文山

Input:
{llm_answer}

Output:
"""

    raw_output = _call_llm_for_extraction(extraction_prompt)
    triples = []
    
    # 增强解析：处理可能的前缀/思维链残留
    lines = raw_output.split('\n')
    for line in lines:
        line = line.strip()
        # 跳过明显的非三元组行
        if not line or " | " not in line or line.startswith("Thinking") or "..." in line:
            continue
            
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 3: # 允许 loose parsing
            h = parts[0]
            r = parts[1]
            t = parts[2]
            
            # 清理书名号和常见标点
            h = re.sub(r'[《》]', '', h)
            t = re.sub(r'[《》]', '', t)
            
            if r in {"歌手", "作词", "作曲"}:
                triples.append((h, r, t))
    
    if triples:
        return triples

    print(f"[LLM EXTRACTION FAILED OR EMPTY] Raw: {raw_output}. Trying fallback...")

    # === 第二步：LLM 失败 → 启用规则方法（你的 RELATION_KEYWORDS + KG 实体）===
    print("[INFO] Fallback to regex-based extraction with relation keywords.")

    # 【新增】先尝试轻量规则抽取（解决“周杰伦”类纯答案）
    light_triples = _lightweight_extraction(llm_answer, question, extractor)
    if light_triples:
        return light_triples

    # 再走原有 fallback
    return _fallback_regex_extraction(llm_answer, extractor)


def _lightweight_extraction(text: str, question: str, extractor: MusicEntityExtractor) -> List[Tuple[str, str, str]]:
    from handler import get_relation_type_from_question

    rel = get_relation_type_from_question(question)
    if not rel:
        return []

    song = ""
    match = re.search(r'《([^》]+)》', question)
    if match:
        song = match.group(1).strip()
    else:
        # 更通用的歌曲提取
        song_match = re.search(r'(?:歌曲|作品)?\s*([^\s的]+)\s*(?:的|之)', question)
        if song_match:
            song = song_match.group(1).strip()

    if not song:
        return []

    clean_ans = text.strip()
    clean_ans = re.sub(r'\*+', '', clean_ans)
    clean_ans = re.split(r'[。！？\n]', clean_ans)[0].strip()

    # === 关键修复：支持关系词变体 ===
    REL_VARIANTS = {
        "作词": ["作词", "作词人", "词作者", "填词人", "填词"],
        "作曲": ["作曲", "作曲人", "曲作者", "谱曲人", "谱曲"],
        "歌手": ["歌手", "演唱者", "主唱", "演唱"]
    }
    variants = REL_VARIANTS.get(rel, [rel])

    # 短答案直接返回（如果在 KG 中）
    if len(clean_ans) <= 20 and not any(
            w in clean_ans for w in ["不知道", "不确定", "可能", "需要", "嗯", "好的", "用户"]) \
            and song not in clean_ans and not any(v in clean_ans for v in variants):
        if clean_ans in extractor.persons:
            return [(song, rel, clean_ans)]

    # 构建正则 patterns
    patterns = []
    for v in variants:
        # 模式1: 《青花瓷》的作词人是 XXX
        patterns.append(r'《?{}》?\s*的\s*{}(?:是|为)?\s*([^\s。，；！？、,，]+)'.format(re.escape(song), re.escape(v)))
        # 模式2: 作词人是 XXX
        patterns.append(r'{}(?:是|为)?\s*([^\s。，；！？、,，]+)'.format(re.escape(v)))

    patterns.append(r'答案[：:]\s*([^\s。，；！？、,，]+)')

    for pattern in patterns:
        match = re.search(pattern, clean_ans)
        if match:
            tail = match.group(1).strip()
            # 只取第一个词（防“陈奕迅（周杰伦）”之类）
            tail = re.split(r'[（\(【\s]', tail)[0].strip()
            if tail and len(tail) >= 2:
                return [(song, rel, tail)]

    return []


def _fallback_regex_extraction(text: str, extractor: MusicEntityExtractor) -> List[Tuple[str, str, str]]:
    """
    备用方案：基于关系关键词进行规则抽取。
    - head（歌曲）必须来自 KG（确保主体正确）
    - tail（人物）可以从文本中提取任意合理候选（允许错误，供后续 KG 验证）
    """
    # 1. 提取歌曲（必须来自 KG）
    entities = extractor.extract_entities(text)
    songs = entities["songs"]
    if not songs:
        return []

    # 优先使用 KG 中的人物
    persons_in_text = [p for p in extractor.persons if p in text]
    if persons_in_text:
        candidate_tails = persons_in_text
    else:
        # 否则用保守正则（只取2~5字中文，且不在黑名单）
        raw_candidates = re.findall(r'[\u4e00-\u9fa5]{2,5}', text)
        blacklist = {"作词人", "作曲人", "演唱者", "是谁", "答案", "歌曲", "专辑", "人是", "可能是", "不确定"}
        candidate_tails = [c for c in raw_candidates if c not in blacklist]
    if not candidate_tails:
        return []

    triples = []
    cleaned_text = text.replace("《", "").replace("》", "")

    for song in songs:
        for rel_type, keywords in RELATION_KEYWORDS.items():
            for kw in keywords:
                pattern = kw if kw.startswith("由") else re.escape(kw)
                if re.search(pattern, cleaned_text, re.IGNORECASE):
                    # 找到第一个合理的 tail（排除 song 自身）
                    for tail in candidate_tails:
                        if tail == song:
                            continue
                        triples.append((song, rel_type, tail))
                        break  # 每种关系只取一个最可能的
                    break  # 找到关键词就跳出
    return triples


# 全局单例实例
_extractor_instance = None


def get_entity_extractor() -> MusicEntityExtractor:
    """获取实体抽取器单例"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = MusicEntityExtractor()
    return _extractor_instance