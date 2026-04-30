# PhD Consulting Agent

一个面向博士留学咨询顾问的本地 Case 工作台。项目目标是把顾问日常重复的博士申请咨询流程拆成可复用能力：学生背景诊断、研究方向设计、学校/项目/导师匹配、可比案例生成、顾问话术改写和咨询电话准备。

当前版本是一个 MVP：前端提供本地 Case 工作台，后端提供 FastAPI 接口和 SQLite 本地存储，技能运行暂时使用 `MockSkillRunner` 返回 prompt preview，方便先验证产品流程和数据结构。

## 当前功能

- 创建学生 Case
- 输入学生背景和目标地区
- 运行 6 个咨询动作：
  - 背景分析：`student_profile_analysis`
  - 研究方向：`research_direction_design`
  - 学校/导师：`school_supervisor_matching`
  - 可比案例：`comparable_case_generator`
  - 顾问话术：`consultant_delivery_rewriter`
  - 电话准备：`consultation_call_prep`
- 保存每次生成结果到本地 SQLite
- 读取清洗后的 Gemini 历史咨询记录索引
- 使用脚本清洗 Google Takeout 中的 Gemini activity 数据

## 项目结构

```text
phd-consulting-agent/
├── AGENTS.md                         # 项目设计说明和产品原则
├── app/
│   ├── backend/                       # FastAPI 后端
│   │   ├── pyproject.toml
│   │   ├── phd_consulting_agent/
│   │   │   ├── api.py                 # API 入口
│   │   │   ├── config.py              # 本地路径配置
│   │   │   ├── gemini_history.py      # Gemini 历史索引读取
│   │   │   ├── models.py              # Case / Output / Provenance 模型
│   │   │   ├── skill_contracts.py     # Skill 请求结构
│   │   │   ├── skill_prompts.py       # 各咨询技能的 prompt 模板
│   │   │   ├── skill_runner.py        # 当前 MockSkillRunner
│   │   │   └── storage.py             # SQLite 存储
│   │   └── tests/                     # 后端测试
│   └── frontend/                      # React + Vite 本地工作台
│       ├── package.json
│       ├── index.html
│       └── src/
│           ├── App.tsx
│           ├── api.ts
│           ├── styles.css
│           └── types.ts
├── docs/                              # 项目文档
├── scripts/
│   └── clean_gemini_takeout.py        # 清洗 Gemini Takeout 数据
└── skills/phd-consulting/             # PhD 咨询 skill pack
```

## 环境要求

- Python 3.11+
- Node.js 20+
- npm

## 快速启动

### 1. 克隆仓库

```bash
git clone https://github.com/zcloveyou2333/phd-consulting-agent.git
cd phd-consulting-agent
```

### 2. 启动后端

```bash
cd app/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn phd_consulting_agent.api:app --host 127.0.0.1 --port 8765 --reload
```

后端启动后可以访问：

```text
http://127.0.0.1:8765/health
```

正常返回：

```json
{"status":"ok"}
```

### 3. 启动前端

另开一个终端：

```bash
cd app/frontend
npm install
npm run dev
```

前端默认运行在：

```text
http://127.0.0.1:5174
```

前端会调用后端：

```text
http://127.0.0.1:8765
```

## 本地试用流程

1. 打开 `http://127.0.0.1:5174`
2. 在「学生背景」里粘贴一个学生 case，例如：

```text
本科环境设计，硕士景观建筑，目标港澳或大湾区博士，希望申请有奖学金项目，长期想往城市更新、房地产开发和中东/Dubai 城市发展方向走。
```

3. 在「目标地区」里填写：

```text
香港,澳门,大湾区
```

4. 点击「创建 Case」
5. 依次点击「背景分析」「研究方向」「学校/导师」「可比案例」「顾问话术」「电话准备」
6. 页面下方会显示每个 skill 的 Mock 输出和 prompt preview

注意：当前版本还没有真正接入大模型，输出是 `MockSkillRunner` 生成的占位结果。它的作用是先验证工作台、API、数据库和 skill prompt 结构是否跑通。

## 后端 API

### 健康检查

```bash
curl http://127.0.0.1:8765/health
```

### 创建 Case

```bash
curl -X POST http://127.0.0.1:8765/cases \
  -H "Content-Type: application/json" \
  -d '{
    "student_name": "匿名学生",
    "summary": "本科环境设计，硕士景观建筑，目标港澳博士，希望申请奖学金。",
    "target_regions": ["香港", "澳门"],
    "notes": "希望未来往城市更新和房地产开发方向发展。"
  }'
```

### 运行 Skill

把下面的 `case_xxx` 换成创建 Case 后返回的真实 ID：

```bash
curl -X POST http://127.0.0.1:8765/cases/case_xxx/run/student_profile_analysis \
  -H "Content-Type: application/json" \
  -d '{
    "user_instruction": "请帮我做背景分析",
    "target_regions": ["香港", "澳门"]
  }'
```

可用的 `skill_name`：

```text
student_profile_analysis
research_direction_design
school_supervisor_matching
comparable_case_generator
consultant_delivery_rewriter
consultation_call_prep
```

### 查看 Case 输出

```bash
curl http://127.0.0.1:8765/cases/case_xxx/outputs
```

### 查看 Gemini 历史索引

```bash
curl "http://127.0.0.1:8765/gemini/history?limit=20"
```

如果本地还没有清洗后的 Gemini 数据，这个接口会返回空列表。

## 清洗 Gemini Takeout 数据

项目提供了一个脚本，用来把 Google Takeout 导出的 Gemini activity 清洗成结构化文件。

示例命令：

```bash
python3 scripts/clean_gemini_takeout.py \
  --input-dir "/path/to/Takeout/My Activity/Gemini Apps" \
  --output-dir "data/cleaned/gemini_takeout"
```

脚本会生成：

```text
gemini_activity_all.jsonl
gemini_activity_relevant.jsonl
gemini_activity_relevant.csv
gemini_activity_relevant_index.csv
gemini_attachment_references.csv
gemini_activity_relevant.md
gemini_files_manifest.jsonl
summary.json
```

隐私提醒：`Takeout/`、`data/`、压缩包、数据库和 `.env` 文件都已在 `.gitignore` 中排除，不要把学生隐私数据或原始导出提交到 GitHub。

## 运行测试

```bash
cd app/backend
source .venv/bin/activate
pytest
```

测试覆盖内容包括：

- Case 创建和读取
- 运行背景分析 skill
- 输出保存
- Gemini 历史索引读取
- Prompt 约束和 provenance 标记

## 当前技术架构

```text
React/Vite frontend
        ↓
FastAPI backend
        ↓
CaseRepository + SQLite
        ↓
MockSkillRunner
        ↓
skill_prompts.py
```

当前最重要的设计点是 provenance：系统需要区分学生提供事实、文档抽取事实、已验证公开事实、模型生成策略和模拟案例，避免把生成内容包装成真实录取案例或已验证信息。

## 下一步开发建议

- 用真实 LLM runner 替换 `MockSkillRunner`
- 给每个 skill 增加可编辑参数和输入模板
- 增加 Case 列表、历史输出查看和删除功能
- 接入文档解析：CV、RP、SOP、成绩单、截图
- 将清洗后的 Gemini 历史记录用于案例检索和风格学习
- 增加导师/项目信息的实时验证流程
- 把 `skills/phd-consulting/` 与 Hermes 或通用 Agent runtime 对接

## 安全与隐私

这个项目会处理学生背景、申请材料和历史咨询记录，因此默认原则是：

- 不提交原始 Google Takeout 数据
- 不提交学生材料、CV、RP、SOP、截图或成绩单
- 不提交本地 SQLite 数据库
- 不提交 `.env` 和任何 API key
- 对模拟案例必须明确标注为 simulated reference profiles
- 对学校排名、导师状态、项目要求、奖学金和 deadline 等动态信息必须做实时核验
