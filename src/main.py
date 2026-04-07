"""主程序模块 - 整合所有功能."""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from config import TenderConfig


def setup_argument_parser() -> argparse.ArgumentParser:
    """设置命令行参数解析器."""
    parser = argparse.ArgumentParser(
        description="医疗器械招投标信息搜集工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py                    # 使用默认配置运行
  python run.py -k 眼科 皮肤科      # 指定关键词
  python run.py -d 14              # 搜索最近14天
  python run.py -o output.xlsx     # 指定输出文件
  python run.py --multi-sheet      # 多工作表导出
  python run.py -v                 # 详细输出
        """
    )
    
    parser.add_argument(
        "-k", "--keywords",
        nargs="+",
        default=["眼科"],
        help="搜索关键词列表 (默认: 眼科)"
    )
    
    parser.add_argument(
        "-d", "--days",
        type=int,
        default=7,
        help="搜索最近多少天的招标信息 (默认: 7)"
    )
    
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="输出Excel文件名 (默认: 自动生成带日期的文件名)"
    )
    
    parser.add_argument(
        "--multi-sheet",
        action="store_true",
        help="使用多工作表格式导出"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细输出"
    )
    
    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="每个关键词最大结果数 (默认: 100)"
    )
    
    return parser


def main():
    """主函数."""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # 自动生成带日期的文件名
    if args.output is None:
        today = datetime.now().strftime("%Y%m%d")
        args.output = f"medical_tenders_{today}.xlsx"
    
    # 创建配置
    config = TenderConfig(
        keywords=args.keywords,
        days_back=args.days,
        output_file=args.output,
        max_results=args.max_results
    )
    
    if args.verbose:
        print("=" * 60)
        print("医疗器械招投标信息搜集工具")
        print("=" * 60)
        print(f"\n配置信息:")
        print(f"  关键词: {', '.join(config.keywords)}")
        print(f"  时间范围: 最近 {config.days_back} 天")
        print(f"  输出文件: {config.output_file}")
        print(f"  最大结果数: {config.max_results}")
        print()
    
    # 延迟导入，避免循环导入
    from fetchers.ccgp_fetcher import CCGPFetcher
    from exporters.excel_exporter import ExcelExporter
    
    # 创建抓取器
    fetcher = CCGPFetcher(config)
    
    try:
        # 搜索所有关键词
        results = fetcher.search_all_keywords()
        
        # 统计结果
        total = sum(len(tenders) for tenders in results.values())
        
        if total == 0:
            print("\n未找到任何招标信息")
            return 0
        
        print(f"\n搜索完成！共找到 {total} 条招标信息")
        
        # 导出到Excel
        exporter = ExcelExporter(config.output_file)
        
        if args.multi_sheet:
            exporter.export_multi_sheet(results)
        else:
            exporter.export(results)
        
        print("\n全部完成！")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        return 130
    except Exception as e:
        print(f"\n错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        fetcher.close()


if __name__ == "__main__":
    sys.exit(main())
