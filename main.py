import os
import json
from src.strategy_architect import generate_strategic_blueprint

def main():
    """
    Main function to test the Strategy Architect module.
    """
    print("--- Running Strategy Architect Test Script ---")

    # The API key is essential for the module to function.
    # We check for it here and provide clear instructions if it's missing.
    if not os.environ.get("GEMINI_API_KEY"):
        print("\n[ERROR] GEMINI_API_KEY environment variable is not set.")
        print("This script requires a Google Gemini API key to function.")
        print("\nPlease set the environment variable before running:")
        print("  export GEMINI_API_KEY='your_google_api_key_here'")
        print("\nScript finished without execution.")
        return

    # A sample problem description, as outlined in the plan.
    # This simulates the input that the main system would provide to the module.
    problem_state = (
        "我们正在开发一个大型语言模型驱动的自主研究代理。"
        "当前进展：代理可以分解问题、执行网络搜索并阅读文档。"
        "遇到的困境：当面对需要综合来自多个来源的矛盾信息才能得出结论的复杂问题时，"
        "代理的性能会急剧下降。它经常会陷入其中一个信源的观点，或者无法形成一个连贯的最终答案。"
    )

    print(f"\nProblem State:\n{problem_state}")
    print("\nAttempting to generate strategic blueprint...")

    # Call the core function from our implemented module.
    strategies = generate_strategic_blueprint(problem_state)

    # Process and display the output.
    if strategies:
        print("\n[SUCCESS] Successfully generated strategic blueprint:")
        # Pretty-print the JSON output for readability.
        print(json.dumps(strategies, indent=2, ensure_ascii=False))
    else:
        print("\n[FAILURE] Failed to generate strategic blueprint.")
        print("Please check the console for any error messages from the module.")

    print("\n--- Test Script Finished ---")

if __name__ == "__main__":
    main()
