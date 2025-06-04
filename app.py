import random
import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime
import base64

# ========== 工具函数 ==========

#渲染文本
def render_latex_textblock(text):
    pattern = re.compile(r"(\${1,2}.*?\${1,2})")
    parts = pattern.split(text)
    result = ""
    for part in parts:
        if part.startswith("$$") or part.startswith("$"):
            result += part  # 保留 $ 符号，用于 markdown 渲染
        else:
            result += part.replace("\n", "<br>")  # 处理换行
    st.markdown(result, unsafe_allow_html=True)

#渲染对话轮
def render_turn(turn: dict, model_name: str):
    if "model_respond" in turn:
        st.markdown(f"模型 {model_name}：")
        render_latex_textblock(turn["model_respond"])
    if "user" in turn:
        st.markdown(f"学生：")
        render_latex_textblock(turn["user"])


#渲染竖分割线
def render_vertical_divider():
    st.markdown("""
        <div style='height: 75px; border-left: 1px solid lightgray; margin: auto 0;'>&nbsp;</div>
    """, unsafe_allow_html=True)


# ========== 展示布局的函数 ==========
def display_part1(part1, poid):
    st.markdown("### 🧩 Part 1: 模型答疑中的整体评价")
    st.markdown("**题目：**")
    render_latex_textblock(part1["question"])

    st.markdown("#### 📊 模型 1 / 2 / 3 对该问题的答疑过程")

    model_map = st.session_state.model_shuffle_map[st.session_state.page]
    model_keys = [model_map[m] for m in ["1", "2", "3"]]
    model_names = ["模型1", "模型2", "模型3"]
    model_turns = [part1.get(k, []) for k in model_keys]

    col_a, col_b, col_c = st.columns(3)
    for col, turns, name in zip([col_a, col_b, col_c], model_turns, model_names):
        with col:
            st.markdown(f"#### 🤖 {name}")

            # 拼接 markdown 内容
            blocks = []
            for idx, turn in enumerate(turns):
                if idx != 0 and "user" in turn:
                    blocks.append("**学生：**\n" + turn["user"])
                if "model_respond" in turn:
                    blocks.append(f"**{name}：**\n" + turn["model_respond"])
                blocks.append("---")
            content = "\n\n".join(blocks)

            # 渲染可滚动区域（外层是 HTML 滚动，内层是 markdown 内容）
            st.markdown(f"""
<div style='height: 500px; overflow-y: auto; padding-right:10px; border: 1px solid #ccc; border-radius: 10px; padding: 10px; background-color: #f9f9f9;'>
{content}
</div>
""", unsafe_allow_html=True)

    if "answer" in part1:
        render_latex_textblock("##### ✅ 该题正确答案：" + part1["answer"])

    render_part1_scoring(poid)
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)





def display_part2(part2_list, poid):
    st.markdown("### 🧪 Part 2: 模型在引导解题和引导话题上的评价")
    type_map = {1: "✅ 理解（do）", 2: "❌ 不理解（don’t）", 3: "💬 无关回答（noise）"}

    model_map = st.session_state.model_shuffle_map[st.session_state.page]
    model_keys = [model_map[m] for m in ["1", "2", "3"]]
    model_names = ["1", "2", "3"]

    for idx, block in enumerate(part2_list):
        st.markdown(f"#### {type_map[block['type']]} 类型")

        # === 展示题干，带分隔线 ===
        col_a, col_mid1, col_b, col_mid2, col_c = st.columns([1, 0.03, 1, 0.03, 1])
        with col_a:
            st.markdown(f"**模型 {model_names[0]} 的题目：**")
            model_data = block["content"][model_keys[0]]
            render_latex_textblock(model_data.get("question", "（无题目）"))
        with col_mid1:
            render_vertical_divider()
        with col_b:
            st.markdown(f"**模型 {model_names[1]} 的题目：**")
            model_data = block["content"][model_keys[1]]
            render_latex_textblock(model_data.get("question", "（无题目）"))
        with col_mid2:
            render_vertical_divider()
        with col_c:
            st.markdown(f"**模型 {model_names[2]} 的题目：**")
            model_data = block["content"][model_keys[2]]
            render_latex_textblock(model_data.get("question", "（无题目）"))

        # === 构造对话 turns ===
        turns = []
        for key in model_keys:
            model_data = block["content"][key]
            if isinstance(model_data, dict) and "dialogue" in model_data:
                turns.append(model_data["dialogue"])
            else:
                turns.append(model_data)  # 向后兼容旧格式

        max_len = max(len(t) for t in turns)
        for t in turns:
            while len(t) < max_len:
                t.append({})

        # === 展示对话内容，带分隔线 ===
        col_a, col_mid1, col_b, col_mid2, col_c = st.columns([1, 0.03, 1, 0.03, 1])
        for i in range(max_len):
            with col_a:
                render_turn(turns[0][i], model_names[0])
            with col_mid1:
                render_vertical_divider()
            with col_b:
                render_turn(turns[1][i], model_names[1])
            with col_mid2:
                render_vertical_divider()
            with col_c:
                render_turn(turns[2][i], model_names[2])

        render_part2_scoring([block], f"{poid}_idx{idx}")

        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)


def display_part3(part3_list, poid):
    st.markdown("### 🎯 Part 3: 单轮反馈能力评估")

    model_map = st.session_state.model_shuffle_map[st.session_state.page]
    model_keys = [model_map[m] for m in ["1", "2", "3"]]
    model_names = ["1", "2", "3"]

    for item in part3_list:
        st.markdown(f"**类型：** {item['type']}")
        st.markdown("**题目：**")
        render_latex_textblock(item["question"])
        st.markdown("**学生：**")
        render_latex_textblock(item["single_dialog"]["user"])

        # === 模型回复三栏 + 分隔线 ===
        col_a, col_mid1, col_b, col_mid2, col_c = st.columns([1, 0.03, 1, 0.03, 1])
        with col_a:
            st.markdown(f"**模型 {model_names[0]} 回复：**")
            render_latex_textblock(item["single_dialog"][f"model_response_{model_keys[0]}"])
        with col_mid1:
            render_vertical_divider()
        with col_b:
            st.markdown(f"**模型 {model_names[1]} 回复：**")
            render_latex_textblock(item["single_dialog"][f"model_response_{model_keys[1]}"])
        with col_mid2:
            render_vertical_divider()
        with col_c:
            st.markdown(f"**模型 {model_names[2]} 回复：**")
            render_latex_textblock(item["single_dialog"][f"model_response_{model_keys[2]}"])

        st.markdown("**教师参考回复：**")
        render_latex_textblock(item["single_dialog"]["gt"])

        render_part3_scoring(item, poid)

        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)



# ========== 评分表单的函数 ==========

def render_part1_scoring(poid: str):
    teacher_id = st.session_state.teacher_id
    model_names = ["模型1", "模型2", "模型3"]
    model_map = st.session_state.model_shuffle_map[st.session_state.page]
    model_keys = [model_map[str(i)] for i in range(1, 4)]

    dimensions = {
        "整体偏好排序（主观倾向）": "rank",
        "语言流畅度": "slider_int",
        "是否指出知识点": "radio",
        "知识点内容是否正确": "radio",
        "最终答案正确": "radio",
        "过程正确": "slider_float",
        "是否分步讲解": "radio",
        "提问质量": "slider_float"
    }

    descriptions = {
        "整体偏好排序（主观倾向）": "阅读以上三个模型的答疑对话后，假设你需要从中选择一个用于实际学生答疑，请根据你的主观判断，对这三个模型进行偏好排序（排在前面的表示你最倾向选择的模型）。",
        "语言流畅度": "请为上面对话中模型的语言流畅度打分，满分（10）的标准为语言符合语法、表达简洁准确、清晰易懂。",
        "是否指出知识点": "在与学生对话的过程中，模型是否有明显地告知学生该题目涉及的知识点,并且知识点正确，如有则选择1，无则选择0.",
        "知识点内容是否正确": "请判断对话中提及的知识点、概念描述是否都是正确的？是则选择1，否则选择0",
        "最终答案正确": "请判断对话中，模型给学生提供的最终答案是否正确？（如果对话还没推进到最终答案，则视为没有给出最终答案）是则选择1，否则选择0.",
        "过程正确": "请判断模型在逐步讲解的过程中，过程正确的部分大致占比多少？比如，如果在讲解中大致正确了一半，或是在一个有两个小问的题目中正确了一个小问，则分数为0.5。",
        "是否分步讲解": "请判断对话中，模型是否遵循了分步骤对学生进行讲解的原则(每次对话对学生进行下一步的引导)，对学生进行逐步的讲解？是则选择1；如果并未逐步讲解，而是直接给出结果，则选择0.",
        "提问质量": "请你判断在讲解过程中，模型对学生提出的高质量问题的比例大致有多少？类似于“你明白了吗？”“你理解了吗？”等没有给出具体信息的内容，视为低质量提问；有具体引导学生进行下一步计算或者下一个推导步骤的，如“请你试着完成计算”“那么下一步是不是应该...？”视为高质量提问。"
    }

    scores = st.session_state.all_scores[teacher_id].setdefault("part1_scores", {})
    part1_key = f"part1_{poid}"
    scores.setdefault(part1_key, {})

    render_latex_textblock("###### 请根据以上内容，根据下列维度评分：")

    for i, (dim, control_type) in enumerate(dimensions.items(), start=1):
        scores[part1_key].setdefault(dim, {})  # 防止 KeyError

        st.markdown(f"<span style='font-size: 18px; font-weight: bold;'>（{i}） {dim}</span>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 16px; padding-left: 1em;'>{descriptions[dim]}</div>", unsafe_allow_html=True)

        if control_type == "rank":
            options = model_names
            default_order = model_names
            selected = st.multiselect("请按偏好排序（从左到右表示从高到低）", options, default=default_order, key=f"{part1_key}_{dim}")
            if len(selected) == 3:
                for idx, mname in enumerate(selected):
                    model_idx = model_names.index(mname)
                    scores[part1_key][dim][model_keys[model_idx]] = 3 - idx
            else:
                for i in range(3):
                    scores[part1_key][dim][model_keys[i]] = 0
            continue  # 跳过后续控件布局

        cols = st.columns([1, 0.05, 1, 0.05, 1])
        for j, (col, model_name) in enumerate(zip([cols[0], cols[2], cols[4]], model_names)):
            key = f"{part1_key}_{dim}_{model_name}"
            prev_value = scores[part1_key][dim].get(model_keys[j], 0)

            with col:
                subcol1, subcol2 = st.columns([1, 2])
                with subcol1:
                    st.markdown(
                        f"<div style='text-align: center; padding-top: 0.5rem; font-weight: bold;'>{model_name}</div>",
                        unsafe_allow_html=True
                    )
                with subcol2:
                    if control_type == "slider_int":
                        st.markdown("<style>div[data-baseweb='slider'] { max-width: 130px; }</style>", unsafe_allow_html=True)
                        val = st.slider("", 0, 10, int(prev_value), step=1, key=key)
                    elif control_type == "slider_float":
                        st.markdown("<style>div[data-baseweb='slider'] { max-width: 130px; }</style>", unsafe_allow_html=True)
                        val = st.slider("", 0.0, 1.0, float(prev_value), step=0.1, key=key)
                    elif control_type == "radio":
                        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
                        val = st.radio("", [0, 1], index=int(prev_value), horizontal=True, key=key)
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        val = 0
                    scores[part1_key][dim][model_keys[j]] = val

        # 插入竖线
        with cols[1]:
            render_vertical_divider()
        with cols[3]:
            render_vertical_divider()





def render_part2_scoring(part2_list, poid):
    teacher_id = st.session_state.teacher_id
    model_names = ["模型1", "模型2", "模型3"]
    model_map = st.session_state.model_shuffle_map[st.session_state.page]
    model_keys = [model_map[str(i)] for i in range(1, 4)]

    type_map = {
        1: "引导质量（理解）",
        2: "引导质量（不理解）",
        3: "导正话题"
    }

    type_options = {
        1: [0, 1],
        2: [0, 1],
        3: [0, 0.5, 1]
    }

    description_map = {
        "引导质量（理解）": "    判断模型是否能根据学生的理解/不理解进行适当引导。有效引导的定义为：在学生表示理解的情况下，当前轮对话对比上一轮对话应在逻辑上推进问题的解决，推动到下一个步骤或更深的推理。若当前轮对话没有逻辑推进，则认为引导质量为0；如果有推进，则引导质量为1。",
        "引导质量（不理解）": "    判断模型是否能根据学生的理解/不理解进行适当引导。有效引导的定义为：在学生表示不理解的情况下，当前轮对话应对比上一轮对话增加新的内容，如提供更多的解释、示例或提示，帮助学生更好地理解问题。",
        "导正话题": "    判断模型是否能在学生答非所问时将话题拉回问题本身。如果模型顺着学生的无关话题向下，则为0；如果模型无视学生无关发言，直接继续讲解，则为0.5；如果模型引导学生话题回到题目上，并继续讲解，则为1分。"
    }

    scores = st.session_state.all_scores[teacher_id].setdefault("part2_scores", {})

    for idx, block in enumerate(part2_list):
        block_type = block["type"]
        label = type_map[block_type]
        block_key = f"part2_{poid}_t{block_type}_{idx}"

        # === 标题（编号） ===
        st.markdown(f"<div style='font-size:18px; font-weight: bold;'>（{block_type}） {label}</div>", unsafe_allow_html=True)

        # === 描述（加大字体 + 缩进） ===
        st.markdown(f"<div style='font-size: 16px; padding-left: 1em;'>{description_map.get(label, '')}</div>", unsafe_allow_html=True)


        # === 布局：带分割线 ===
        cols = st.columns([1, 0.05, 1, 0.05, 1])
        scores.setdefault(block_key, {})

        for i, (col, model_name) in enumerate(zip([cols[0], cols[2], cols[4]], model_names)):
            key = f"{block_key}_{model_name}"
            prev_value = scores[block_key].get(model_keys[i], type_options[block_type][0])

            with col:
                subcol1, subcol2 = st.columns([1, 2])
                with subcol1:
                    st.markdown(
                        f"<div style='text-align: center; padding-top: 0.3rem; font-weight: bold;'>{model_name}</div>",
                        unsafe_allow_html=True
                    )
                with subcol2:
                    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
                    val = st.radio("", type_options[block_type],
                                   index=type_options[block_type].index(prev_value),
                                   horizontal=True, key=key)
                    st.markdown("</div>", unsafe_allow_html=True)

            scores[block_key][model_keys[i]] = val

        # === 插入分隔竖线 ===
        with cols[1]:
            render_vertical_divider()
        with cols[3]:
            render_vertical_divider()


def render_part3_scoring(item, poid):
    teacher_id = st.session_state.teacher_id
    model_names = ["模型1", "模型2", "模型3"]
    model_map = st.session_state.model_shuffle_map[st.session_state.page]
    model_keys = [model_map[str(i)] for i in range(1, 4)]

    scores = st.session_state.all_scores[teacher_id].setdefault("part3_scores", {})

    type_labels_map = {
        "correct": [
            ("正确理解", "判断模型是否指出学生是回答是正确的，如“你说得对”“回答得很好”等。"),
            ("正确反馈", "判断模型是否引导学生进行下一步，或是总结正确答案。")
        ],
        "error": [
            ("正确理解", "判断模型是否正面指出学生的回答是错误的。"),
            ("正确反馈", "判断模型是否正确地改正了学生错误。")
        ],
        "question": [
            ("正确理解", "判断模型是否回答学生的问题。"),
            ("正确反馈", "判断模型是否正确回答学生提问。")
        ],
    }

    current_type = item.get("type", "correct")
    label_pairs = type_labels_map.get(current_type, type_labels_map["correct"])

    for score_type, (label, desc) in enumerate(label_pairs):
        score_key = f"part3_{poid}_{item['question_id']}_score{score_type}"

        # === 维度标题加编号 ===
        st.markdown(f"<div style='font-size: 18px; font-weight: bold;'>（{score_type + 1}） {label}</div>", unsafe_allow_html=True)

        # === 描述文字样式优化 ===
        st.markdown(f"<div style='font-size: 16px; padding-left: 1em;'>{desc}</div>", unsafe_allow_html=True)


        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # === 模型评分：三栏分隔 + 竖线 ===
        cols = st.columns([1, 0.05, 1, 0.05, 1])
        scores.setdefault(score_key, {})

        for i, (col, model_name) in enumerate(zip([cols[0], cols[2], cols[4]], model_names)):
            key = f"{score_key}_{model_name}"
            prev_value = scores[score_key].get(model_keys[i], 0)

            with col:
                subcol1, subcol2 = st.columns([1, 2])
                with subcol1:
                    st.markdown(
                        f"<div style='text-align: center; padding-top: 0.3rem; font-weight: bold;'>{model_name}</div>",
                        unsafe_allow_html=True
                    )
                with subcol2:
                    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
                    val = st.radio("", [0, 1],
                                   index=int(prev_value), horizontal=True, key=key)
                    st.markdown("</div>", unsafe_allow_html=True)

            scores[score_key][model_keys[i]] = val

        # === 插入分隔竖线 ===
        with cols[1]:
            render_vertical_divider()
        with cols[3]:
            render_vertical_divider()









# ========== 主程序入口 ==========
def main():
    # ========== 入口页：教师编号输入 ==========
    if "teacher_id" not in st.session_state:
        st.title("智能答疑教师评估系统")
        st.markdown("请输入您的教师编号（例如 T001）：")
        teacher_input = st.text_input("教师编号", "")
        if st.button("开始评估") and teacher_input.strip():
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

    # 初始化模型顺序混淆
    if "model_shuffle_map" not in st.session_state:
        st.session_state.model_shuffle_map = {}

    if idx not in st.session_state.model_shuffle_map:
        shuffled = ["A", "B", "C"]
        random.shuffle(shuffled)
        st.session_state.model_shuffle_map[idx] = dict(zip(["1", "2", "3"], shuffled))


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


    # ========== 导出按钮 ==========
    if st.button("导出所有评分结果"):
        teacher_scores = st.session_state.all_scores.get(teacher_id, {})
        all_scores = []

        # ==== Part1 ====
        for k, v in teacher_scores.get("part1_scores", {}).items():
            poid = k.replace("part1_", "")
            for dim, models in v.items():
                if dim not in ["语言流畅度", "是否指出知识点", "知识点内容是否正确",
               "最终答案正确", "过程正确", "是否分步讲解", "提问质量",
               "整体偏好排序（主观倾向）"]:
                    continue  # 跳过非当前使用字段（如旧字段）
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
        type_map = {
            "1": "引导质量（理解）",
            "2": "引导质量（不理解）",
            "3": "导正话题"
        }

        for k, v in teacher_scores.get("part2_scores", {}).items():
            part_match = re.match(r"part2_(.*?)_t(\d)_(\d+)", k)
            if part_match:
                poid_raw, tval, block_idx = part_match.groups()
                poid_clean = poid_raw.split("_")[0]  # 去掉 _idx 部分，保留 poid
                label = f"{type_map.get(tval, '未知类型')}_block{block_idx}"
                row = {
                    "poid": poid_clean,
                    "part": "part2",
                    "type": label,
                    "dimension": type_map.get(tval, "未知类型"),
                    "score_A": v.get("A", ""),
                    "score_B": v.get("B", ""),
                    "score_C": v.get("C", "")
                }
                all_scores.append(row)



        # ==== Part3 ====
        type_labels_map = {
            "correct": [
                "正确理解",
                "正确反馈"
            ],
            "error": [
                "正确理解",
                "正确反馈"
            ],
            "question": [
                "正确理解",
                "正确反馈"
            ]
        }

        for k, v in teacher_scores.get("part3_scores", {}).items():
            part_match = re.match(r"part3_(.*?)_(.*?)_score(\d)", k)
            if part_match:
                poid, qid, score_type = part_match.groups()
                score_idx = int(score_type)

                # 获取对话类型
                q_type = "correct"
                for sample in data:
                    if sample.get("poid") == poid:
                        for p3 in sample["content"].get("part3", []):
                            if p3.get("question_id") == qid:
                                q_type = p3.get("type", "correct")
                                break

                labels = type_labels_map.get(q_type, type_labels_map["correct"])
                dimension_name = labels[score_idx] if score_idx < len(labels) else f"评分项{score_idx}"

                row = {
                    "poid": poid,
                    "part": "part3",
                    "type": q_type,
                    "dimension": dimension_name,
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

    # 样式
    st.markdown("""
        <style>
            .model-box {
                background-color: #f7f7f7;
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 0.75rem 1rem;
                margin-bottom: 0.5rem;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <style>
            .block-container {
                padding-left: 2rem;
                padding-right: 2rem;
            }
        </style>
    """, unsafe_allow_html=True)

    main()
