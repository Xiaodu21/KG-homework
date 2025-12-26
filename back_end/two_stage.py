# back_end/two_stage.py
from llm import call_llm
from handler import query_handler
from entity_extractor import get_entity_extractor


def two_stage_qa(question: str):
    """
    两阶段问答系统：
    1. 第一阶段：LLM生成答案
    2. 第二阶段：从LLM回答中抽取实体，与知识图谱结果进行比对验证
    """
    # === 第一阶段：LLM 生成 ===
    llm_ans = call_llm(question)
    print(f"【第一阶段】已接入千问2.5 1.5b，大模型的回答是：{llm_ans}")

    # === 第二阶段：尝试用 KG 验证 ===
    kg_res = query_handler(question)
    
    # 获取实体抽取器
    extractor = get_entity_extractor()
    
    # 从LLM回答中抽取实体
    llm_entities = extractor.extract_entities(llm_ans)
    llm_all_entities = extractor.extract_all_entities(llm_ans)
    print(f"【实体抽取】从LLM回答中抽取到实体: {llm_all_entities}")
    print(f"  歌曲: {llm_entities['songs']}")
    print(f"  专辑: {llm_entities['albums']}")
    print(f"  人物: {llm_entities['persons']}")

    if kg_res["state"] == 0 and kg_res["data"]:
        kg_answers = kg_res["data"]
        kg_set = set(kg_answers)
        
        # 方法1: 原始字符串匹配（保留兼容性）
        if llm_ans in kg_set:
            return {
                "final_answer": llm_ans,
                "source": "verified_by_kg_string",
                "llm_answer": llm_ans,
                "kg_answers": kg_answers,
                "llm_entities": llm_entities,
                "is_hallucination": False,
                "match_type": "string_match"
            }
        
        # 方法2: 实体级别匹配 - 检查LLM回答中的实体是否与KG结果有交集
        if llm_all_entities:
            # 检查LLM抽取的实体是否在KG结果中
            llm_entity_set = set(llm_all_entities)
            kg_set_lower = {str(item).lower() for item in kg_set}
            llm_entity_set_lower = {str(item).lower() for item in llm_entity_set}
            
            matched_entities = llm_entity_set_lower & kg_set_lower
            
            if matched_entities:
                # 找到匹配的实体，使用KG结果
                # 优先使用与匹配实体最接近的KG答案
                matched_entity_original = None
                for llm_ent in llm_entity_set:
                    if llm_ent.lower() in matched_entities:
                        matched_entity_original = llm_ent
                        break
                
                # 如果KG结果包含匹配的实体，直接使用
                for kg_ans in kg_answers:
                    if str(kg_ans).lower() in matched_entities or matched_entity_original in str(kg_ans):
                        print(f"【实体匹配成功】LLM实体 '{matched_entity_original}' 与KG结果 '{kg_ans}' 匹配")
                        return {
                            "final_answer": kg_ans,
                            "source": "verified_by_kg_entity",
                            "llm_answer": llm_ans,
                            "kg_answers": kg_answers,
                            "llm_entities": llm_entities,
                            "matched_entities": list(matched_entities),
                            "is_hallucination": False,
                            "match_type": "entity_match"
                        }
                
                # 如果匹配到实体但格式不完全一致，使用KG第一个结果
                correct = kg_answers[0]
                print(f"【实体部分匹配】LLM实体 '{list(matched_entities)[0]}' 与KG相关，使用KG答案 '{correct}' 修正")
                return {
                    "final_answer": correct,
                    "source": "corrected_by_kg_entity",
                    "llm_answer": llm_ans,
                    "kg_answers": kg_answers,
                    "llm_entities": llm_entities,
                    "matched_entities": list(matched_entities),
                    "is_hallucination": True,
                    "match_type": "entity_partial_match"
                }
            else:
                # LLM抽取了实体，但与KG结果不匹配，可能存在幻觉
                correct = kg_answers[0]
                print(f"【实体不匹配】LLM回答中的实体 {llm_all_entities} 与KG结果 {kg_answers} 不匹配，使用KG答案 '{correct}' 修正")
                return {
                    "final_answer": correct,
                    "source": "corrected_by_kg_entity",
                    "llm_answer": llm_ans,
                    "kg_answers": kg_answers,
                    "llm_entities": llm_entities,
                    "is_hallucination": True,
                    "match_type": "entity_mismatch"
                }
        else:
            # LLM回答中未提取到实体，使用KG结果修正
            correct = kg_answers[0]
            print(f"【未提取到实体】LLM回答中未找到已知实体，使用KG答案 '{correct}' 修正")
            return {
                "final_answer": correct,
                "source": "corrected_by_kg",
                "llm_answer": llm_ans,
                "kg_answers": kg_answers,
                "llm_entities": llm_entities,
                "is_hallucination": True,
                "match_type": "no_entity_extracted"
            }
    else:
        # KG查询失败，返回LLM答案（无法验证）
        return {
            "final_answer": llm_ans,
            "source": "unverified_llm",
            "llm_answer": llm_ans,
            "kg_answers": [],
            "llm_entities": llm_entities,
            "is_hallucination": None,
            "match_type": "kg_query_failed"
        }