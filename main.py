import logging
from config import DEBUG, LOG_LEVEL
from graph_config import graph

# 配置日志
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
if DEBUG:
    logger.setLevel(logging.DEBUG)


def main():
    logger.info("Starting LangGraph Agent...")
    print("=== LangGraph Agent ===")
    print("Type 'exit' or 'quit' to stop.")

    while True:
        try:
            user_input = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if user_input.strip().lower() in ("exit", "quit"):
            logger.info("Received exit command, shutting down.")
            break

        # 调用流程图进行处理
        result = graph.invoke({"input": user_input})
        response = result.get("response", "")

        print(f"Bot: {response}")
        logger.debug(f"Input: {user_input} | Response: {response}")

    print("Goodbye!")
    logger.info("Agent stopped.")


if __name__ == "__main__":
    main()
