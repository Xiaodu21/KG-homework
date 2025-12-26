import os
import csv
from neo4j import GraphDatabase

# 获取当前脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 定义 data 目录路径
DATA_DIR = os.path.join(SCRIPT_DIR)

# 构造所有 CSV 文件的完整路径
ALBUM_FILE = os.path.join(DATA_DIR, '专辑.csv')
MUSIC_FILE = os.path.join(DATA_DIR, '音乐作品.csv')
PERSON_FILE = os.path.join(DATA_DIR, '人物.csv')
RELATION_FILE = os.path.join(DATA_DIR, 'relation.csv')

# Neo4j 连接配置
import os
NEO4J_URI = os.getenv('NEO4J_URI', "bolt://localhost:7687")
NEO4J_USER = os.getenv('NEO4J_USER', "neo4j")
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', "Song0714.")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def clear_db(tx):
    tx.run("MATCH (n) DETACH DELETE n")


def create_constraints(tx):
    # 分别尝试创建约束，如果已存在则忽略错误
    try:
        tx.run("CREATE CONSTRAINT ON (p:作品) ASSERT p.name IS UNIQUE")
    except Exception as e:
        if "already exists" not in str(e) and "ConstraintAlreadyExists" not in str(e):
            raise e

    try:
        tx.run("CREATE CONSTRAINT ON (a:专辑) ASSERT a.name IS UNIQUE")
    except Exception as e:
        if "already exists" not in str(e) and "ConstraintAlreadyExists" not in str(e):
            raise e

    try:
        tx.run("CREATE CONSTRAINT ON (p:人物) ASSERT p.name IS UNIQUE")
    except Exception as e:
        if "already exists" not in str(e) and "ConstraintAlreadyExists" not in str(e):
            raise e


def load_nodes():
    with driver.session() as session:
        # 清空旧数据（可选）
        # session.write_transaction(clear_db)

        # 创建约束
        session.write_transaction(create_constraints)

        # 加载 专辑
        with open(ALBUM_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row['专辑名称']
                if name.strip():
                    session.run("MERGE (:专辑 {name: $name})", name=name)

        # 加载 音乐作品
        with open(MUSIC_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row['所有音乐作品']
                if name.strip():
                    session.run("MERGE (:作品 {name: $name})", name=name)

        # 加载 人物
        with open(PERSON_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row['人物列表']
                if name.strip():
                    session.run("MERGE (:人物 {name: $name})", name=name)


def load_relations():
    with driver.session() as session:
        with open(RELATION_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    work = row['Column1'].strip()
                    target = row['Column2'].strip()
                    rel_type = row['Column3'].strip()

                    if not work or not target or not rel_type:
                        continue

                    # 根据关系类型创建不同关系
                    if rel_type == '所属专辑':
                        session.run(
                            "MATCH (w:作品 {name: $work}) "
                            "MATCH (a:专辑 {name: $target}) "
                            "MERGE (w)-[:所属专辑]->(a)",
                            work=work, target=target
                        )
                    elif rel_type == '歌手':
                        session.run(
                            "MATCH (w:作品 {name: $work}) "
                            "MATCH (p:人物 {name: $target}) "
                            "MERGE (w)-[:歌手]->(p)",
                            work=work, target=target
                        )
                    elif rel_type == '作词':
                        session.run(
                            "MATCH (w:作品 {name: $work}) "
                            "MATCH (p:人物 {name: $target}) "
                            "MERGE (w)-[:作词]->(p)",
                            work=work, target=target
                        )
                    # 其他关系可扩展
                except Exception as e:
                    print(f"Error processing row: {row} | {e}")


if __name__ == "__main__":
    print("正在加载节点...")
    load_nodes()
    print("正在加载关系...")
    load_relations()
    print("✅ 数据导入完成！")
    driver.close()

