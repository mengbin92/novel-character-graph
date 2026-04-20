#!/usr/bin/env python3
"""
自动生成交互式人物关系图谱 HTML
- D3.js Force Simulation（拖拽 + 力导向布局）
- Hover Tooltip（鼠标悬停显示人物详情）
- 关系孤立节点自动补全
- S/A/B/C 层级节点大小
"""

import os
import json
import sys

# ── Emoji 映射 ──────────────────────────────────────────
REL_EMOJI = {
    "夫妻": "💕", "恋人": "💕", "爱情": "❤️", "道侣": "💕",
    "父子": "👨‍👦", "母子": "👩‍👦", "兄弟": "👬", "姐妹": "👭",
    "血缘": "👨‍👩‍👧", "家族": "👨‍👩‍👧",
    "师徒": "👨‍🏫", "徒弟": "👨‍🏫",
    "敌人": "⚔️", "敌对": "⚔️", "死敌": "💀",
    "主仆": "🛡️",
    "盟友": "🤝", "结义": "🤝", "朋友": "👫", "战友": "⚔️",
    "对手": "🎯",
    "收养": "🏠", "救命恩人": "🙏", "恋人未满": "💗",
    "其他": "➖",
}

def rel_emoji(rt: str) -> str:
    return REL_EMOJI.get(rt, "➖")

# ── 阵营识别 ──────────────────────────────────────────
FACTION_KEYWORDS = {
    "魔": 0, "邪": 0, "鬼": 0,
    "仙": 1, "道": 1, "神": 1,
    "龙": 2, "兽": 2, "妖": 2,
    "人": 3, "凡": 3,
    "佛": 4,
}
FACTION_NAMES = ["魔族", "仙道", "妖族", "人族", "佛门", "其他"]
FACTION_COLORS = ["#e74c3c", "#3498db", "#2ecc71", "#9b59b6", "#f39c12", "#95a5a6"]

def detect_faction(role: str) -> int:
    if not role:
        return 5
    for kw, fid in FACTION_KEYWORDS.items():
        if kw in role:
            return fid
    return 5

def get_level_color(lv: str) -> str:
    return {"S": "#ffd700", "A": "#3498db", "B": "#2ecc71", "C": "#95a5a6"}.get(lv, "#aaa")

def get_level_base_radius(lv: str) -> int:
    return {"S": 28, "A": 22, "B": 16, "C": 12}.get(lv, 14)

# ── HTML 生成 ──────────────────────────────────────────

def generate_html(
    title: str,
    subtitle: str,
    characters: list,
    relationships: list,
    output_path: str = "index.html",
    timeline_html: str = "",
    comic_html: str = "",
) -> str:
    """
    生成交互式人物关系图 HTML

    characters: [
        {
            "name": str,
            "alias": str,
            "role": str,
            "personality": str,
            "level": str,   # S/A/B/C
            "cultivation": str,
            "description": str,
        }
    ]

    relationships: [
        {
            "from_person": str,
            "to_person": str,
            "relationship_type": str,
            "emojis": str,
            "description": str,
        }
    ]
    """

    # ── 1. 统计每个节点的关系数量 ──────────────────────
    rel_count = {}
    for rel in relationships:
        for p in [rel.get("from_person", ""), rel.get("to_person", "")]:
            if p:
                rel_count[p] = rel_count.get(p, 0) + 1

    # ── 2. 补全关系中出现但不在 characters 里的孤立节点 ──
    node_names = {c["name"] for c in characters}
    chars_map = {c["name"]: c for c in characters}

    for rel in relationships:
        fp = rel.get("from_person", "")
        tp = rel.get("to_person", "")
        for p in [fp, tp]:
            if p and p not in node_names:
                chars_map[p] = {"name": p, "role": "人物", "level": "C", "alias": "", "personality": "", "cultivation": "", "description": ""}
                node_names.add(p)

    # ── 3. 构建 char_detail ─────────────────────────────
    char_detail = {}
    for name in node_names:
        c = chars_map.get(name, {})
        related = []
        for rel in relationships:
            if rel.get("from_person") == name:
                related.append((rel.get("to_person", ""), rel.get("relationship_type", "其他"), rel.get("emojis", "")))
            elif rel.get("to_person") == name:
                related.append((rel.get("from_person", ""), rel.get("relationship_type", "其他"), rel.get("emojis", "")))

        related_str = "; ".join([
            f"{e or rel_emoji(rt)}{nm}"
            for nm, rt, e in related[:6]
        ])

        char_detail[name] = {
            "role": c.get("role", ""),
            "alias": c.get("alias", ""),
            "cultivation": c.get("cultivation", ""),
            "personality": c.get("personality", ""),
            "level": c.get("level", "C"),
            "description": c.get("description", ""),
            "related": related_str or "—",
            "faction": detect_faction(c.get("role", "")),
            "rel_count": rel_count.get(name, 0),
        }

    # ── 4. 构建 D3 nodes + links ─────────────────────────
    nodes = []
    for name, d in char_detail.items():
        lv = d["level"]
        rc = d["rel_count"]
        base = get_level_base_radius(lv)
        radius = base + min(rc * 1.5, 14)
        nodes.append({
            "id": name,
            "role": d["role"],
            "group": d["faction"],
            "radius": radius,
            "level": lv,
            "tooltip": d,   # 完整详情对象
        })

    # 关系类型颜色
    rel_color_map = {
        "夫妻": "#feca57", "恋人": "#feca57", "爱情": "#feca57", "道侣": "#feca57",
        "父子": "#48dbfb", "母子": "#48dbfb", "兄弟": "#48dbfb", "姐妹": "#48dbfb",
        "血缘": "#48dbfb", "家族": "#48dbfb",
        "师徒": "#a55eea",
        "敌人": "#ff6b6b", "敌对": "#ff6b6b", "死敌": "#ff6b6b",
        "主仆": "#ff9ff3",
        "盟友": "#1dd1a1", "结义": "#1dd1a1", "朋友": "#1dd1a1", "战友": "#1dd1a1",
        "对手": "#54a0ff",
    }
    rel_str_map = {
        "夫妻": 5, "恋人": 4, "爱情": 4, "血缘": 4, "兄弟": 4,
        "师徒": 3, "结义": 3, "盟友": 3, "主仆": 2, "朋友": 2,
        "敌人": 1, "对手": 1,
    }

    links = []
    seen = set()
    for rel in relationships:
        fp, tp = rel.get("from_person", ""), rel.get("to_person", "")
        key = tuple(sorted([fp, tp]))
        if not fp or not tp or key in seen:
            continue
        seen.add(key)
        rt = rel.get("relationship_type", "其他")
        rts = rel.get("relationship_types", [rt])
        strength = sum(rel_str_map.get(r, 1) for r in rts) / max(len(rts), 1)
        links.append({
            "source": fp,
            "target": tp,
            "type": "/".join(rts),
            "color": rel_color_map.get(rt, "#54a0ff"),
            "width": max(1, min(6, strength)),
        })

    # ── 5. 人物卡片 HTML ────────────────────────────────
    level_order = ["S", "A", "B", "C"]
    by_level = {lv: [] for lv in level_order}
    for n in nodes:
        lv = n.get("level", "C")
        by_level.setdefault(lv, []).append(n)
    for lv in by_level:
        by_level[lv].sort(key=lambda x: -x.get("tooltip", {}).get("rel_count", 0))

    cards_html = ""
    for lv in level_order:
        chars_lv = by_level.get(lv, [])
        if not chars_lv:
            continue
        lv_color = get_level_color(lv)
        stars = {"S": "⭐⭐⭐⭐", "A": "⭐⭐⭐", "B": "⭐⭐", "C": "⭐"}.get(lv, "")
        cards_html += f'<div class="level-header" style="color:{lv_color}">{stars} {lv}级人物 ({len(chars_lv)}人)</div>'
        cards_html += '<div class="cards-grid">'
        for n in chars_lv[:40]:  # 每级最多40人
            tt = n.get("tooltip", {})
            lv_c = get_level_color(n.get("level", "C"))
            cards_html += f'''<div class="char-card" onclick="focusNode('{n["id"]}')">
                <div class="char-name" style="color:{lv_c}">{n["id"]}</div>
                <div class="char-role">{tt.get('role', '') or '—'}</div>
                <div class="char-cul">{tt.get('cultivation', '') or '—'}</div>
                <div class="char-per">{tt.get('personality', '') or '—'}</div>
                <div class="char-desc">{tt.get('description', '') or '—'}</div>
                <div class="char-rels">{tt.get('related', '') or '—'}</div>
            </div>'''
        cards_html += '</div>'

    # ── 6. 势力格局 HTML ────────────────────────────────
    faction_stats = []
    for fid, fname in enumerate(FACTION_NAMES):
        cnt = sum(1 for n in nodes if n.get("group") == fid)
        faction_stats.append({"name": fname, "count": cnt, "color": FACTION_COLORS[fid]})

    world_html = ""
    for fs in faction_stats:
        if fs["count"] > 0:
            pct = int(fs["count"] / max(len(nodes), 1) * 100)
            world_html += f'''<div class="faction-item">
                <div class="faction-info"><span class="faction-dot" style="background:{fs["color"]}"></span>{fs["name"]} ({fs["count"]}人)</div>
                <div class="faction-bar"><div class="faction-fill" style="width:{pct}%;background:{fs["color"]}"></div></div>
            </div>'''

    # ── 7. 序列化 JS 数据 ───────────────────────────────
    nodes_js = json.dumps(nodes, ensure_ascii=False)
    links_js = json.dumps(links, ensure_ascii=False)
    faction_colors_js = json.dumps(FACTION_COLORS, ensure_ascii=False)
    faction_names_js = json.dumps(FACTION_NAMES, ensure_ascii=False)
    char_detail_js = json.dumps(char_detail, ensure_ascii=False)

    # ── 8. 读取并渲染模板 ───────────────────────────────
    template_path = os.path.join(os.path.dirname(__file__), '../assets/graph_template.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    html = html.replace('{{TITLE}}', title)
    html = html.replace('{{SUBTITLE}}', subtitle)
    html = html.replace('{{NODES}}', nodes_js)
    html = html.replace('{{LINKS}}', links_js)
    html = html.replace('{{FACTION_COLORS}}', faction_colors_js)
    html = html.replace('{{FACTION_NAMES}}', faction_names_js)
    html = html.replace('{{CHAR_DETAIL}}', char_detail_js)
    html = html.replace('{{CARDS_HTML}}', cards_html)
    html = html.replace('{{WORLD_HTML}}', world_html)
    html = html.replace('{{TOTAL_CHARS}}', str(len(nodes)))
    html = html.replace('{{TOTAL_RELS}}', str(len(links)))

    # 时间线和漫画设定（可选）
    default_timeline = '''<div style="color:#666688; text-align:center; padding:60px;">
        📝 剧情时间线由 AI 分析自动生成<br>
        <span style="font-size:13px;">将在 parse.py 完整解析后自动填充</span>
    </div>'''
    default_comic = '''<div class="comic-placeholder">
        🎨 漫画设定功能开发中<br>
        <span>可基于人物描述生成 AI 漫画分镜</span>
    </div>'''
    html = html.replace('{{TIMELINE_HTML}}', timeline_html or default_timeline)
    html = html.replace('{{COMIC_HTML}}', comic_html or default_comic)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ 生成完成: {output_path}")
    print(f"   人物总数: {len(nodes)} | 关系数: {len(links)}")
    return output_path


if __name__ == "__main__":
    # 用法示例
    if len(sys.argv) >= 2:
        # 从 JSON 文件加载数据
        json_path = sys.argv[1]
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        characters = data.get("characters", [])
        relationships = data.get("relationships", [])
        output = sys.argv[2] if len(sys.argv) > 2 else "index.html"
        title = data.get("title", "小说人物图谱")
        subtitle = data.get("subtitle", f"共 {len(characters)} 个人物")
        generate_html(title, subtitle, characters, relationships, output)
    else:
        print("用法: python3 generate_html.py <data.json> [output.html]")
