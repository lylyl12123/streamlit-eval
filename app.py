import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime
import base64

# ========== 工具函数 ==========
def render_latex_textblock(text):
    pattern = re.compile(r"(\${1,2}.*?\${1,2})")
    parts = pattern.split(text)
    for part in parts:
        if part.startswith("$$") and part.endswith("$$"):
            st.latex(part.strip("$"))
        elif part.startswith("$") and part.endswith("$"):
            st.latex(part.strip("$"))
        else:
            st.markdown(part)

def render_turn(turn: dict, model_name: str):
    if "model_respond" in turn:
        st.markdown(f"**模型 {model_name}：**")
        render_latex_textblock(turn["model_respond"])
    if "user" in turn:
        st.markdown(f"**学生：**")
        render_latex_textblock(turn["user"])

# ========== 展示布局的函数 ==========
def display_part1(part1, poid):
    st.markdown("### 🧩 Part 1: 模型完整对话")
    st.markdown("**题目：**")
    render_latex_textblock(part1["question"])

    st.markdown("#### 📊 模型 A / B / C 对话对齐展示")

    models = ["A", "B", "C"]
    turns = [part1[model] for model in models]

    # 计算最大轮数（补空用）
    max_len = max(len(t) for t in turns)
    for t in turns:
        while len(t) < max_len:
            t.append({})  # 补空字典

    col_a, col_b, col_c = st.columns(3)
    for i in range(max_len):
        with col_a:
            render_turn(turns[0][i], "A")
        with col_b:
            render_turn(turns[1][i], "B")
        with col_c:
            render_turn(turns[2][i], "C")

    #这里是评分表单
    render_part1_scoring(poid)
    
def display_part2(part2_list, poid):
    st.markdown("### 🧪 Part 2: 不同学生反馈场景")
    type_map = {1: "✅ 理解（do）", 2: "❌ 不理解（don’t）", 3: "💬 无关回答（noise）"}

    for idx, block in enumerate(part2_list):
        st.markdown(f"#### {type_map[block['type']]} 类型")
        st.markdown("**题目：**")
        render_latex_textblock(block["question"])

        models = ["A", "B", "C"]
        turns = [block["content"][m] for m in models]
        max_len = max(len(t) for t in turns)
        for t in turns:
            while len(t) < max_len:
                t.append({})  # 补空

        col_a, col_b, col_c = st.columns(3)
        for i in range(max_len):
            with col_a:
                render_turn(turns[0][i], "A")
            with col_b:
                render_turn(turns[1][i], "B")
            with col_c:
                render_turn(turns[2][i], "C")
        render_part2_scoring([block], f"{poid}_idx{idx}")
    

def display_part3(part3_list, poid):
    st.markdown("### 🎯 Part 3: 单轮反馈能力评估")
    for item in part3_list:
        st.markdown(f"**类型：** {item['type']}")
        st.markdown("**题目：**")
        render_latex_textblock(item["question"])
        st.markdown("**学生：**")
        render_latex_textblock(item["single_dialog"]["user"])

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("**模型 A 回复：**")
            render_latex_textblock(item["single_dialog"]["model_response_A"])
        with col_b:
            st.markdown("**模型 B 回复：**")
            render_latex_textblock(item["single_dialog"]["model_response_B"])
        with col_c:
            st.markdown("**模型 C 回复：**")
            render_latex_textblock(item["single_dialog"]["model_response_C"])

        st.markdown("**教师参考回复：**")
        render_latex_textblock(item["single_dialog"]["gt"])

        render_part3_scoring(item, poid)

# ========== 评分表单的函数 ==========

def render_part1_scoring(poid: str):
    #st.markdown("### 📝 Part 1 评分表单")
    st.markdown("请对以下指标进行打分：")

    models = ["模型A", "模型B", "模型C"]
    dimensions = {
        "语言流畅（1-10）": "slider_int",
        "是否指出知识点（0,1）": "radio",
        "知识点内容是否正确（0,1）": "radio",
        "最终答案正确（0,1）": "radio",
        "部分答案正确（0,1）": "radio",
        "过程正确（0~1，步长0.1）": "slider_float",
        "是否分步讲解（0,1）": "radio",
        "提问质量（高质量提问比例0~1）": "slider_float"
    }

    if "part1_scores" not in st.session_state:
        st.session_state.part1_scores = {}

    part1_key = f"part1_{poid}"
    if part1_key not in st.session_state.part1_scores:
        st.session_state.part1_scores[part1_key] = {}

    for dim, control_type in dimensions.items():
        st.markdown(f"**{dim}**")
        cols = st.columns(3)
        for i, model in enumerate(models):
            key = f"{part1_key}_{dim}_{model}"
            prev_value = st.session_state.part1_scores[part1_key].get(dim, {}).get(model, 0)

            if control_type == "slider_int":
                val = cols[i].slider(f"{model}", 0, 10, int(prev_value), step=1, key=key)
            elif control_type == "slider_float":
                val = cols[i].slider(f"{model}", 0.0, 1.0, float(prev_value), step=0.1, key=key)
            elif control_type == "radio":
                val = cols[i].radio(f"{model}", [0, 1], index=int(prev_value), horizontal=True, key=key)
            else:
                val = 0  # fallback

            st.session_state.part1_scores[part1_key].setdefault(dim, {})[model] = val

def render_part2_scoring(part2_list, poid):
    #st.markdown("### 📝 Part 2 评分表单")

    models = ["A", "B", "C"]
    type_map = {
        1: "引导质量（0=未引导，1=成功引导）",
        2: "引导质量（0=未引导，1=成功引导）",
        3: "导正话题（0=偏离话题，0.5=忽略但继续讲题，1=纠正话题）"
    }
    type_options = {
        1: [0, 1],
        2: [0, 1],
        3: [0, 0.5, 1]
    }

    if "part2_scores" not in st.session_state:
        st.session_state.part2_scores = {}

    for idx, block in enumerate(part2_list):
        block_type = block["type"]
        block_key = f"part2_{poid}_t{block_type}_{idx}"
        st.markdown(f"**{type_map[block_type]}**")
        cols = st.columns(3)

        if block_key not in st.session_state.part2_scores:
            st.session_state.part2_scores[block_key] = {}

        for i, model in enumerate(models):
            key = f"{block_key}_{model}"
            prev_value = st.session_state.part2_scores[block_key].get(model, type_options[block_type][0])
            val = cols[i].radio(f"{model}", type_options[block_type], index=type_options[block_type].index(prev_value), horizontal=True, key=key)
            st.session_state.part2_scores[block_key][model] = val

def render_part3_scoring(item, poid):
    models = ["A", "B", "C"]
    if "part3_scores" not in st.session_state:
        st.session_state.part3_scores = {}

    score_labels = [
        "是否回答了学生的问题（0=否，1=是）",
        "是否正确回答了学生的问题（0=否，1=是）"
    ]

    for score_type, label in enumerate(score_labels):
        score_key = f"part3_{poid}_{item['question_id']}_score{score_type}"
        st.markdown(f"**{label}**")
        cols = st.columns(3)

        if score_key not in st.session_state.part3_scores:
            st.session_state.part3_scores[score_key] = {}

        for i, model in enumerate(models):
            key = f"{score_key}_{model}"
            prev_value = st.session_state.part3_scores[score_key].get(model, 0)
            val = cols[i].radio(f"{model}", [0, 1], index=prev_value, horizontal=True, key=key)
            st.session_state.part3_scores[score_key][model] = val



# ========== 主程序入口 ==========
def main():

    # 加载数据
    with open("test_ques.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    total_pages = len(data)
    if "page" not in st.session_state:
        st.session_state.page = 0
    if "results" not in st.session_state:
        st.session_state.results = {}

    idx = st.session_state.page
    current = data[idx]
    poid = current.get("poid", f"id_{idx}")

    # 页面导航
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("上一条") and idx > 0:
            st.session_state.page -= 1
            st.rerun()
    with col3:
        if st.button("下一条") and idx < total_pages - 1:
            st.session_state.page += 1
            st.rerun()

    # 显示信息
    st.markdown(f"### 第 {idx + 1} / {total_pages} 条样本")
    st.markdown(f"**样本 ID：** {poid}")

    display_part1(current["content"]["part1"], poid)
    display_part2(current["content"]["part2"], poid)
    display_part3(current["content"]["part3"], poid)


    # 导出功能
    if st.button("导出所有评分结果"):
        all_scores = []

        # ==== Part1 ====
        for k, v in st.session_state.get("part1_scores", {}).items():
            poid = k.replace("part1_", "")
            for dim, models in v.items():
                row = {
                    "poid": poid,
                    "part": "part1",
                    "type": dim,
                    "dimension": dim,
                    "score_A": models.get("A", ""),
                    "score_B": models.get("B", ""),
                    "score_C": models.get("C", "")
                }
                all_scores.append(row)

        # ==== Part2 ====
        for k, v in st.session_state.get("part2_scores", {}).items():
            part_match = re.match(r"part2_(.*?)_t(\d)_(\d+)", k)
            if part_match:
                poid, tval, block_idx = part_match.groups()
                label = f"type{tval}_block{block_idx}"
                row = {
                    "poid": poid,
                    "part": "part2",
                    "type": label,
                    "dimension": "引导质量" if tval in ["1", "2"] else "导正话题",
                    "score_A": v.get("A", ""),
                    "score_B": v.get("B", ""),
                    "score_C": v.get("C", "")
                }
                all_scores.append(row)

        # ==== Part3 ====
        for k, v in st.session_state.get("part3_scores", {}).items():
            part_match = re.match(r"part3_(.*?)_(.*?)_score(\d)", k)
            if part_match:
                poid, qid, score_type = part_match.groups()
                label = "是否回答学生问题" if score_type == "0" else "是否正确回答学生问题"
                row = {
                    "poid": poid,
                    "part": "part3",
                    "type": f"score{score_type}",
                    "dimension": label,
                    "score_A": v.get("A", ""),
                    "score_B": v.get("B", ""),
                    "score_C": v.get("C", "")
                }
                all_scores.append(row)

        # ==== 导出并自动下载 ====
        df = pd.DataFrame(all_scores)
        csv = df.to_csv(index=False, encoding="utf-8-sig")
        csv_bytes = csv.encode('utf-8-sig')  # 👈 添加这行确保 BOM
        b64 = base64.b64encode(csv_bytes).decode()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        href = f'<a href="data:file/csv;base64,{b64}" download="评分结果_{timestamp}.csv">📥 点击下载评分表</a>'
        st.markdown(href, unsafe_allow_html=True)



# 启动
if __name__ == "__main__":
    st.set_page_config(layout="wide")

    st.markdown("""
        <style>
            .block-container {
                padding-left: 2rem;
                padding-right: 2rem;
            }
        </style>
    """, unsafe_allow_html=True)

    main()
