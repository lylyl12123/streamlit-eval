import json

# 读取原始合并文件（含已清洗过的 LaTeX）
fixed_file_path = "D:\VScode\\test\data_T001_generated_fixed.json"
with open(fixed_file_path, "r", encoding="utf-8") as f:
    fixed_data = json.load(f)

# 读取新的去重后的 Part2 数据
part2_new_path = "D:\VScode\\test\spilte_data\part2_constructed.jsonl"
with open(part2_new_path, "r", encoding="utf-8") as f:
    new_part2_blocks = [json.loads(line) for line in f]

# 重新组织新的 Part2 数据：按 question_id 分组
from collections import defaultdict

part2_grouped_new = defaultdict(list)
for block in new_part2_blocks:
    part2_grouped_new[block["question_id"]].append(block)

# 替换 fixed_data 中的 part2 内容
updated_count = 0
for sample in fixed_data:
    qid = sample.get("content", {}).get("part1", {}).get("question_id", "")
    if qid in part2_grouped_new:
        sample["content"]["part2"] = part2_grouped_new[qid]
        updated_count += 1

# 输出新文件
output_path = "data_T001_merged_with_dedup_part2.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(fixed_data, f, ensure_ascii=False, indent=2)

output_path, updated_count
