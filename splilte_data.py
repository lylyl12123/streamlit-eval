import json
import random
from collections import defaultdict
import os

# 加载数据
input_path = "D:/VScode/test/data_T000.json"
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 打乱顺序
random.shuffle(data)

# 配置
num_teachers = 6
annotations_per_sample = 3  # 每条样本分给3位老师
samples_per_teacher = 50

# 初始化
teacher_ids = [f"data_T00{i+1}" for i in range(num_teachers)]
teacher_assignments = defaultdict(list)
teacher_load = {tid: 0 for tid in teacher_ids}

# 分配数据
for sample in data:
    # 找负载最少的三个老师
    sorted_teachers = sorted(teacher_ids, key=lambda x: teacher_load[x])
    assigned_teachers = sorted_teachers[:annotations_per_sample]
    for tid in assigned_teachers:
        teacher_assignments[tid].append(sample)
        teacher_load[tid] += 1

# 导出文件
output_dir = "."
os.makedirs(output_dir, exist_ok=True)
for tid in teacher_ids:
    output_file = os.path.join(output_dir, f"{tid}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(teacher_assignments[tid], f, ensure_ascii=False, indent=2)

print("✅ 写入完成，每位老师分配50条样本。")


