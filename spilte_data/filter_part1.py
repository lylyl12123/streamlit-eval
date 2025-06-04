import streamlit as st
import json
from pathlib import Path
from collections import defaultdict
import base64

# ========== 配置文件路径 ==========
FILE_PATHS = {
    "DeepSeek-V3": "DeepSeek-V3_dialogs.jsonl",
    "o4-mini": "o4-mini_dialogs.jsonl",
    "Spark_X1": "Spark_X1_dialogs.jsonl"
}

@st.cache_data(show_spinner=False)
def load_dialogues():
    data = defaultdict(dict)
    for model_name, path in FILE_PATHS.items():
        if not Path(path).exists():
            continue
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    item = json.loads(line)
                    if item.get("dialogue_type") != 1:
                        continue
                    qid = item["id"]
                    data[qid][model_name] = item
                except json.JSONDecodeError:
                    continue
    return data

all_data = load_dialogues()
filtered_data = {qid: models for qid, models in all_data.items() if len(models) == 3}
question_ids = list(filtered_data.keys())

if len(question_ids) == 0:
    st.error("未能找到符合条件的对话数据。请检查 jsonl 文件是否存在，且包含 dialogue_type == 1 的记录，并确保三个模型都有相同的 question_id。")
    st.stop()

st.set_page_config(layout="wide")
st.title("🧠 Part1 数据筛选工具")
st.markdown("逐条检查模型对话，选择是否保留")

# ========== 分页控制 ==========
if "page" not in st.session_state:
    st.session_state.page = 0

qid = question_ids[st.session_state.page]
entry = filtered_data[qid]

# ========== 显示进度条 ==========
progress_text = f"已完成 {st.session_state.page + 1} / {len(question_ids)} 条"
st.markdown(f"**{progress_text}**")
st.progress((st.session_state.page + 1) / len(question_ids))

# ========== 显示内容 ==========
st.markdown(f"### 📌 题目 ID： `{qid}`")
st.markdown(f"**题目内容：**  \n{entry['DeepSeek-V3']['question']}")
st.markdown(f"**答案：**  \n{entry['DeepSeek-V3'].get('answer', '（无答案）')}")


cols = st.columns(3)
for i, model in enumerate(["DeepSeek-V3", "o4-mini", "Spark_X1"]):
    with cols[i]:
        st.markdown(f"#### 🤖 模型 {model}")
        for turn in entry[model]["messages"]:
            st.markdown(f"**学生：** {turn['user']}")
            st.markdown(f"**模型：** {turn['model_respond']}")
            st.markdown("---")

# ========== 勾选是否保留 ==========
if "selections" not in st.session_state:
    st.session_state.selections = {}

keep = st.checkbox("✅ 保留该组对话", key=qid, value=st.session_state.selections.get(qid, False))
st.session_state.selections[qid] = keep

# ========== 翻页按钮 ==========
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("⬅️ 上一条") and st.session_state.page > 0:
        st.session_state.page -= 1
        st.rerun()
with col2:
    if st.button("➡️ 下一条") and st.session_state.page < len(question_ids) - 1:
        st.session_state.page += 1
        st.rerun()


# ========== 已选条数显示 ==========
selected_count = sum(st.session_state.selections.get(qid, False) for qid in question_ids)
st.markdown(f"📊 已选择对话数：**{selected_count} / {len(question_ids)}**")


# ========== 导出按钮 ==========
st.markdown("---")
if st.button("📤 导出选中数据"):
    export = []
    for qid in question_ids:
        if st.session_state.selections.get(qid):
            models = filtered_data[qid]
            export.append({
                "question_id": qid,
                "question": models['DeepSeek-V3']['question'],
                "answer": models['DeepSeek-V3'].get('answer', ''),
                "DeepSeek-V3": models['DeepSeek-V3']['messages'],
                "o4-mini": models['o4-mini']['messages'],
                "Spark_X1": models['Spark_X1']['messages']
            })
    output_lines = [json.dumps(line, ensure_ascii=False) for line in export]
    output_str = "\n".join(output_lines)
    b64 = base64.b64encode(output_str.encode()).decode()
    href = f'<a href="data:application/jsonl;base64,{b64}" download="part1_filtered.jsonl">📥 下载筛选后 JSONL 文件</a>'
    st.markdown(href, unsafe_allow_html=True)