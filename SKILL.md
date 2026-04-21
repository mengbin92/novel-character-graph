---
name: novel-character-graph
description: 长篇小说深度分析 + 人物关系图谱 + 主题曲生成。支持 TXT/EPUB/PDF/DOCX 格式，百万字级自动分段解析，自动识别人物S/A/B/C层级、势力阵营、关系类型，输出交互式 HTML 图谱（SVG力导向图+四分tab页面），支持鼠标悬停tooltip详情、右键平移画布、滚轮缩放。可独立生成小说主题曲/片头曲/片尾曲/OST。
tags: [novel, analysis, character, relationship, graph, xianxia, wuxia, fantasy, song, music]
triggers:
  - 小说分析
  - 人物图谱
  - 人物关系
  - 关系图谱
  - 世界观
  - 小说人物
  - 角色设定
  - 主题曲
  - 片头曲
  - 片尾曲
  - OST
  - 小说配乐
required_commands:
  - iconv
  - ebook-convert
  - pdftotext
  - pandoc
usage_hint: >
  当用户提到「小说分析」「人物图谱」「关系图」「世界观」「角色设定」时使用本skill。
  当用户提到「主题曲」「片头曲」「片尾曲」「OST」「配乐」时也使用本skill（可独立使用）。
---

# 小说人物图谱专业分析 Skill + 主题曲生成

## 核心流程

```
小说文件 (.txt/.epub/.pdf/.docx)
    ↓ [parse.py]（编码修复 + 章节分割 + 批量并行LLM提取）
分批文本 (.txt, 每批3000-5000字)
    ↓ [generate_html.py]（角色建模 + 关系共现分析 + 渲染）
交互式 HTML 图谱（SVG力导向 + 4分Tab）
```

---

## 第一步：文件预处理

### 编码检测与修复

```bash
file -i <小说文件>
wc -l <小说文件>

# 中文小说90%为GBK，先尝试GBK→UTF-8
iconv -f GBK -t UTF-8 <小说文件> 2>/dev/null > decoded.txt && mv decoded.txt <小说文件>
# 备选
iconv -f GB18030 -t UTF-8 <小说文件> 2>/dev/null
```

### 格式转换

| 格式 | 命令 | 依赖 |
|------|------|------|
| `.txt` | 直接使用 | - |
| `.epub` / `.mobi` | `ebook-convert file.epub file.txt` | `calibre-bin` |
| `.pdf` | `pdftotext -layout file.pdf output.txt` | `poppler-utils` |
| `.docx` | `pandoc -s file.docx -o output.txt` | `pandoc` |

### 分批（>500KB 强制分段，每批 3000-5000 字）

```python
# batch 分批示例（Python）
batch_size = 5000
with open('novel.txt', 'r', encoding='utf-8') as f:
    text = f.read()
for i in range(0, len(text), batch_size):
    batch = text[i:i+batch_size]
    with open(f'/tmp/batches/batch_{i//batch_size+1:02d}.txt', 'w', encoding='utf-8') as out:
        out.write(batch)
```

---

## 第二步：LLM 批量提取人物

36 批文本分成 6 组（每组 6 批），**每批取前 1000 字**打包进 prompt，让 LLM 一次性提取该批所有人名。

### 提取 prompt 模板

```
你是小说人物提取助手。从以下文本中提取所有中文人名（2-4字），每行一个名字，无其他内容。只返回人名列表。
```

### 合并策略

```python
# 所有批次结果 → 去重 → 频次统计
# 频次阈值：出现≥2次为有效角色
# 输出：{name: set of batch_numbers}
```

### 共现分析（自动建关系）

同一段落（以空行分割）中同时出现的人物 → 建立关系对 → 统计共现频次。

```python
# 共现频次 → 关系强度
# 频次≥5：强关系
# 频次≥3：普通关系
# 频次<3：忽略
```

---

## 第三步：人物数据建模

### 角色分级标准

| 层级 | 定义 | 节点半径 | 颜色 |
|------|------|---------|------|
| S | 主角团 + 最终BOSS + 关键导师 | 28+ | 金色 #ffd700 |
| A | 主要反派 + 主要盟友 + 女主 | 22+ | 蓝色 #3498db |
| B | 重要配角 + 各门派掌门 | 16+ | 绿色 #2ecc71 |
| C | 路人甲 + 一次性炮灰 | 12+ | 灰色 #95a5a6 |

### 角色数据字段

```python
{
    "name": str,         # 人名（唯一标识）
    "role": str,         # 身份描述
    "level": str,        # S/A/B/C
    "cultivation": str,  # 修为/境界
    "personality": str,  # 性格关键词
    "description": str,  # 人物描述
}
```

### 关系数据字段

```python
{
    "from_person": str,
    "to_person": str,
    "relationship_type": str,  # 夫妻/恋人/师徒/兄弟/敌人/主仆/盟友/其他
    "description": str,
    "source": str,            # 人工分析 / 共现分析
}
```

---

## 第四步：生成交互式图谱

### 核心脚本

```python
from generate_html import generate_html

generate_html(
    title="御龙征程",
    subtitle="人物关系图谱 · 主角团",
    characters=[...],   # 角色列表
    relationships=[...], # 关系列表
    output_path="/path/to/output.html",
    timeline_html="",   # 可选：时间线HTML片段
    comic_html="",      # 可选：漫画设定HTML片段
)
```

### 输出文件

- **主角团图谱**：S级+A级人物 + 相互关系
- **全员图谱**：全部角色 + 共现关系（107人/552关系）

---

## 第五步：图谱交互功能（graph_template.html）

### 四分 Tab 页面

| Tab | 内容 |
|-----|------|
| 🕸️ 关系图谱 | SVG 力导向图（D3.js Force Simulation） |
| 👤 人物介绍 | 毛玻璃角色卡片，按 S/A/B/C 分级 |
| 🌍 势力格局 | 各阵营人数占比柱状图 |
| 🎨 漫画设定 | 预留漫画分镜区域 |

### 图谱交互

- **节点显示**：圆形内显示姓氏特征字（全名显示在圆圈下方）
- **悬停 tooltip**：修为 / 性格 / 阵营 / 描述 / 关系数 / 相关人物
- **拖拽节点**：鼠标拖拽重新布局
- **滚轮缩放**：0.1x ~ 5x 范围
- **右键平移**：右键拖拽画布（避免浏览器右键菜单干扰）
- **节点颜色**：按阵营着色（S/A/B/C 级也有颜色区分）
- **连线粗细**：按关系强度（strength）动态调整
- **连线颜色**：按关系类型着色（兄弟=蓝/敌人=红/恋人=金/师徒=紫等）

### 节点Tooltip字段

```
姓名（着色）
角色身份
等级 + 关系数量
修为 / 性格 / 阵营
人物描述（2-3句）
相关人物（ Emoji + 名字，最多6个）
```

---

## 第六步：关系类型自动推断

基于上下文关键词判断关系类型：

| 关系类型 | 判定关键词 |
|---------|-----------|
| 夫妻 | 夫妻/妻子/夫君/娘子/成亲/结婚 |
| 恋人 | 恋人/爱人/喜欢/爱慕/追求/心上人 |
| 师徒 | 师父/师傅/徒弟/徒儿/传承/指点 |
| 兄弟 | 兄弟/义兄/大哥/二哥/妹妹/姐姐 |
| 主仆 | 主人/属下/手下/效忠/忠诚 |
| 敌人 | 敌人/仇敌/杀/战/对抗 |
| 盟友 | 盟友/战友/联队长/团长 |
| 其他 | 默认值 |

---

## 第七步：主题曲生成（可独立使用）

> 当用户要求生成「主题曲/片头曲/片尾曲/OST/配乐」时执行
> **注意**：可独立使用，不需要先做完整人物分析

### 推荐主题风格

| 风格 | 情绪关键词 | 适用场景 |
|------|-----------|---------|
| 🔥 热血燃战 | 燃/热血/激昂/不屈 | 主角爆发、决战、逆袭 |
| 🌙 古风柔情 | 婉约/忧伤/唯美/深情 | 爱情线、离别、思念 |
| ⚔️ 江湖侠气 | 豪迈/洒脱/义气/快意 | 武侠门派争斗 |
| 🌌 史诗宏大 | 庄严/壮阔/神秘/命运 | 神魔大战、世界观 |
| ❄️ 冰冽虐心 | 压抑/悲怆/孤独/破碎 | 悲剧结局、失去 |
| ☀️ 希望曙光 | 希望/温暖/崛起/救赎 | 胜利、重生 |
| 🔮 宿命轮回 | 轮回/命运/混沌/超脱 | 穿越、系统、转生 |

### Suno Style 参考

**🔥 热血型**
```
Epic xianxia battle anthem, intense heroic atmosphere, ancient Chinese fantasy,
drums and erhu lead, male vocalist with powerful belting, orchestral percussion,
minor key with triumphant modulations, 90BPM D minor
```

**🌙 古风柔情型**
```
Ancient Chinese romantic ballad, melancholic and ethereal, guqin and bamboo flute,
female vocalist with soulful nasally tone, sparse arrangement, 65BPM Bb major
```

**⚔️ 江湖侠气型**
```
Wuxia martial arts world soundtrack, bold and free-spirited, pipa and dizi,
male vocalist with raw gritty tone, rhythmic drums with folk elements, 85BPM G minor
```

---

## 第八步：MiniMax Music 2.6 API 主题曲生成

> 当用户要求生成主题曲且提供了 MiniMax API Key 时，使用本节
> **API Key 格式**：`sk-cp-xxxxxxxxx`

### MiniMax Music API 调用模板

```python
import urllib.request
import json

api_key = "sk-cp-你的APIKey"
url = "https://api.minimaxi.com/v1/music_generation"

payload = {
    "model": "music-2.6",
    "prompt": "Epic Dark Fantasy Orchestral, Chinese Xianxia, War Anthem, ...",
    "lyrics": "[Intro]\n歌词内容...\n[Chorus]\n核心高潮歌词...",
    "audio_setting": {
        "sample_rate": 44100,
        "bitrate": 256000,
        "format": "mp3"
    },
    "output_format": "url"
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}'
}, method='POST')

with urllib.request.urlopen(req, timeout=120) as response:
    result = json.loads(response.read().decode('utf-8'))
    audio_url = result["data"]["audio"]
    urllib.request.urlretrieve(audio_url, "主题曲.mp3")
```

### 字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| `model` | 模型名称，固定 | `"music-2.6"` |
| `prompt` | 风格描述（英文） | `"Epic Dark Fantasy Orchestral, Chinese Xianxia..."` |
| `lyrics` | 中文歌词，带结构标签 | `[Intro]`/`[Verse]`/`[Chorus]`/`[Bridge]`/`[Outro]` |
| `audio_setting` | 音频参数 | sample_rate/ bitrate/ format |
| `output_format` | 输出格式，固定 | `"url"`（返回下载链接） |

### 歌词结构标签

```
[Intro] → [Verse] → [Pre-Chorus] → [Chorus] → [Post-Chorus] → [Bridge] → [Verse] → [Chorus] → [Outro]
```

### 推荐歌词长度

- **最短**：30-50字（可生成约30秒）
- **适中**：80-150字（可生成约60秒）
- **完整版**：200-300字（可生成约2-3分钟，需更长timeout）

### 常见错误

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `token not match group` | GroupId 不匹配 | 使用正确的GroupId参数 |
| `timeout` | 歌词过长/网络慢 | 缩短歌词或增加timeout |
| `status_code: 1003` | 参数错误 | 检查payload格式 |


## 脚本说明

### `parse.py`（输入处理）

- 编码自动检测与转换（GBK/GB18030/BIG5 → UTF-8）
- 按指定大小自动分批（每批 3000-5000 字）
- 输出：分批文本到 `/tmp/batches/batch_XX.txt`

### `generate_html.py`（图谱生成）

- 输入：角色列表 + 关系列表（JSON格式）
- 自动识别阵营（role 字段含魔/仙/妖/人/佛关键词）
- 自动计算节点大小（level + 关系数量加权）
- 孤立节点自动补全（关系中有但角色列表未收录的自动加入）
- 关系去重（同一对人物只保留一条，取最强关系类型）

### `graph_template.html`（可视化模板）

- D3.js v7 力导向布局
- SVG 无 clipPath 裁剪，节点可拖到视口外
- 响应式：自动适应窗口大小

---

## 输出交付物

| 文件 | 内容 |
|------|------|
| `人物关系数据.json` | S+A 级核心角色 + 人工分析关系 |
| `全员人物关系数据.json` | 全部角色（107人）+ 共现关系（552条） |
| `御龙征程_主角团图谱.html` | 主角团专用图（17人/44关系） |
| `御龙征程_全员图谱.html` | 全员图谱（107人/552关系） |
| `御龙征程_主题曲.mp3` | Suno 生成的 AI 主题曲 |