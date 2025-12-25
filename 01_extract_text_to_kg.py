"""
主程序 - 文本信息抽取与构建系统
"""
import os
from ner_extractor import NERModule
from relation_extractor import REModule
from extraction_utils import save_results, format_entities, format_relations, visualize_knowledge_graph
from extraction_config import EXAMPLES_DIR


def process_text(text: str, save_output: bool = True):
    """
    处理文本，进行NER和RE
    
    Args:
        text: 输入文本
        save_output: 是否保存输出结果
    """
    print("\n" + "="*60)
    print("文本信息抽取与构建系统")
    print("="*60)
    print(f"\n输入文本: {text}\n")
    
    # 初始化模块
    print("正在初始化NER和RE模块...")
    ner = NERModule()
    re_module = REModule()
    
    # 实体识别
    print("\n正在进行实体识别...")
    entities = ner.extract(text)
    
    print(f"\n识别到 {len(entities)} 个实体:")
    print(format_entities(entities))
    
    # 关系抽取
    print("\n正在进行关系抽取...")
    relations = re_module.extract(text, entities)
    
    print(f"\n抽取到 {len(relations)} 个关系:")
    print(format_relations(relations))
    
    # 可视化知识图谱
    visualize_knowledge_graph(entities, relations)
    
    # 保存结果
    if save_output:
        results = {
            "text": text,
            "entities": entities,
            "relations": relations,
            "statistics": {
                "entity_count": len(entities),
                "relation_count": len(relations),
                "entity_types": {}
            }
        }
        
        # 统计实体类型
        for entity in entities:
            label = entity["label"]
            results["statistics"]["entity_types"][label] = \
                results["statistics"]["entity_types"].get(label, 0) + 1
        
        save_results(results, "extraction_results.json")
    
    return entities, relations


def process_file(filepath: str):
    """处理文件中的文本"""
    if not os.path.exists(filepath):
        print(f"错误: 文件 {filepath} 不存在")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    
    if not text:
        print("错误: 文件为空")
        return
    
    process_text(text)


def interactive_mode():
    """交互式模式"""
    print("\n" + "="*60)
    print("交互式文本信息抽取")
    print("="*60)
    print("输入文本进行分析，输入 'quit' 或 'exit' 退出\n")
    
    ner = NERModule()
    re_module = REModule()
    
    while True:
        text = input("请输入文本: ").strip()
        
        if text.lower() in ['quit', 'exit', '退出']:
            print("再见！")
            break
        
        if not text:
            print("文本不能为空，请重新输入。")
            continue
        
        try:
            entities = ner.extract(text)
            relations = re_module.extract(text, entities)
            
            visualize_knowledge_graph(entities, relations)
            
            save = input("\n是否保存结果？(y/n): ").strip().lower()
            if save == 'y':
                results = {
                    "text": text,
                    "entities": entities,
                    "relations": relations
                }
                save_results(results, "interactive_results.json")
        
        except Exception as e:
            print(f"处理出错: {e}")


def main():
    """主函数"""
    import sys
    
    # 示例文本
    example_texts = [
        "苹果公司的CEO蒂姆·库克在2023年9月12日于加利福尼亚州发布了新款iPhone手机，售价5999元。",
        "阿里巴巴集团位于浙江省杭州市，马云是公司的创始人。",
        "清华大学是位于北京市的一所著名大学，培养了许多优秀人才。",
        "腾讯公司的马化腾在深圳创立了这家互联网公司，现在拥有微信和QQ等产品。"
    ]
    
    if len(sys.argv) > 1:
        # 命令行模式
        if sys.argv[1] == "-i" or sys.argv[1] == "--interactive":
            interactive_mode()
        elif sys.argv[1] == "-f" or sys.argv[1] == "--file":
            if len(sys.argv) > 2:
                process_file(sys.argv[2])
            else:
                print("错误: 请指定文件路径")
        else:
            # 直接处理命令行参数作为文本
            process_text(" ".join(sys.argv[1:]))
    else:
        # 默认处理示例文本
        print("未提供输入，使用示例文本进行演示...\n")
        for i, text in enumerate(example_texts[:2], 1):  # 只处理前两个示例
            print(f"\n{'='*60}")
            print(f"示例 {i}")
            print(f"{'='*60}")
            process_text(text, save_output=(i == 1))
        
        print("\n提示:")
        print("  - 使用 'python 01_extract_text_to_kg.py -i' 进入交互模式")
        print("  - 使用 'python 01_extract_text_to_kg.py -f <文件路径>' 处理文件")
        print("  - 使用 'python 01_extract_text_to_kg.py <文本>' 直接处理文本")


if __name__ == "__main__":
    main()

