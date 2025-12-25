"""
关系抽取（RE）模块
"""
import re
from typing import List, Dict, Tuple
from extraction_config import RELATION_TYPES


class REModule:
    """关系抽取模块"""
    
    def __init__(self):
        """初始化RE模块"""
        self._init_relation_patterns()
    
    def _init_relation_patterns(self):
        """初始化关系抽取模式"""
        self.relation_patterns = {
            "WORK_FOR": [
                r"(.+?)(?:是|担任|作为|任职于|就职于)(.+?)(?:的|公司|企业|组织|机构)(?:CEO|总裁|董事长|总经理|经理|员工|职员|创始人)?",
                r"(.+?)(?:在|于)(.+?)(?:工作|任职|就职)",
                r"(.+?)(?:为|给)(.+?)(?:工作|服务)",
            ],
            "LOCATED_IN": [
                r"(.+?)(?:位于|在|处于)(.+?)",
                r"(.+?)(?:的|位于)(.+?)(?:省|市|县|区|国家|地区)",
            ],
            "PART_OF": [
                r"(.+?)(?:是|属于|为)(.+?)(?:的|一部分|组成部分)",
                r"(.+?)(?:隶属于|归)(.+?)",
            ],
            "MANAGE": [
                r"(.+?)(?:管理|负责|领导|掌管)(.+?)",
                r"(.+?)(?:是|担任)(.+?)(?:的|管理者|负责人|领导)",
            ],
            "FOUNDED": [
                r"(.+?)(?:创立|创建|成立|建立|创办)(.+?)",
                r"(.+?)(?:是|由)(.+?)(?:创立|创建|成立|建立|创办)(?:的)?",
            ],
            "OWN": [
                r"(.+?)(?:拥有|持有|控制)(.+?)",
                r"(.+?)(?:是|为)(.+?)(?:的|所有|拥有)",
            ],
            "PRODUCE": [
                r"(.+?)(?:生产|制造|研发|开发|推出|发布)(.+?)",
                r"(.+?)(?:是|由)(.+?)(?:生产|制造|研发|开发)(?:的)?",
            ],
        }
    
    def extract(self, text: str, entities: List[Dict] = None) -> List[Dict]:
        """
        从文本中抽取关系
        
        Args:
            text: 输入文本
            entities: 已识别的实体列表（可选）
            
        Returns:
            关系列表，每个关系包含head, relation, tail
        """
        relations = []
        
        # 如果提供了实体列表，使用实体进行关系抽取
        if entities:
            relations.extend(self._extract_with_entities(text, entities))
        
        # 使用模式匹配抽取关系
        relations.extend(self._extract_with_patterns(text))
        
        # 去重
        relations = self._deduplicate_relations(relations)
        
        return relations
    
    def _extract_with_entities(self, text: str, entities: List[Dict]) -> List[Dict]:
        """基于已识别实体抽取关系"""
        relations = []
        
        # 构建实体位置映射
        entity_map = {}
        for entity in entities:
            entity_text = entity["text"]
            if entity_text not in entity_map:
                entity_map[entity_text] = entity
        
        # 查找实体对之间的关系
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities):
                if i >= j:
                    continue
                
                # 检查两个实体是否在同一个句子中
                start = min(entity1["start"], entity2["start"])
                end = max(entity1["end"], entity2["end"])
                
                # 提取包含两个实体的文本片段
                context_start = max(0, start - 20)
                context_end = min(len(text), end + 20)
                context = text[context_start:context_end]
                
                # 尝试识别关系
                relation = self._find_relation_in_context(
                    context, entity1["text"], entity2["text"]
                )
                
                if relation:
                    relations.append({
                        "head": entity1["text"],
                        "head_label": entity1["label"],
                        "relation": relation,
                        "relation_zh": RELATION_TYPES.get(relation, relation),
                        "tail": entity2["text"],
                        "tail_label": entity2["label"],
                    })
        
        return relations
    
    def _extract_with_patterns(self, text: str) -> List[Dict]:
        """使用模式匹配抽取关系"""
        relations = []
        
        for relation_type, patterns in self.relation_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    if match.groups():
                        groups = match.groups()
                        if len(groups) >= 2:
                            head = groups[0].strip()
                            tail = groups[1].strip()
                            
                            # 过滤掉太短或太长的实体
                            if 2 <= len(head) <= 20 and 2 <= len(tail) <= 20:
                                relations.append({
                                    "head": head,
                                    "head_label": "UNKNOWN",
                                    "relation": relation_type,
                                    "relation_zh": RELATION_TYPES.get(relation_type, relation_type),
                                    "tail": tail,
                                    "tail_label": "UNKNOWN",
                                })
        
        return relations
    
    def _find_relation_in_context(self, context: str, entity1: str, entity2: str) -> str:
        """在上下文中查找两个实体之间的关系"""
        for relation_type, patterns in self.relation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, context):
                    # 检查模式是否包含这两个实体
                    match = re.search(pattern, context)
                    if match and match.groups():
                        groups = [g.strip() for g in match.groups()]
                        if entity1 in groups and entity2 in groups:
                            return relation_type
        return None
    
    def _deduplicate_relations(self, relations: List[Dict]) -> List[Dict]:
        """去除重复的关系"""
        seen = set()
        unique_relations = []
        
        for rel in relations:
            key = (rel["head"], rel["relation"], rel["tail"])
            if key not in seen:
                seen.add(key)
                unique_relations.append(rel)
        
        return unique_relations
    
    def extract_triplets(self, text: str, entities: List[Dict] = None) -> List[Tuple[str, str, str]]:
        """
        抽取三元组 (head, relation, tail)
        
        Args:
            text: 输入文本
            entities: 已识别的实体列表（可选）
            
        Returns:
            三元组列表
        """
        relations = self.extract(text, entities)
        return [(rel["head"], rel["relation"], rel["tail"]) for rel in relations]


if __name__ == "__main__":
    # 测试
    re_module = REModule()
    test_text = "苹果公司的CEO蒂姆·库克在加利福尼亚州发布了新产品iPhone。"
    relations = re_module.extract(test_text)
    
    print("抽取的关系：")
    for rel in relations:
        print(f"  {rel['head']} --[{rel['relation_zh']}]--> {rel['tail']}")

