# novel-character-graph

长篇小说人物关系图谱分析 Skill。

## 功能
- 自动解析小说人物 S/A/B/C 层级
- 势力阵营识别（仙/魔/妖/佛/人）
- 关系类型分析（夫妻/恋人/师徒/兄弟/敌人/主仆/盟友）
- 生成交互式 SVG 力导向图谱
- 鼠标悬停 tooltip（修为/性格/阵营/描述）
- 右键平移画布、滚轮缩放
- 四分 Tab：图谱 / 人物卡片 / 势力格局 / 漫画设定
- 可独立生成主题曲/片头曲/片尾曲/OST

## 目录结构
```
novel-character-graph/
├── SKILL.md              # 技能说明文档
├── scripts/
│   ├── generate_html.py  # 图谱生成核心脚本
│   ├── character_extract.py  # 人物提取脚本
│   └── chapter_split.py  # 章节分割脚本
└── assets/
    └── graph_template.html  # D3.js 图谱可视化模板
```

## 使用方法
详见 SKILL.md
