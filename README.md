# PhD Consulting Agent

一个用于博士留学咨询场景的本地智能体项目，帮助顾问提升效率、标准化流程，并沉淀经验为可复用技能（skills）。

## 项目结构

```bash
app/                 # 本地工作台（agent入口）
docs/                # 项目文档
scripts/             # 启动 / 辅助脚本
skills/phd-consulting/  # 核心咨询技能包
AGENTS.md            # Agent设计说明
```

## 核心能力

- 学生背景解析（profile extraction）
- 博士申请定位（positioning）
- 研究方向与RP框架生成
- 导师匹配与套磁邮件生成
- 申请时间线 & checklist

## 快速开始（MVP）

### 1. 克隆项目

```bash
git clone https://github.com/zcloveyou2333/phd-consulting-agent.git
cd phd-consulting-agent
```

### 2. 启动本地环境（根据你的实现调整）

如果是 Python：

```bash
pip install -r requirements.txt
python app/main.py
```

如果是 Node：

```bash
npm install
npm run dev
```

## 使用方式（当前推荐）

1. 准备一个学生case（文本或结构化信息）
2. 调用对应 skill，例如：
   - student_profile
   - phd_positioning
   - research_proposal
3. 输出结果用于顾问加工和决策

## 设计理念

- Skill 化：把咨询流程拆成可复用能力
- 本地优先：支持离线/私有数据
- Human-in-the-loop：AI 生成 + 人工审核

## Roadmap

- [ ] Skill Store（技能库管理）
- [ ] 多学生管理（CRM-lite）
- [ ] 导师数据库集成
- [ ] 自动套磁 pipeline
- [ ] 与 Hermes / 通用 Agent 框架对接

## 适用人群

- 博士留学顾问
- 留学中介团队
- 想把经验产品化的个人顾问

---

如果你是未来的你：这个项目其实就是你那个“顾问Agent产品化”的起点。
