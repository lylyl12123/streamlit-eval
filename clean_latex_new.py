import json
import openai
from tqdm import tqdm

# ==== 配置 ====
client = openai.OpenAI(
    base_url="https://aihubmix.com/v1",
    api_key="sk-YQUM9TfwzbSs1Qfn08395e177a6547F6818f14Ba72DdCeBf"
)

REAL_MODELS = ["DeepSeek-V3", "o4-mini", "Spark_X1"]

def fix_latex_with_api(text: str) -> str:
    prompt = f"""
        你是一个文本修复工具。你只允许修改数学公式的表示形式，其它任何字符、标点、换行都不允许修改。
        请将以下文本中所有非标准 LaTeX 数学表达式格式（如 \\(x\\)、(\\boxed{{0}})）转换为标准的 LaTeX 公式格式（$$...$$）。
        仅转换公式部分，**其它任何字符不得更改。**不要输出其他任何思考。

        示例：
        原始：本题答案为 (\\boxed{{0}})。
        转换：本题答案为 $$\\boxed{{0}}$$。

        原始内容如下：
        {text}
            """
    try:
        completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3-0324",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        print("---原文---：",text)
        print("---返回---：", completion.choices[0].message.content.strip())
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print("API 调用失败：", e)
        return text

def process_file(filename: str):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    for sample in tqdm(data, desc="清洗中"):
        content = sample.get("content", {})

        # === Part 2：清洗模型回复 ===
        for item in content.get("part2", []):
            for model in REAL_MODELS:
                dialogue = item.get("content", {}).get(model, {}).get("dialogue", [])
                for turn in dialogue:
                    if "model_respond" in turn:
                        turn["model_respond"] = fix_latex_with_api(turn["model_respond"])

        # === Part 3：只清洗 user 和 gt，不动模型回复 ===
        for item in content.get("part3", []):
            single = item.get("single_dialog", {})
            if "user" in single:
                single["user"] = fix_latex_with_api(single["user"])
            if "gt" in single:
                single["gt"] = fix_latex_with_api(single["gt"])

    output_path = filename.replace(".json", "_fixed.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 清洗完成，保存为：{output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="清洗 Part2 + Part3 的 Latex 格式")
    parser.add_argument("--file", type=str, required=True, help="输入 JSON 文件名，如 data_T001_generated.json")
    args = parser.parse_args()
    process_file(args.file)
