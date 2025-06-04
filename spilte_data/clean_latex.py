import json
import os
import openai
from tqdm import tqdm

# ==== 配置 ====


client = openai.OpenAI(
    base_url="https://aihubmix.com/v1",
    api_key="sk-YQUM9TfwzbSs1Qfn08395e177a6547F6818f14Ba72DdCeBf"
)


def fix_latex_with_api(text: str) -> str:
    prompt = f"""
请将以下文本中所有非标准 LaTeX 数学表达式格式（如 \\(x\\)、(\\boxed{{0}})）转换为标准的 LaTeX 公式格式（$$...$$）。仅转换公式部分，保留原句其它内容不变。不要输出其他任何思考。

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
        print(completion.choices[0].message.content.strip())
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print("API 调用失败：", e)
        return text  # 保留原文

def process_file(filename: str):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    for sample in tqdm(data, desc="处理中"):
        content = sample.get("content", {})

        # part1 模型多轮对话
        for model in ["A", "B", "C"]:
            turns = content.get("part1", {}).get(model, [])
            for turn in turns:
                if "model_respond" in turn:
                    turn["model_respond"] = fix_latex_with_api(turn["model_respond"])

        # part2 多轮单轮结构嵌套
        for item in content.get("part2", []):
            for model in ["A", "B", "C"]:
                dialogue = item["content"][model].get("dialogue", [])
                for turn in dialogue:
                    if "model_respond" in turn:
                        turn["model_respond"] = fix_latex_with_api(turn["model_respond"])

        # part3 单轮结构
        for item in content.get("part3", []):
            for key in ["model_response_A", "model_response_B", "model_response_C"]:
                if key in item.get("single_dialog", {}):
                    item["single_dialog"][key] = fix_latex_with_api(item["single_dialog"][key])

    output_path = filename.replace(".json", "_fixed.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 修复完成，已保存为：{output_path}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="修复模型回复中的数学公式为标准 LaTeX 格式")
    parser.add_argument("--file", type=str, required=True, help="输入的 JSON 文件名，如 data_T001.json")
    args = parser.parse_args()

    process_file(args.file)
