"""
工具函数 - 文本抽取模块
"""
import json
import os
from typing import List, Dict, Any
from extraction_config import OUTPUT_DIR


def save_results(results: Dict[str, Any], filename: str = "results.json"):
    """保存结果到JSON文件"""
    output_path = os.path.join(OUTPUT_DIR, filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"结果已保存到: {output_path}")


def load_text_file(filepath: str) -> str:
    """加载文本文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def format_entities(entities: List[Dict]) -> str:
    """格式化实体输出"""
    if not entities:
        return "未识别到实体"
    
    result = []
    for entity in entities:
        result.append(f"  - {entity['text']} ({entity['label']})")
    return "\n".join(result)


def format_relations(relations: List[Dict]) -> str:
    """格式化关系输出"""
    if not relations:
        return "未抽取到关系"
    
    result = []
    for rel in relations:
        result.append(
            f"  - {rel['head']} --[{rel['relation']}]--> {rel['tail']}"
        )
    return "\n".join(result)


def visualize_knowledge_graph(entities: List[Dict], relations: List[Dict]):
    """可视化知识图谱（简单文本格式）"""
    print("\n" + "="*50)
    print("知识图谱")
    print("="*50)
    
    print("\n实体列表:")
    print(format_entities(entities))
    
    print("\n关系列表:")
    print(format_relations(relations))
    
    print("\n" + "="*50)

