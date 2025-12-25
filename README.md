# 周杰伦音乐作品知识图谱问答系统

## 项目介绍

本项目是一个基于知识图谱的周杰伦音乐作品在线检索系统。系统对周杰伦出道以来参与过的所有歌曲作品、专辑以及合作歌手、作词人进行关系分析，将这些信息组织成三元组构建知识图谱，并实现了基于知识图谱的智能问答功能。

**核心特性：**
- 🎵 音乐领域知识图谱构建（歌曲、专辑、人物关系）
- 🔍 基于模板的图谱查询系统
- 🤖 两阶段问答系统（LLM + 知识图谱验证）
- 📊 实体抽取与智能匹配
- 🌐 现代化Web界面

## 技术栈

### 后端
- **框架**: Flask 2.2.2
- **数据库**: Neo4j 5.4.0（图数据库）
- **LLM**: Ollama + Qwen3:1.7b（本地大语言模型）
- **语言**: Python 3.11+

### 前端
- **框架**: Vue 3 + Vue Router
- **构建工具**: Vite 4.0
- **UI库**: Bootstrap 5
- **HTTP客户端**: Axios

## 项目结构

```
KG-homework/
├── back_end/                 # 后端服务
│   ├── app.py               # Flask应用入口
│   ├── db.py                # Neo4j数据库连接
│   ├── handler.py           # 查询处理器（基于模板匹配）
│   ├── two_stage.py         # 两阶段问答系统
│   ├── entity_extractor.py  # 实体抽取模块
│   ├── llm.py               # LLM调用模块
│   ├── requirements.txt     # Python依赖
│   └── ENTITY_EXTRACTION_README.md  # 实体抽取功能说明
│
├── front_end/               # 前端应用
│   ├── src/
│   │   ├── App.vue          # 主应用组件
│   │   ├── views/           # 页面视图
│   │   │   ├── IntroView.vue    # 项目介绍页
│   │   │   └── QueryView.vue    # 问答查询页
│   │   ├── router/          # 路由配置
│   │   └── main.js          # 入口文件
│   ├── package.json         # Node.js依赖
│   └── vite.config.js       # Vite配置
│
├── data/                    # 数据文件
│   ├── 专辑.csv             # 专辑数据
│   ├── 人物.csv             # 人物数据
│   ├── 音乐作品.csv         # 音乐作品数据
│   ├── relation.csv         # 关系三元组数据
│   └── 02_import_to_neo4j.py # 数据导入脚本
│
├── 01_extract_text_to_kg.py  # 文本信息抽取主程序（可选）
├── extraction_config.py      # 文本抽取配置文件（可选）
├── ner_extractor.py          # 命名实体识别模块（可选）
├── relation_extractor.py     # 关系抽取模块（可选）
├── extraction_utils.py       # 抽取工具函数（可选）
├── test_extraction.py        # 文本抽取测试脚本（可选）
├── EXECUTION_ORDER.md        # 执行顺序详细指南
└── README.md                 # 本文档
```

## 环境要求

### 必需环境
- **Python**: 3.11 或更高版本
- **Node.js**: 16.0 或更高版本
- **Neo4j**: 5.0 或更高版本（本地安装或云端实例）
- **Ollama**: 已安装并运行（用于LLM功能）

### 可选环境
- **npm** 或 **yarn**（Node.js包管理器）

## 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd KG-homework
```

### 2. 安装 Neo4j 数据库

#### 方式一：本地安装
1. 下载并安装 Neo4j Desktop 或 Neo4j Community Edition
2. 启动 Neo4j 服务
3. 默认连接地址：`bolt://localhost:7687`
4. 默认用户名：`neo4j`
5. 首次登录需要修改密码

#### 方式二：使用 Neo4j Aura（云端）
1. 注册 Neo4j Aura 账号
2. 创建数据库实例
3. 获取连接URI、用户名和密码

### 3. 配置数据库连接

编辑 `back_end/db.py`，修改数据库连接信息：

```python
NEO4J_URI = "bolt://localhost:7687"      # 数据库地址
NEO4J_USERNAME = "neo4j"                 # 用户名
NEO4J_PASSWORD = "your_password"         # 密码（修改为你的密码）
```

同样，编辑 `data/02_import_to_neo4j.py` 中的连接信息（用于数据导入）。

### 4. 安装后端依赖

```bash
cd back_end

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 5. 安装前端依赖

```bash
cd front_end

# 使用 npm
npm install

# 或使用 yarn
yarn install
```

### 6. 安装 Ollama 和模型（可选，用于两阶段问答）

```bash
# 安装 Ollama（参考 https://ollama.ai）
# Windows: 下载安装包
# Linux/Mac: curl -fsSL https://ollama.ai/install.sh | sh

# 下载 Qwen3 模型
ollama pull qwen3:1.7b
```

## 配置说明

### 数据库配置

**文件**: `back_end/db.py`

```python
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "your_password"
```

### 前端代理配置

**文件**: `front_end/vite.config.js`

前端已配置代理，将 `/api` 请求转发到后端 `http://127.0.0.1:5001`

### LLM 配置

**文件**: `back_end/llm.py`

默认使用 `qwen3:1.7b` 模型，如需修改，编辑 `llm.py` 中的模型名称。

## 运行步骤

### 1. 导入知识图谱数据

在导入数据前，确保 Neo4j 数据库已启动并可以连接。

```bash
cd data

# 确保导入脚本中的数据库连接信息正确
# 编辑 02_import_to_neo4j.py，修改 NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# 运行导入脚本
python 02_import_to_neo4j.py
```

导入成功后，会看到类似输出：
```
正在加载节点...
加载了 XX 首歌曲
加载了 XX 个专辑
加载了 XX 个人物
正在加载关系...
✅ 数据导入完成！
```

### 2. 启动后端服务

```bash
cd back_end

# 激活虚拟环境（如果使用）
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 启动Flask服务
python app.py
```

后端服务将在 `http://127.0.0.1:5001` 启动。

### 3. 启动前端服务

打开新的终端窗口：

```bash
cd front_end

# 启动开发服务器
npm run dev
# 或
yarn dev
```

前端服务通常会在 `http://localhost:5173` 启动（具体端口见终端输出）。

### 4. 访问应用

在浏览器中打开前端地址（如 `http://localhost:5173`），即可使用系统。

## 功能说明

### 1. 基础图谱查询（/query接口）

基于正则模板匹配的查询系统，支持以下7种查询类型：

1. **查询歌曲所属专辑**
   - 示例：`歌曲兰亭序所属的音乐专辑是`
   - 返回：专辑名称

2. **查询歌曲作词人**
   - 示例：`歌曲兰亭序的作词人是`
   - 返回：作词人姓名

3. **查询歌曲演唱者**
   - 示例：`演唱兰亭序的歌手是`
   - 返回：歌手姓名

4. **查询专辑包含的歌曲**
   - 示例：`专辑魔杰座包含的歌曲是`
   - 返回：歌曲列表

5. **查询歌手演唱的歌曲**
   - 示例：`周杰伦演唱的歌曲有`
   - 返回：最多10首歌曲

6. **查询作词人作词的歌曲**
   - 示例：`方文山作词的歌曲有`
   - 返回：最多10首歌曲

7. **查询人物合作者**
   - 示例：`周杰伦合作过的人有`
   - 返回：最多10个合作者

### 2. 两阶段问答系统（/query_v2接口）

结合LLM和知识图谱的智能问答：

**工作流程：**
1. **第一阶段**：LLM生成答案
2. **第二阶段**：实体抽取 + KG验证
   - 从LLM回答中抽取实体（歌曲、专辑、人物）
   - 与知识图谱结果进行比对
   - 检测幻觉并修正答案

**返回结果包含：**
- `final_answer`: 最终答案
- `source`: 答案来源（verified_by_kg_entity/corrected_by_kg_entity等）
- `llm_answer`: LLM原始回答
- `kg_answers`: 知识图谱查询结果
- `llm_entities`: 从LLM回答中抽取的实体
- `is_hallucination`: 是否存在幻觉

### 3. 实体抽取功能

系统会自动从LLM回答中提取音乐相关实体：
- **歌曲名**：匹配知识图谱中的歌曲/作品
- **专辑名**：匹配知识图谱中的专辑
- **人物名**：匹配知识图谱中的人物（歌手、作词人等）

## API 文档

### 1. 健康检查

**GET** `/`

**响应**:
```
server running
```

### 2. 基础查询接口

**POST** `/query`

**请求体**:
```json
{
  "question": "歌曲兰亭序所属的音乐专辑是"
}
```

**响应**:
```json
{
  "state": 0,
  "data": ["魔杰座"],
  "msg": "查询成功"
}
```

### 3. 两阶段问答接口

**POST** `/query_v2`

**请求体**:
```json
{
  "question": "歌曲兰亭序的作词人是"
}
```

**响应**:
```json
{
  "final_answer": "方文山",
  "source": "verified_by_kg_entity",
  "llm_answer": "方文山",
  "kg_answers": ["方文山"],
  "llm_entities": {
    "songs": ["兰亭序"],
    "albums": [],
    "persons": ["方文山"]
  },
  "matched_entities": ["方文山"],
  "is_hallucination": false,
  "match_type": "entity_match"
}
```

## 使用示例

### 前端使用

1. 访问前端页面
2. 选择"图谱问答"页面
3. 在下拉菜单中选择查询模板（可选）
4. 输入问题（需符合模板格式）
5. 点击"查询"按钮
6. 查看查询结果

### 后端API调用

使用 `curl` 或 `Postman` 测试API：

```bash
# 基础查询
curl -X POST http://127.0.0.1:5001/query \
  -H "Content-Type: application/json" \
  -d '{"question": "歌曲兰亭序所属的音乐专辑是"}'

# 两阶段问答
curl -X POST http://127.0.0.1:5001/query_v2 \
  -H "Content-Type: application/json" \
  -d '{"question": "周杰伦演唱的歌曲有"}'
```

## 注意事项

### 数据库相关
- 确保 Neo4j 数据库服务正在运行
- 首次使用需要导入数据（运行 `data/02_import_to_neo4j.py`）
- 数据库密码建议使用环境变量管理（当前为硬编码，生产环境需改进）

### LLM 相关
- 使用 `/query_v2` 接口需要安装并运行 Ollama
- 首次使用需要下载模型：`ollama pull qwen3:1.7b`
- LLM 调用有90秒超时限制

### 查询格式
- 基础查询（/query）必须严格按照模板格式输入
- 两阶段问答（/query_v2）可以使用自然语言，但建议参考模板格式以获得更好效果

### 端口配置
- 后端默认端口：5001
- 前端默认端口：5173（Vite自动分配）
- 如需修改，编辑对应配置文件

## 常见问题

### Q: 数据库连接失败怎么办？
A: 检查 Neo4j 是否启动，连接信息是否正确，防火墙是否阻止连接。

### Q: 前端无法连接后端？
A: 检查后端是否启动，端口是否为5001，检查 `vite.config.js` 中的代理配置。

### Q: LLM调用失败？
A: 确认 Ollama 已安装并运行，模型已下载（`ollama list` 查看）。

### Q: 查询返回"没有匹配的问句模版"？
A: 检查问题格式是否完全符合模板要求，注意标点符号。

## 开发说明

### 添加新的查询模板

编辑 `back_end/handler.py`，在 `patterns` 和 `queries` 列表中添加对应的正则表达式和Cypher查询。

### 扩展实体类型

编辑 `back_end/entity_extractor.py`，在 `_load_entities_from_kg()` 方法中添加新的实体类型加载逻辑。

## 许可证

[根据实际情况填写]

## 作者

[根据实际情况填写]

## 更新日志

### v1.0.0
- 初始版本发布
- 基础图谱查询功能
- 两阶段问答系统
- 实体抽取与匹配功能
- Web界面

