# Eve Skills — AI Agent Skills Market

[![Deployed](https://img.shields.io/badge/status-live-brightgreen)](https://prerequisite-writers-end-dress.trycloudflare.com)
[![Skills](https://img.shields.io/badge/skills-219-blue)](https://prerequisite-writers-end-dress.trycloudflare.com/api/skills/categories)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**全球最大中文AI Agent技能市场 — 219个即用技能，涵盖46个类别**

> 像App Store一样浏览、搜索和下载AI Agent技能(Skills)。支持 Hermes Agent、Claude Code、OpenAI Compatible Agents。

---

## 🏆 核心数据

| 指标 | 数值 |
|------|:----:|
| 技能总数 | **219** |
| 类别数 | **46** |
| 最大类别 | CMMI5 (48), DevOps (32), Agent-Skills (24) |
| 支持格式 | SKILL.md (YAML Frontmatter) |
| 生态兼容 | Hermes Agent ✓ Claude Code ✓ OpenAI ✓ |

## 🎯 为什么选Eve Skills？

- **中文第一** — 全球唯一中文AI Agent技能市场
- **质量门禁** — 每个技能经过CMMI5质量体系审核
- **即拿即用** — 下载即用，无需额外配置
- **生态兼容** — Hermes Agent、Claude Code、OpenAI Agents通用

## 📦 技能类别速览

| 类别 | 数量 | 说明 |
|------|:----:|------|
| cmmi5 | 48 | CMMI5软件开发全流程 |
| devops | 32 | 运维/部署/CI/CD |
| agent-skills | 24 | Agent框架集成 |
| engineering | 21 | 测试/诊断/架构 |
| business | 12 | 市场/销售/运营 |
| security | 10 | 安全扫描/审计 |
| ... 40+更多 | 102 | 覆盖全部开发场景 |

## 🚀 快速开始

```bash
# 浏览所有技能
curl https://your-deploy-url/api/skills?page=1&page_size=20

# 按类别筛选
curl https://your-deploy-url/api/skills?category=devops

# 搜索技能
curl "https://your-deploy-url/api/skills?search=docker"

# 查看技能详情
curl https://your-deploy-url/api/skills/cmmi5/cmmi5-compliance-binding

# 下载技能包
curl -OJ https://your-deploy-url/api/skills/devops/docker-compose-manager/download
```

## 💰 价格

| 层级 | 价格 | 功能 |
|------|:----:|------|
| 免费 | ¥0 | 50个技能下载 |
| 专业 | ¥99/月 | 全库无限下载 |
| 企业 | ¥299/月 | 私有技能+SLA |

## 🛠 技术栈

- **后端:** FastAPI (Python)
- **数据库:** SQLite
- **认证:** JWT + bcrypt
- **支付:** 支付宝 (集成中)

## 📄 开源协议

MIT License — 技能内容可自由使用，商业使用需订阅。

## 🔗 相关项目

- [Eve LLM Gateway](https://github.com/eve-ai/llm-gateway) — 统一国产LLM API网关
- [Eve Env Vault](https://github.com/eve-ai/env-vault) — 环境变量安全管理器
