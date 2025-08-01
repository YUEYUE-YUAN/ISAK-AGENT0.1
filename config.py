import os
from dotenv import load_dotenv

# --------------------------------------------------
# 1. 加载 .env 文件中的环境变量
# --------------------------------------------------
load_dotenv()  # 会从项目根目录下的 .env 文件中读取变量

# --------------------------------------------------
# 2. OpenAI 相关配置
# --------------------------------------------------
# 必填：OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# 可选：自定义 API Base（多数场景无需修改）
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
# 默认模型
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")
# 最大 token 限制，记得在调用 API 时使用
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1000))
# 温度参数（0~1）
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))

# --------------------------------------------------
# 3. 调试与日志级别
# --------------------------------------------------
# DEBUG 模式开关，True/False
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
# 日志级别，可用值：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# --------------------------------------------------
# 4. 数据库配置（若不使用可留空或注释）
# --------------------------------------------------
# 格式示例：sqlite:///./data/agent_data.db 或 postgresql://user:pwd@host:port/db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/agent_data.db")

# --------------------------------------------------
# 5. 其他第三方 API 密钥
# --------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
# 如果后续再接入其他服务，也可在此添加：
# AZURE_API_KEY = os.getenv("AZURE_API_KEY")
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --------------------------------------------------
# 6. （可选）SQLAlchemy 数据库连接初始化
#    如果你需要持久化记忆或使用关系型数据库，
#    可以取消下面代码段的注释。
# --------------------------------------------------
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
#
# engine = create_engine(
#     DATABASE_URL,
#     connect_args={"check_same_thread": False}
#     if DATABASE_URL.startswith("sqlite") else {}
# )
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)