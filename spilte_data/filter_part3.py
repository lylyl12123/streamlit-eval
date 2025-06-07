from pathlib import Path
import json
import streamlit as st
import base64

# ========== 配置文件路径 ==========
MODEL_FILES = {
    "DeepSeek-V3": "DeepSeek-V3_single_dialogs.json",
    "o4-mini": "o4-mini_single_dialogs.json",
    "Spark_X1": "Spark_X1_single_dialogs.json"
}
QUESTION_FILE = "math_single_dialogs.json"

# ========== 加载题目、GT、上一轮模型回复 ==========
@st.cache_data(show_spinner=False)
def load_and_merge_data():
    question_map = {}
    gt_map = {}
    last_model_reply_map = {}

    if Path(QUESTION_FILE).exists():
        with open(QUESTION_FILE, "r", encoding="utf-8") as f:
            for item in json.load(f):
                qid = item["dialog_id"]
                question_map[qid] = item["messages"][0]["content"]
                gt_map[qid] = item.get("GT", "")
                last_model = ""
                for msg in reversed(item["messages"][:-1]):
                    if msg["role"] == "assistant":
                        last_model = msg["content"]
                        break
                last_model_reply_map[qid] = last_model

    merged = {}
    for model_name, path in MODEL_FILES.items():
        if not Path(path).exists():
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                qid = item["dialog_id"]
                if qid not in merged:
                    merged[qid] = {
                        "question_id": qid,
                        "type": item["type"],
                        "question": question_map.get(qid, "（未找到题干）"),
                        "last_model_reply": last_model_reply_map.get(qid, ""),
                        "single_dialog": {
                            "user": item["single_dialog"]["user"],
                            "gt": gt_map.get(qid, "")
                        }
                    }
                merged[qid]["single_dialog"][model_name] = item["single_dialog"]["model_response"]

    return {
        k: v for k, v in merged.items()
        if all(m in v["single_dialog"] for m in MODEL_FILES)
    }

# ========== 主程序 ==========
st.set_page_config(layout="wide")
st.title("🎯 Part3 单轮反馈筛选工具（含上一轮模型回复与GT）")

all_data = load_and_merge_data()
question_ids = list(all_data.keys())

if "page" not in st.session_state:
    st.session_state.page = 0
if "selections" not in st.session_state:
    st.session_state.selections = {}

if not question_ids:
    st.error("❌ 没有找到符合条件的数据，请检查原始文件是否存在或格式正确。")
    st.stop()

qid = question_ids[st.session_state.page]
entry = all_data[qid]

# ========== 显示内容 ==========
st.markdown(f"### 🆔 题目 ID： `{qid}`")
st.markdown(f"**类型：** {entry['type']}")
st.markdown(f"**题目内容：**  \n{entry.get('question', '（无题干）')}")

if entry.get("last_model_reply"):
    st.markdown("**上一轮提问：**")
    st.markdown(entry["last_model_reply"])

st.markdown(f"**学生回复：**  \n{entry['single_dialog']['user']}")

cols = st.columns(3)
for i, model in enumerate(["DeepSeek-V3", "o4-mini", "Spark_X1"]):
    with cols[i]:
        st.markdown(f"#### 🤖 模型 {model} 回复")
        st.markdown(entry["single_dialog"][model])

st.markdown("#### 🧑‍🏫 学生本应有的正确回复（gt）")
st.markdown(entry["single_dialog"].get("gt", "（无参考回复）"))

# ========== 勾选是否保留 ==========
keep = st.checkbox("✅ 保留该组数据", key=qid, value=st.session_state.selections.get(qid, False))
st.session_state.selections[qid] = keep

# ========== 翻页 ==========
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("⬅️ 上一条") and st.session_state.page > 0:
        st.session_state.page -= 1
        st.rerun()
with col2:
    if st.button("➡️ 下一条") and st.session_state.page < len(question_ids) - 1:
        st.session_state.page += 1
        st.rerun()

# ========== 进度显示 ==========
selected_count = sum(st.session_state.selections.get(qid, False) for qid in question_ids)
st.markdown(f"📊 当前进度：**{st.session_state.page + 1} / {len(question_ids)}**，已选：**{selected_count} 条**")

# ========== 导出 ==========
st.markdown("---")
if st.button("📤 导出筛选结果"):
    export = []
    for qid in question_ids:
        if st.session_state.selections.get(qid):
            export.append(all_data[qid])
    output_str = "\n".join([json.dumps(line, ensure_ascii=False) for line in export])
    b64 = base64.b64encode(output_str.encode()).decode()
    href = f'<a href="data:application/jsonl;base64,{b64}" download="part3_filtered.jsonl">📥 点击下载 JSONL</a>'
    st.markdown(href, unsafe_allow_html=True)
