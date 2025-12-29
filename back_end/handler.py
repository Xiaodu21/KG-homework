# coding=utf-8
from db import get_db, close_db
import re

patterns = [
    '歌曲(.+)所属的音乐专辑是',
    '歌曲(.+)的作词人是',
    '演唱(.+)的歌手是',
    '专辑(.+)包含的歌曲是',
    '(.+)演唱的歌曲有',
    '(.+)作词的歌曲有',
    '(.+)合作过的人有',
    '(.+)是谁唱的',  # New
    '(.+)是哪个专辑的', # New
    '谁唱的(.+)', # New
    '谁作词的(.+)', # New
]

queries = [
    "MATCH (a:作品{name:$val})-[:所属专辑]->(b:专辑) RETURN b.name AS name LIMIT 1",
    "MATCH (a:作品{name:$val})-[:作词]->(b:人物) RETURN b.name AS name LIMIT 1",
    "MATCH (a:作品{name:$val})-[:歌手]->(b:人物) RETURN b.name AS name LIMIT 1",
    "MATCH (a:专辑{name:$val})<-[:所属专辑]-(b:作品) RETURN b.name AS name",
    "MATCH (a:人物{name:$val})<-[:歌手]-(b:作品) RETURN b.name AS name LIMIT 10",
    "MATCH (a:人物{name:$val})<-[:作词]-(b:作品) RETURN b.name AS name LIMIT 10",
    "MATCH (a:人物{name:$val})-[:合作]->(b:人物) RETURN b.name AS name LIMIT 10",
    "MATCH (a:作品{name:$val})-[:歌手]->(b:人物) RETURN b.name AS name LIMIT 1", # Mapped to (.+)是谁唱的
    "MATCH (a:作品{name:$val})-[:所属专辑]->(b:专辑) RETURN b.name AS name LIMIT 1", # Mapped to (.+)是哪个专辑的
    "MATCH (a:作品{name:$val})-[:歌手]->(b:人物) RETURN b.name AS name LIMIT 1", # Mapped to 谁唱的(.+)
    "MATCH (a:作品{name:$val})-[:作词]->(b:人物) RETURN b.name AS name LIMIT 1", # Mapped to 谁作词的(.+)
]


def query_handler(question):
    """原有 KG 查询逻辑，完全保留"""
    print("问题：", question)
    for index, pattern in enumerate(patterns):
        matchObj = re.match(pattern, question)
        if matchObj:
            print("匹配成功 pattern is: ", pattern)
            val = matchObj.group(1)
            query = queries[index]
            db = get_db()
            try:
                with db.session() as session:
                    result = session.run(query, val=val)
                    rows = result.values('name')
                    rows = [row[0] for row in rows]
                    print("查询结果：", rows)
                return {
                    "state": 0,
                    "data": rows,
                    "msg": "查询成功"
                }
            finally:
                close_db(db)
    print("匹配失败")
    return {
        "state": 1,
        "msg": "查询失败，没有匹配的问句模版"
    }


# ========== 新增：仅用于推断关系类型（不改变原有查询逻辑）==========
def get_relation_type_from_question(question: str) -> str:
    """
  根据问题文本推断应查询的关系类型（用于构造三元组比对）
  注意：必须与 patterns 中的语义对齐！
  """
    q = question.strip()

    if re.match(r'歌曲.+的作词人是', q):
        return "作词"
    elif re.match(r'演唱.+的歌手是', q):
        return "歌手"
    elif re.match(r'.+作词的歌曲有', q):
        return "作词"  # 虽然是反向，但三元组仍为 (歌曲, 作词, 人)
    elif re.match(r'.+演唱的歌曲有', q):
        return "歌手"
    else:
        # 默认 fallback
        if "作词" in q or "词" in q:
            return "作词"
        elif "作曲" in q or "曲" in q:
            return "作曲"
        else:
            return "歌手"


def extract_entity_for_kg_query(question: str):
    """仅用于从问题中提取 KG 查询所需的实体值（即 patterns 中的 (.+) 部分）"""
    for pattern in patterns:
        match = re.match(pattern, question)
        if match:
            return match.group(1).strip()
    return None


# handler.py 末尾添加
def extract_head_entity(question: str) -> str:
    """从问题中提取 pattern 中的 (.+) 部分，用于构造三元组 head"""
    for pattern in patterns:
        match = re.match(pattern, question.strip())
        if match:
            return match.group(1).strip()
    return ""