# back_end/two_stage.py
from llm import call_llm
from handler import query_handler, get_relation_type_from_question, extract_head_entity  # ← 新增导入
from entity_extractor import extract_triples_from_llm_answer
import re


def two_stage_qa(question: str):
    # ========== 阶段1：LLM 原始回答 ==========
    llm_ans = call_llm(question)
    print(f"【阶段1 - LLM原始回答】: {llm_ans}")

    # ========== 阶段2：从 LLM 回答中抽取三元组 ==========
    llm_triples = extract_triples_from_llm_answer(
        llm_ans,
        question,
        allow_ungrounded=True
    )
    print(f"【阶段2 - 抽取三元组】: {llm_triples}")

    # ========== 阶段3：查询知识库 ==========
    kg_res = query_handler(question)
    kg_answers = kg_res["data"] if kg_res["state"] == 0 and kg_res["data"] else []
    print(f"【阶段3 - KG查询结果】: {kg_answers}")

    # ✅ 关键修复：使用与 query_handler 完全一致的实体提取方式！
    head_entity = extract_head_entity(question)
    rel = get_relation_type_from_question(question)

    # 对于前3种查询（歌曲→专辑/作词/歌手），head 就是歌曲名
    # 后4种是反向查询（人物/专辑→歌曲），此时不构造 (head, rel, tail) 三元组（或需调整）
    # 当前我们只处理正向关系（rel in {"歌手", "作词", "作曲"}）
    if rel in {"歌手", "作词", "作曲"} and head_entity and kg_answers:
        kg_triples = [(head_entity, rel, ans) for ans in kg_answers]
    else:
        kg_triples = []

    print(f"【阶段3 - KG三元组】: {kg_triples}")

    # ========== 阶段4：匹配验证 ==========
    match_result = False
    if kg_triples and llm_triples:
        match_result = any(triple in kg_triples for triple in llm_triples)

    if match_result:
        final_answer = llm_ans
        print("【阶段4 - 匹配验证】: 匹配成功 → LLM回答正确")
    elif kg_answers:
        final_answer = ", ".join(kg_answers)
        print("【阶段4 - 匹配验证】: 匹配失败 → 使用KG事实修正答案")
    else:
        final_answer = llm_ans if llm_ans.strip() not in {"", "未知"} else "未找到相关信息"
        print("【阶段4 - 匹配验证】: 无法验证（KG无相关事实）")

    print(f"【最终答案】: {final_answer}")
    print("-" * 60)

    return {
        "final_answer": final_answer,
        "is_hallucination": (not match_result) and bool(kg_answers),
        "source": "verified_by_kg_triple" if match_result else ("corrected_by_kg" if kg_answers else "llm_unverified"),
        "stage_1_llm_raw": llm_ans,
        "stage_2_extracted_triples": [list(t) for t in llm_triples],
        "stage_3_kg_triples": [list(t) for t in kg_triples],
        "stage_4_match_result": match_result,
        "kg_answers": kg_answers,
        "llm_answer": llm_ans,
    }
