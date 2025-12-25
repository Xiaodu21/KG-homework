"""
配置文件 - 文本抽取模块
"""
import os

# 模型配置
NER_MODEL_NAME = "bert-base-chinese"  # 或使用其他中文预训练模型
RE_MODEL_NAME = "bert-base-chinese"

# 实体类型
ENTITY_TYPES = {
    "PERSON": "人物",
    "ORG": "组织",
    "LOC": "地点",
    "TIME": "时间",
    "MONEY": "金额",
    "PERCENT": "百分比",
    "PRODUCT": "产品"
}

# 关系类型
RELATION_TYPES = {
    "WORK_FOR": "工作于",
    "LOCATED_IN": "位于",
    "PART_OF": "属于",
    "MANAGE": "管理",
    "FOUNDED": "创立",
    "OWN": "拥有",
    "PRODUCE": "生产"
}

# 数据路径
DATA_DIR = "data"
EXAMPLES_DIR = "examples"
OUTPUT_DIR = "output"

# 创建必要的目录
for dir_path in [DATA_DIR, EXAMPLES_DIR, OUTPUT_DIR]:
    os.makedirs(dir_path, exist_ok=True)

