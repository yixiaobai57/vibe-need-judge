"""CLI 入口：python main.py "<想法/PRD/URL>"

示例：
  python main.py "AI 给程序员写诗鼓励他们"
  python main.py "中小商家简易进销存小程序"

未配置 OPENAI_API_KEY 时自动走 Mock 模式，可离线跑通演示。
"""
import asyncio, sys, json
from src import graph, config


def main():
    user_input = " ".join(sys.argv[1:]) or "一个AI写诗鼓励程序员的应用"
    use_graph = len(sys.argv) > 2 and sys.argv[1] == "--graph"

    if use_graph:
        # 清理 --graph 参数，取剩余文本
        user_input = " ".join(sys.argv[2:]) or user_input

    if use_graph:
        app = graph.build_graph()
        result = app.invoke({"user_input": user_input})
    else:
        result = asyncio.run(graph.run_serial(user_input))

    print("\n" + "=" * 56)
    print(f"输入：{user_input}")
    print(f"阶段：{result.get('stage')}（可信度 {result.get('trust')}）")
    print(f"专家举证：{len(result.get('expert_statements', []))} 条")
    print(f"消费群体：{len(result.get('jury_statements', []))} 个")
    print(f"分歧点：{result.get('key_divergence', '')[:80]}")
    print(f"加权得分：{result.get('weighted_score')}　裁决：{result.get('verdict')}（置信度 {result.get('confidence')}）")
    print("=" * 56)
    if config.is_mock():
        print("[提示] 当前为 Mock 模式。设置 OPENAI_API_KEY 后可获得真实模型推理。")
    # 导出完整结果供查看
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("完整结果已写入 result.json")


if __name__ == "__main__":
    main()
