# 项目执行顺序指南
## 完整执行流程

### 阶段一：环境准备

1. **安装Python依赖**
   ```bash
   cd back_end
   pip install -r requirements.txt
   ```

2. **安装Node.js依赖**
   ```bash
   cd front_end
   npm install
   ```

3. **安装和启动Neo4j数据库**
   - 下载安装Neo4j
   - 启动Neo4j服务
   - 配置连接信息（修改 `back_end/db.py` 和 `data/02_import_to_neo4j.py`）

4. **安装Ollama（可选，用于两阶段问答）**
   ```bash
   ollama pull qwen3:1.7b
   ```

### 阶段二：数据准备（选择以下方式之一）

#### 方式A：使用已有的CSV数据（推荐）

**步骤1：导入CSV数据到Neo4j**
```bash
cd data
python 02_import_to_neo4j.py
```

#### 方式B：从文本抽取构建知识图谱（可选）

**步骤1：运行文本抽取**
```bash
# 方式1：交互式模式
python 01_extract_text_to_kg.py -i

# 方式2：处理文件
python 01_extract_text_to_kg.py -f <文件路径>

# 方式3：直接处理文本
python 01_extract_text_to_kg.py "文本内容"
```

**步骤2：将抽取结果转换为CSV格式**
（需要手动或编写脚本将抽取结果转换为CSV）

**步骤3：导入到Neo4j**
```bash
cd data
python 02_import_to_neo4j.py
```

### 阶段三：启动服务

**步骤1：启动后端服务**
```bash
cd back_end
python app.py
```
后端服务将在 `http://127.0.0.1:5001` 启动

**步骤2：启动前端服务（新终端窗口）**
```bash
cd front_end
npm run dev
```
前端服务将在 `http://localhost:5173` 启动

**步骤3：访问应用**
在浏览器中打开前端地址，开始使用系统

## 详细执行步骤

### 第一步：数据导入（必需）

```bash
# 1. 确保Neo4j数据库已启动
# 2. 检查数据库连接配置
#    编辑 data/02_import_to_neo4j.py，确认连接信息正确

# 3. 运行导入脚本
cd data
python 02_import_to_neo4j.py

# 4. 验证导入结果
#    应该在终端看到类似输出：
#    正在加载节点...
#    加载了 XX 首歌曲
#    加载了 XX 个专辑
#    加载了 XX 个人物
#    正在加载关系...
#    ✅ 数据导入完成！
```

**注意**：如果CSV文件路径有问题，可能需要修改 `02_import_to_neo4j.py` 中的文件路径。

### 第二步：启动后端服务（必需）

```bash
# 1. 进入后端目录
cd back_end

# 2. 激活虚拟环境（如果使用）
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. 启动Flask服务
python app.py

# 4. 确认服务启动
#    应该看到：
#    * Running on http://127.0.0.1:5001
```

### 第三步：启动前端服务（必需）

```bash
# 1. 打开新的终端窗口
# 2. 进入前端目录
cd front_end

# 3. 启动开发服务器
npm run dev

# 4. 确认服务启动
#    应该看到：
#    VITE v4.x.x  ready in xxx ms
#    ➜  Local:   http://localhost:5173/
```

### 第四步：使用系统

1. 在浏览器中访问前端地址（如 `http://localhost:5173`）
2. 点击"图谱问答"页面
3. 选择查询模板或输入问题
4. 点击"查询"按钮查看结果

## 可选步骤

### 测试文本抽取功能（可选）

```bash
# 运行测试脚本
python test_extraction.py
```

### 测试后端API（可选）

```bash
# 测试基础查询接口
curl -X POST http://127.0.0.1:5001/query \
  -H "Content-Type: application/json" \
  -d '{"question": "歌曲兰亭序所属的音乐专辑是"}'

# 测试两阶段问答接口
curl -X POST http://127.0.0.1:5001/query_v2 \
  -H "Content-Type: application/json" \
  -d '{"question": "周杰伦演唱的歌曲有"}'
```

## 执行顺序总结

```
1. 环境准备
   ├── 安装Python依赖
   ├── 安装Node.js依赖
   ├── 安装并启动Neo4j
   └── 安装Ollama（可选）

2. 数据准备
   └── 运行 02_import_to_neo4j.py （必需）

3. 启动服务
   ├── 启动后端（app.py）
   └── 启动前端（npm run dev）

4. 使用系统
   └── 访问前端页面进行查询
```

## 注意事项

1. **执行顺序很重要**：
   - 必须先导入数据，再启动后端服务
   - 后端服务必须在前端服务之前启动

2. **数据库配置**：
   - 确保 `back_end/db.py` 和 `data/02_import_to_neo4j.py` 中的数据库连接信息一致
   - 如果使用Neo4j Aura（云端），需要修改连接URI

3. **端口占用**：
   - 后端默认使用5001端口
   - 前端默认使用5173端口
   - 确保这些端口未被占用

4. **文件重命名后**：
   - 如果重命名了文件，需要更新所有导入语句
   - 建议先完成重命名，再进行后续操作

