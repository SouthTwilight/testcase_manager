from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# 创建数据库实例
db = SQLAlchemy()
# 创建 CORS 实例
cors = CORS()

# 不导入任何蓝图或模型，避免循环导入
