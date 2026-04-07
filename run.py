#!/usr/bin/env python3
"""运行入口 - 医疗器械招投标信息搜集工具."""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import main

if __name__ == "__main__":
    sys.exit(main())
