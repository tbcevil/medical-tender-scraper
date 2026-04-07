#!/usr/bin/env python3
"""运行入口 - 医疗器械招投标信息搜集工具.

使用方法:
    python scripts/run.py                    # 默认运行
    python scripts/run.py -k 眼科            # 指定关键词
    python scripts/run.py -d 14              # 指定时间范围
    python scripts/run.py --max-results 50   # 指定最大结果数
    python scripts/run.py --multi-sheet      # 多工作表导出
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import main

if __name__ == "__main__":
    sys.exit(main())
