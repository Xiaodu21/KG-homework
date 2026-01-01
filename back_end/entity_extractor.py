# coding=utf-8
"""
实体抽取模块 - 专门用于从LLM回答中提取音乐相关三元组 (head, relation, tail)
通过查询知识图谱获取已知实体列表，并结合规则与大模型进行混合抽取。

核心目标：准确抽取出如 ("七里香", "歌手", "周杰伦") 的结构化事实，
以便与KG比对，检测幻觉。
"""
from db import get_db, close_db
import re
import subprocess
import sys
import json
from typing import List, Dict, Tuple


# ==============================================================================
# 🧠 类：MusicEntityExtractor —— 音乐领域实体词典加载与匹配器
# 作用：从 Neo4j 知识图谱中一次性加载所有已知实体（歌曲/专辑/人物），
#       并提供基于最大匹配（longest-first）的实体识别方法。
# 设计理念：避免抽取“不存在”的幻觉实体，只信任 KG 中的真实名字。
# ==============================================================================
class MusicEntityExtractor:
    """音乐领域实体抽取器"""

    def __init__(self):
        """
        初始化实体抽取器，从KG加载实体列表。
        加载三类实体：作品（歌曲）、专辑、人物。
        """
        self.songs = set()  # 存储所有歌曲名（来自 :作品 节点）
        self.albums = set()  # 存储所有专辑名（来自 :专辑 节点）
        self.persons = set()  # 存储所有人物名（来自 :人物 节点）
        self._load_entities_from_kg()

    def _load_entities_from_kg(self):
        """
        【私有方法】从 Neo4j 知识图谱中加载全部实体。
        执行三条 Cypher 查询，分别获取作品、专辑、人物的 name 属性。
        若连接失败，则清空集合，避免后续崩溃。
        """
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
        """
        【核心方法】基于词典的最大匹配实体抽取（Dictionary-based NER）。
        输入：任意文本（如 LLM 的回答）
        输出：按类型分类的实体列表 {"songs": [...], "albums": [...], "persons": [...]}
        策略：
          - 按实体长度降序排序，优先匹配长串（防“青花瓷”被拆成“花瓷”）
          - 记录匹配位置，防止重叠（如“周杰伦”和“杰伦”）
        """
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
                        break  # 每个匹配位置只取一次
            entities[entity_type] = list(set(found_entities))
        return entities

    def extract_all_entities(self, text: str) -> List[str]:
        """
        【辅助方法】提取文本中所有类型的实体（不分类，去重）。
        用途：快速获取所有提及的 KG 实体。
        """
        entities_dict = self.extract_entities(text)
        return list(set(entities_dict["songs"] + entities_dict["albums"] + entities_dict["persons"]))


# ==============================================================================
# 🔑 全局常量：RELATION_KEYWORDS —— 关系关键词映射表
# 作用：为 fallback 规则路径提供关系触发词。
# 格式：{关系类型: [关键词正则或字符串列表]}
# ==============================================================================
RELATION_KEYWORDS = {
    "歌手": ["演唱", "唱", "主唱", "由.*?演唱", "演唱者", "谁唱"],
    "作词": ["作词", "填词", "词作者", "歌词由", "作词人", "谁写的词"],
    "作曲": ["作曲", "谱曲", "曲作者", "作曲人", "谁作曲"]
}

ALLOWED_RELATIONS = {"歌手", "作词", "作曲"}


def _normalize_entity(text: str) -> str:
    if not text:
        return ""
    return text.replace("《", "").replace("》", "").strip()


def _clean_tail_candidate(tail: str) -> str:
    if not tail:
        return ""
    cleaned = _normalize_entity(tail)
    cleaned = re.sub(r"[A-Za-z0-9]+", "", cleaned)
    for sep in ["是", "为", "由"]:
        if sep in cleaned:
            cleaned = cleaned.split(sep)[-1]
    if "成员" in cleaned:
        cleaned = cleaned.split("成员")[-1]
    cleaned = cleaned.lstrip("的")
    for suffix in ["演唱者", "演唱", "主唱", "歌手"]:
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
    return cleaned.strip()


def _is_valid_tail(tail: str, extractor: MusicEntityExtractor, allow_ungrounded: bool) -> bool:
    if not tail:
        return False
    if not allow_ungrounded:
        return tail in extractor.persons
    if tail in extractor.persons:
        return True
    if len(tail) < 2 or len(tail) > 20:
        return False
    if re.search(r"[0-9A-Za-z]", tail):
        return False
    if any(bad in tail for bad in ["不知道", "不确定", "可能", "需要", "答案", "用户", "歌曲", "专辑", "演唱", "韩国", "中国", "日本", "美国", "男子", "女子", "组合", "成员"]):
        return False
    return True


def _extract_ungrounded_person_candidates(text: str, extractor: MusicEntityExtractor) -> List[str]:
    candidates = []
    for match in re.finditer(r"[\u4e00-\u9fff]{2,6}", text):
        candidate = _clean_tail_candidate(match.group(0))
        if candidate in extractor.songs or candidate in extractor.albums:
            continue
        if _is_valid_tail(candidate, extractor, allow_ungrounded=True):
            if candidate not in candidates:
                candidates.append(candidate)
    return candidates


# ==============================================================================
# 🤖 函数：_call_llm_for_extraction —— 调用 LLM 执行结构化信息抽取
# 作用：通过 Ollama 调用本地 LLM（如 qwen:7b），传入 Prompt，要求其输出 JSON。
# 输入：Prompt 字符串
# 输出：LLM 返回的第一行非空文本（已清理 Thinking... 日志）
# 注意：这是“让 LLM 自己做 NER+RE”的核心调用点。
# ==============================================================================
def _call_llm_for_extraction(prompt: str) -> str:
    """内部函数：调用 LLM 执行抽取"""
    try:
        result = subprocess.run(
            ["ollama", "run", "qwen2.5:1.5b", prompt],
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


# ==============================================================================
# 🧩 函数：extract_triples_from_llm_answer —— 主三元组抽取入口
# 作用：从 LLM 的自然语言回答中，抽取出结构化三元组 [(head, relation, tail)]。
# 策略（混合式）：
#   1️⃣ 主路径：让 LLM 输出 JSON（端到端 NER+RE）
#   2️⃣ 轻量规则：处理“方文山”这类短答案
#   3️⃣ Fallback：关键词 + 实体匹配（兜底）
# 输入：llm_answer（LLM 回答文本），question（原始问题，用于上下文）
# 输出：三元组列表，如 [("青花瓷", "作词", "方文山")]
# ==============================================================================
def extract_triples_from_llm_answer(
    llm_answer: str,
    question: str = "",
    allow_ungrounded: bool = False
) -> List[Tuple[str, str, str]]:
    if not llm_answer or llm_answer.strip().lower() in {"未知", "unknown", ""}:
        return []

    extractor = get_entity_extractor()
    forced_head = ""
    if allow_ungrounded and question:
        from handler import extract_head_entity
        forced_head = extract_head_entity(question)

    # === 第一步：尝试用 LLM 抽取（主路径）===
    extraction_prompt = f"""你是一个专业的信息抽取系统。请从以下文本中：
1. 识别【歌曲】和【人物】实体；
2. 判断它们之间的关系，关系类型只能是：歌手、作词、作曲；
3. 输出严格为 JSON 列表，格式：[{{"head":"歌曲","relation":"关系","tail":"人物"}}]

示例：
文本：《青花瓷》由周杰伦演唱，方文山作词。
输出：
[{{"head": "青花瓷", "relation": "歌手", "tail": "周杰伦"}}, {{"head": "青花瓷", "relation": "作词", "tail": "方文山"}}]

文本：{llm_answer}
输出：
"""

    raw_output = _call_llm_for_extraction(extraction_prompt)
    triples = []
    try:
        json_match = re.search(r'(\[.*\])', raw_output, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
            for item in data:
                head = _normalize_entity(item.get("head", ""))
                rel = item.get("relation", "").strip()
                tail = _normalize_entity(item.get("tail", ""))
                if allow_ungrounded:
                    tail = _clean_tail_candidate(tail)
                if allow_ungrounded and not head and forced_head:
                    head = forced_head
                if rel in ALLOWED_RELATIONS:
                    if allow_ungrounded:
                        if head and _is_valid_tail(tail, extractor, allow_ungrounded=True):
                            triples.append((head, rel, tail))
                    elif (head in extractor.songs or head in extractor.albums) and tail in extractor.persons:
                        triples.append((head, rel, tail))
        if triples:
            return triples
    except Exception as e:
        print(f"[LLM EXTRACTION FAILED] {e}. Trying fallback...")

    # === 第二步：LLM 失败 → 启用轻量规则抽取 ===
    print("[INFO] Fallback to lightweight extraction.")
    light_triples = _lightweight_extraction(
        llm_answer,
        question,
        extractor,
        allow_ungrounded=allow_ungrounded
    )
    if light_triples:
        return light_triples

    # === 第三步：再走关键词兜底 ===
    print("[INFO] Fallback to regex-based extraction.")
    return _fallback_regex_extraction(
        llm_answer,
        extractor,
        allow_ungrounded=allow_ungrounded
    )


# ==============================================================================
# 🪝 函数：_lightweight_extraction —— 轻量规则抽取（针对短答案优化）
# 作用：当 LLM 直接回答“方文山”时，结合问题上下文构造三元组。
# 流程：
#   1. 从 question 提取歌曲名（使用 handler.py 中的统一逻辑）
#   2. 从 llm_answer 提取干净人名（去括号、去前缀、去尾标点）
#   3. 构造 (song, relation, person)
# 优势：速度快、准确率高，适用于简单问答。
# ==============================================================================
def _lightweight_extraction(
    text: str,
    question: str,
    extractor: MusicEntityExtractor,
    allow_ungrounded: bool = False
) -> List[Tuple[str, str, str]]:
    from handler import get_relation_type_from_question, extract_head_entity  # ← 关键：统一 head 提取

    rel = get_relation_type_from_question(question)
    if not rel:
        return []

    # ✅ 使用与 query_handler 完全一致的 head 提取方式！
    song = extract_head_entity(question)
    if not song or song not in extractor.songs:
        return []

    clean_ans = text.strip()
    clean_ans = re.sub(r'\*+', '', clean_ans)
    clean_ans = re.split(r'[。！？\n]', clean_ans)[0].strip()

    # 清理尾部标点、括号、空格
    clean_tail = re.sub(r'[。！？，,.\s】）\)\]]+$', '', clean_ans).strip()
    if allow_ungrounded:
        clean_tail = _clean_tail_candidate(clean_tail)

    REL_VARIANTS = {
        "作词": ["作词", "作词人", "词作者", "填词人", "填词"],
        "作曲": ["作曲", "作曲人", "曲作者", "谱曲人", "谱曲"],
        "歌手": ["歌手", "演唱者", "主唱", "演唱"]
    }
    variants = REL_VARIANTS.get(rel, [rel])

    # 短答案直接返回（如果在 KG 中）
    if len(clean_tail) <= 20 and not any(
            w in clean_tail for w in ["不知道", "不确定", "可能", "需要", "嗯", "好的", "用户"]) \
            and song not in clean_tail and not any(v in clean_tail for v in variants):
        if _is_valid_tail(clean_tail, extractor, allow_ungrounded):
            return [(song, rel, clean_tail)]

    # 构建正则 patterns
    patterns = []
    for v in variants:
        patterns.append(r'《?{}》?\s*的\s*{}(?:是|为)?\s*([^\s。，；！？、,，]+)'.format(re.escape(song), re.escape(v)))
        patterns.append(r'{}(?:是|为)?\s*([^\s。，；！？、,，]+)'.format(re.escape(v)))
    patterns.append(r'答案[：:]\s*([^\s。，；！？、,，]+)')

    for pattern in patterns:
        match = re.search(pattern, clean_ans)
        if match:
            tail = match.group(1).strip()
            tail = re.split(r'[（\(【\s]', tail)[0].strip()
            tail = re.sub(r'[。！？，,.\s】）\)\]]+$', '', tail).strip()
            if allow_ungrounded:
                tail = _clean_tail_candidate(tail)
            if _is_valid_tail(tail, extractor, allow_ungrounded):
                return [(song, rel, tail)]
    return []


# ==============================================================================
# 🛟 函数：_fallback_regex_extraction —— 关键词规则兜底抽取
# 作用：当 LLM 和轻量规则都失败时，用关键词触发关系，结合 KG 实体匹配。
# 策略：
#   - head 必须来自 KG（确保主体正确）
#   - tail **只使用 KG 中出现过的人物**（不再猜测！）
#   - 每种关系只取第一个合理 tail
# 定位：最后防线，保证系统不崩溃。
# ==============================================================================
def _fallback_regex_extraction(
    text: str,
    extractor: MusicEntityExtractor,
    allow_ungrounded: bool = False
) -> List[Tuple[str, str, str]]:
    entities = extractor.extract_entities(text)
    songs = entities["songs"]
    if not songs:
        return []

    # ✅ 关键修复：只使用 KG 中存在的人物，拒绝乱猜！
    persons_in_text = [p for p in extractor.persons if p in text]
    if not persons_in_text and not allow_ungrounded:
        return []  # 如果没提到任何 KG 人物，直接放弃

    if persons_in_text:
        candidate_tails = persons_in_text
    else:
        candidate_tails = _extract_ungrounded_person_candidates(text, extractor)
        if not candidate_tails:
            return []
    triples = []
    cleaned_text = _normalize_entity(text)

    for song in songs:
        for rel_type, keywords in RELATION_KEYWORDS.items():
            for kw in keywords:
                pattern = kw if kw.startswith("由") else re.escape(kw)
                if re.search(pattern, cleaned_text, re.IGNORECASE):
                    for tail in candidate_tails:
                        if tail == song:
                            continue
                        triples.append((song, rel_type, tail))
                        break
                    break
    return triples


# ==============================================================================
# 🧾 函数：get_entity_extractor —— 单例模式获取实体抽取器
# 作用：全局只加载一次 KG 实体，避免重复连接数据库。
# 返回：MusicEntityExtractor 实例
# ==============================================================================
_extractor_instance = None


def get_entity_extractor() -> MusicEntityExtractor:
    """获取实体抽取器单例"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = MusicEntityExtractor()
    return _extractor_instance
