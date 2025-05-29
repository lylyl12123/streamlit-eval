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
    teacher_id = st.session_state.teacher_id
    models = ["模型A", "模型B", "模型C"]
    model_keys = ["A", "B", "C"]
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

    scores = st.session_state.all_scores[teacher_id].setdefault("part1_scores", {})
    part1_key = f"part1_{poid}"
    scores.setdefault(part1_key, {})

    for dim, control_type in dimensions.items():
        st.markdown(f"**{dim}**")
        cols = st.columns(3)
        scores[part1_key].setdefault(dim, {})

        for i, model in enumerate(models):
            key = f"{part1_key}_{dim}_{model}"
            prev_value = scores[part1_key][dim].get(model_keys[i], 0)

            if control_type == "slider_int":
                val = cols[i].slider(model, 0, 10, int(prev_value), step=1, key=key)
            elif control_type == "slider_float":
                val = cols[i].slider(model, 0.0, 1.0, float(prev_value), step=0.1, key=key)
            elif control_type == "radio":
                val = cols[i].radio(model, [0, 1], index=int(prev_value), horizontal=True, key=key)
            else:
                val = 0

            scores[part1_key][dim][model_keys[i]] = val

def render_part2_scoring(part2_list, poid):
    teacher_id = st.session_state.teacher_id
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

    scores = st.session_state.all_scores[teacher_id].setdefault("part2_scores", {})

    for idx, block in enumerate(part2_list):
        block_type = block["type"]
        block_key = f"part2_{poid}_t{block_type}_{idx}"
        st.markdown(f"**{type_map[block_type]}**")
        cols = st.columns(3)

        scores.setdefault(block_key, {})

        for i, model in enumerate(models):
            key = f"{block_key}_{model}"
            prev_value = scores[block_key].get(model, type_options[block_type][0])
            val = cols[i].radio(model, type_options[block_type], index=type_options[block_type].index(prev_value), horizontal=True, key=key)
            scores[block_key][model] = val


def render_part3_scoring(item, poid):
    teacher_id = st.session_state.teacher_id
    models = ["A", "B", "C"]
    scores = st.session_state.all_scores[teacher_id].setdefault("part3_scores", {})

    score_labels = [
        "是否回答了学生的问题（0=否，1=是）",
        "是否正确回答了学生的问题（0=否，1=是）"
    ]

    for score_type, label in enumerate(score_labels):
        score_key = f"part3_{poid}_{item['question_id']}_score{score_type}"
        st.markdown(f"**{label}**")
        cols = st.columns(3)

        scores.setdefault(score_key, {})

        for i, model in enumerate(models):
            key = f"{score_key}_{model}"
            prev_value = scores[score_key].get(model, 0)
            val = cols[i].radio(model, [0, 1], index=prev_value, horizontal=True, key=key)
            scores[score_key][model] = val




# ========== 主程序入口 ==========
def main():
    # ========== 入口页：教师编号输入 ==========
    if "teacher_id" not in st.session_state:
        st.title("教师标注系统")
        st.markdown("请输入您的教师编号（例如 T001）：")
        teacher_input = st.text_input("教师编号", "")
        if st.button("开始标注") and teacher_input.strip():
            st.session_state.teacher_id = teacher_input.strip().upper()
            st.rerun()
        return  # 停在编号页

    teacher_id = st.session_state.teacher_id

    if "all_scores" not in st.session_state:
        st.session_state.all_scores = {}

    # 初始化当前教师的评分记录（隔离）
    if teacher_id not in st.session_state.all_scores:
        st.session_state.all_scores[teacher_id] = {
            "part1_scores": {},
            "part2_scores": {},
            "part3_scores": {}
        }

    # ========== 加载数据：每位教师一个 JSON ==========
    file_path = f"data_{teacher_id}.json"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        st.error(f"未找到编号 {teacher_id} 对应的数据文件：`{file_path}`。请联系管理员。")
        if st.button("重新输入编号"):
            del st.session_state.teacher_id
            st.rerun()
        return

    # ========== 页面导航 ==========
    total_pages = len(data)
    if "page" not in st.session_state:
        st.session_state.page = 0
    if "results" not in st.session_state:
        st.session_state.results = {}

    idx = st.session_state.page
    current = data[idx]
    poid = current.get("poid", f"id_{idx}")

        # 页面导航（顶部 + 跳转）
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("上一条", key="top_prev") and idx > 0:
            st.session_state.page -= 1
            st.rerun()

    with col2:
        sub_col1, sub_col2, sub_col3 = st.columns([1, 3, 2])
        with sub_col2:
            with st.form(key="jump_form"):
                jump_page = st.number_input("跳转到第几条（从 1 开始）", min_value=1, max_value=total_pages, value=idx + 1, step=1, key="jump_input")
                submitted = st.form_submit_button("跳转")
                if submitted:
                    st.session_state.page = jump_page - 1
                    st.rerun()

    with col3:
        if st.button("下一条", key="top_next") and idx < total_pages - 1:
            st.session_state.page += 1
            st.rerun()


    # ========== 展示任务内容 ==========
    st.markdown(f"### 第 {idx + 1} / {total_pages} 条样本")
    st.markdown(f"**样本 ID：** {poid}")

    display_part1(current["content"]["part1"], poid)
    display_part2(current["content"]["part2"], poid)
    display_part3(current["content"]["part3"], poid)


    # ========== 底部也要操作 ==========
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("上一条", key="bottom_prev") and idx > 0:
            st.session_state.page -= 1
            st.rerun()
    with col3:
        if st.button("下一条", key="bottom_next") and idx < total_pages - 1:
            st.session_state.page += 1
            st.rerun()

    # ========== 导出按钮 ==========
    if st.button("导出所有评分结果"):
        teacher_scores = st.session_state.all_scores.get(teacher_id, {})
        all_scores = []

        # ==== Part1 ====
        for k, v in teacher_scores.get("part1_scores", {}).items():
            poid = k.replace("part1_", "")
            for dim, models in v.items():
                score_a = models.get("A", "")
                score_b = models.get("B", "")
                score_c = models.get("C", "")
                if score_a == "" and score_b == "" and score_c == "":
                    continue
                row = {
                    "poid": poid,
                    "part": "part1",
                    "type": dim,
                    "dimension": dim,
                    "score_A": score_a,
                    "score_B": score_b,
                    "score_C": score_c
                }
                all_scores.append(row)

        # ==== Part2 ====
        for k, v in teacher_scores.get("part2_scores", {}).items():
            part_match = re.match(r"part2_(.*?)_t(\d)_(\d+)", k)
            if part_match:
                poid_raw, tval, block_idx = part_match.groups()
                label = f"type{tval}_block{block_idx}"
                poid_clean = poid_raw.split("_")[0]  # 去掉 _idx 部分，保留 poid
                row = {
                    "poid": poid_clean,
                    "part": "part2",
                    "type": label,
                    "dimension": "引导质量" if tval in ["1", "2"] else "导正话题",
                    "score_A": v.get("A", ""),
                    "score_B": v.get("B", ""),
                    "score_C": v.get("C", "")
                }
                all_scores.append(row)


        # ==== Part3 ====
        for k, v in teacher_scores.get("part3_scores", {}).items():
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

        df = pd.DataFrame(all_scores)
        csv = df.to_csv(index=False, encoding="utf-8-sig")
        b64 = base64.b64encode(csv.encode("utf-8-sig")).decode()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"评分结果_{teacher_id}_{timestamp}.csv"
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 点击下载评分表</a>'
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
