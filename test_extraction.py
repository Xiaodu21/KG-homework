"""
简单的测试示例 - 文本抽取功能测试
"""
from ner_extractor import NERModule
from relation_extractor import REModule

def test_basic():
    """基本功能测试"""
    print("="*60)
    print("基本功能测试")
    print("="*60)
    
    # 测试文本
    text = "苹果公司的CEO蒂姆·库克在2023年9月12日于加利福尼亚州发布了新款iPhone手机，售价5999元。"
    
    # 初始化模块
    print("\n1. 初始化NER和RE模块...")
    ner = NERModule()
    re_module = REModule()
    
    # 实体识别
    print("\n2. 进行实体识别...")
    entities = ner.extract(text)
    print(f"   识别到 {len(entities)} 个实体:")
    for entity in entities:
        print(f"     - {entity['text']} ({entity['label_zh']})")
    
    # 关系抽取
    print("\n3. 进行关系抽取...")
    relations = re_module.extract(text, entities)
    print(f"   抽取到 {len(relations)} 个关系:")
    for rel in relations:
        print(f"     - {rel['head']} --[{rel['relation_zh']}]--> {rel['tail']}")
    
    # 三元组
    print("\n4. 三元组表示:")
    triplets = re_module.extract_triplets(text, entities)
    for head, relation, tail in triplets:
        print(f"     ({head}, {relation}, {tail})")
    
    print("\n测试完成！")

if __name__ == "__main__":
    test_basic()

