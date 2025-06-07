from pathlib import Path
import json
import random
from collections import defaultdict

# ========== 输入路径 ==========
part1_path = "D:\VScode\\test\spilte_data\part1_filtered_fin.jsonl"
model_files = {
    "DeepSeek-V3": "D:\VScode\\test\spilte_data\DeepSeek-V3_dialogs.jsonl",
    "o4-mini": "D:\VScode\\test\spilte_data\o4-mini_dialogs.jsonl",
    "Spark_X1": "D:\VScode\\test\spilte_data\Spark_X1_dialogs.jsonl"
}
output_path = "part2_constructed.jsonl"

# ===== 读取候选 qid 列表 =====
with open(part1_path, "r", encoding="utf-8") as f:
    candidate_qids = [json.loads(line)["question_id"] for line in f]
candidate_qids_set = set(candidate_qids)

# ===== 加载模型数据 =====
model_entries = defaultdict(list)  # model -> List[entry]
for model_name, path in model_files.items():
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if "id" in entry and "template_index" in entry and "messages" in entry:
                    model_entries[model_name].append(entry)
            except:
                continue

# ===== 对话签名（用于去重）=====
used_signatures = set()
def dialogue_signature(dialogue):
    return "\n".join([f"{list(d.keys())[0]}:{list(d.values())[0]}" for d in dialogue])

# ===== 提取指定类型的对话片段 =====
def extract_dialogue_by_type(entry, t_type):
    messages = entry["messages"]
    template_index = entry["template_index"]

    for idx, t in enumerate(template_index):
        if t == t_type:
            msg_idx = idx + 1
            if 0 < msg_idx < len(messages):
                prev_model = messages[msg_idx - 1].get("model_respond", "")
                user = messages[msg_idx].get("user", "")
                model_resp = messages[msg_idx].get("model_respond", "")
                dialogue = [
                    {"model_respond": prev_model},
                    {"user": user},
                    {"model_respond": model_resp}
                ]
                sig = dialogue_signature(dialogue)
                if sig not in used_signatures:
                    used_signatures.add(sig)
                    return {
                        "question": entry["question"],
                        "dialogue": dialogue
                    }
    return None

# ===== 构建 Part2 =====
final_blocks = []
for qid in candidate_qids:
    type_blocks = []
    all_types_present = True

    for t in [1, 2, 3]:
        content = {}
        success = True

        for model_name in ["DeepSeek-V3", "o4-mini", "Spark_X1"]:
            found = False

            # ===== 1）本题中查找 =====
            for entry in model_entries[model_name]:
                if entry["id"] == qid:
                    result = extract_dialogue_by_type(entry, t)
                    if result:
                        content[model_name] = result
                        found = True
                        break

            # ===== 2）fallback：其它 part1 中题目 =====
            if not found:
                fallback_pool = [
                    e for e in model_entries[model_name]
                    if e["id"] in candidate_qids_set and e["id"] != qid
                ]
                random.shuffle(fallback_pool)
                for entry in fallback_pool:
                    result = extract_dialogue_by_type(entry, t)
                    if result:
                        content[model_name] = result
                        found = True
                        break

            # ===== 3）fallback 放宽：允许任意题目 =====
            if not found:
                fallback_pool = [e for e in model_entries[model_name] if e["id"] != qid]
                random.shuffle(fallback_pool)
                for entry in fallback_pool:
                    result = extract_dialogue_by_type(entry, t)
                    if result:
                        content[model_name] = result
                        found = True
                        break

            if not found:
                success = False
                break

        if success:
            type_blocks.append({
                "question_id": qid,
                "type": t,
                "content": content
            })
        else:
            all_types_present = False
            break

    if all_types_present:
        final_blocks.extend(type_blocks)
        if len(final_blocks) >= 300:
            break

# ===== 保存结果 =====
with open(output_path, "w", encoding="utf-8") as f:
    for block in final_blocks:
        f.write(json.dumps(block, ensure_ascii=False) + "\n")

print(f"✅ Part2 构造完成，共 {len(final_blocks)} 条，来自 {len(final_blocks)//3} 道题")