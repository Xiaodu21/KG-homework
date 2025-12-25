"""
命名实体识别（NER）模块
"""
import re
from typing import List, Dict, Tuple
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
from extraction_config import NER_MODEL_NAME, ENTITY_TYPES


class NERModule:
    """命名实体识别模块"""
    
    def __init__(self, model_name: str = None):
        """
        初始化NER模块
        
        Args:
            model_name: 模型名称，默认使用配置文件中的模型
        """
        self.model_name = model_name or NER_MODEL_NAME
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"正在加载NER模型: {self.model_name}")
        print(f"使用设备: {self.device}")
        
        # 注意：这里使用一个简化的方法
        # 实际项目中可以使用专门的中文NER模型，如bert-base-chinese + NER头
        # 或者使用spaCy的中文模型
        self.tokenizer = None
        self.model = None
        
        # 使用规则和关键词作为基础实现
        # 实际项目中应该加载预训练模型
        self._init_patterns()
    
    def _init_patterns(self):
        """初始化实体识别模式（规则基础方法）"""
        self.patterns = {
            "PERSON": [
                r"[王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤][一-龥]{1,3}",
            ],
            "ORG": [
                r"[公司|集团|企业|银行|医院|学校|大学|学院|研究所|实验室|中心|局|部|委员会|协会|基金会|组织|机构]+",
            ],
            "LOC": [
                r"[省|市|县|区|镇|村|街道|路|街|大道|广场|公园|山|河|湖|海]+",
                r"[北京|上海|天津|重庆|河北|山西|辽宁|吉林|黑龙江|江苏|浙江|安徽|福建|江西|山东|河南|湖北|湖南|广东|海南|四川|贵州|云南|陕西|甘肃|青海|台湾|内蒙古|广西|西藏|宁夏|新疆|香港|澳门]+",
            ],
            "TIME": [
                r"\d{4}年\d{1,2}月\d{1,2}日",
                r"\d{4}年\d{1,2}月",
                r"\d{4}年",
                r"今天|明天|昨天|今年|明年|去年",
            ],
            "MONEY": [
                r"\d+[\.\d]*[元|万元|亿元|美元|欧元|人民币]+",
            ],
            "PERCENT": [
                r"\d+[\.\d]*%",
            ],
            "PRODUCT": [
                r"[手机|电脑|汽车|软件|系统|平台|应用|产品]+",
            ]
        }
    
    def extract(self, text: str) -> List[Dict]:
        """
        从文本中提取实体
        
        Args:
            text: 输入文本
            
        Returns:
            实体列表，每个实体包含text, label, start, end
        """
        entities = []
        seen_spans = set()
        
        # 使用模式匹配识别实体
        for label, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    span = (match.start(), match.end())
                    if span not in seen_spans:
                        entities.append({
                            "text": match.group(),
                            "label": label,
                            "label_zh": ENTITY_TYPES.get(label, label),
                            "start": match.start(),
                            "end": match.end()
                        })
                        seen_spans.add(span)
        
        # 去重和排序
        entities = self._deduplicate_entities(entities)
        entities.sort(key=lambda x: x["start"])
        
        return entities
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """去除重复的实体"""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            key = (entity["text"], entity["label"], entity["start"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def extract_with_context(self, text: str, context_window: int = 10) -> List[Dict]:
        """
        提取实体并包含上下文
        
        Args:
            text: 输入文本
            context_window: 上下文窗口大小（字符数）
            
        Returns:
            包含上下文的实体列表
        """
        entities = self.extract(text)
        
        for entity in entities:
            start = max(0, entity["start"] - context_window)
            end = min(len(text), entity["end"] + context_window)
            entity["context"] = text[start:end]
        
        return entities


if __name__ == "__main__":
    # 测试
    ner = NERModule()
    test_text = "苹果公司的CEO蒂姆·库克在2023年9月12日于加利福尼亚州发布了新款iPhone手机，售价5999元。"
    entities = ner.extract(test_text)
    
    print("识别的实体：")
    for entity in entities:
        print(f"  {entity['text']} - {entity['label_zh']} ({entity['label']})")

