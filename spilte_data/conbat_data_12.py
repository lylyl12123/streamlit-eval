import json
from pathlib import Path
from collections import defaultdict

# 路径
part1_path = "D:/VScode/test/spilte_data/part1_filtered_fin.jsonl"
part2_path = "D:/VScode/test/spilte_data/part2_constructed.jsonl"
part3_path = "D:/VScode/test/spilte_data/part3_filtered_fin.jsonl"  # ← 你筛选好的 part3 数据
output_path = "data_T001_generated.json"

REAL_MODELS = ["DeepSeek-V3", "o4-mini", "Spark_X1"]

# === 读取 Part1 数据 ===
part1_data = {}
with open(part1_path, "r", encoding="utf-8") as f:
    for line in f:
        entry = json.loads(line)
        qid = entry["question_id"]
        part1_data[qid] = {
            "question": entry["question"],
            "question_id": qid,
            "answer": entry.get("answer", ""),
            "DeepSeek-V3": entry.get("DeepSeek-V3", []),
            "o4-mini": entry.get("o4-mini", []),
            "Spark_X1": entry.get("Spark_X1", [])
        }

# === 读取 Part2 数据 ===
part2_grouped = defaultdict(list)
with open(part2_path, "r", encoding="utf-8") as f:
    for line in f:
        entry = json.loads(line)
        qid = entry["question_id"]
        part2_grouped[qid].append(entry)

# === 读取 Part3 数据 ===
part3_entries = []
with open(part3_path, "r", encoding="utf-8") as f:
    for line in f:
        part3_entries.append(json.loads(line))

# === 合并 Part1 + Part2 + Part3（按顺序） ===
combined = []
counter = 1
used_part3 = 0

for qid in part1_data:
    if qid in part2_grouped and len(part2_grouped[qid]) == 3:
        if used_part3 < len(part3_entries):
            part3_item = part3_entries[used_part3]
            used_part3 += 1
        else:
            print(f"警告：Part3 数据不足，已用完 {used_part3} 条。")
            break

        sample = {
            "poid": str(counter).zfill(3),
            "content": {
                "part1": part1_data[qid],
                "part2": part2_grouped[qid],
                "part3": [part3_item]  # 注意此处是 list 包裹
            }
        }
        combined.append(sample)
        counter += 1

print(f"✅ 共生成 {len(combined)} 条记录。")

# === 写入输出 ===
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(combined, f, ensure_ascii=False, indent=2)
