#!/usr/bin/env python3
"""全国公共资源交易平台招标信息采集脚本.

使用Playwright进行浏览器自动化抓取。

安装依赖:
    pip install playwright
    playwright install chromium

使用方法:
    python scripts/run_ggzy.py -k 眼科
    python scripts/run_ggzy.py -k 眼科 激光 -d 7 --max-results 50
    python scripts/run_ggzy.py -k 眼科 --all
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
from datetime import datetime

from config import TenderConfig


def setup_argument_parser() -> argparse.ArgumentParser:
    """设置命令行参数解析器."""
    parser = argparse.ArgumentParser(
        description="全国公共资源交易平台招标信息采集工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 基本使用（默认搜索"眼科"）
    python scripts/run_ggzy.py

    # 指定关键词
    python scripts/run_ggzy.py -k 眼科

    # 指定多个关键词
    python scripts/run_ggzy.py -k 眼科 激光 显微镜

    # 指定最大结果数
    python scripts/run_ggzy.py --max-results 50

    # 获取所有结果
    python scripts/run_ggzy.py --all

    # 显示浏览器窗口（非无头模式）
    python scripts/run_ggzy.py --show-browser
        """
    )
    
    parser.add_argument(
        "-k", "--keywords",
        nargs="+",
        default=["眼科"],
        help="搜索关键词列表 (默认: 眼科)"
    )
    
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="输出Excel文件名 (默认: 自动生成带日期的文件名)"
    )
    
    parser.add_argument(
        "--max-results",
        type=int,
        default=20,
        help="每个关键词最大结果数，0表示获取所有 (默认: 20)"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="获取所有结果（相当于 --max-results 0）"
    )
    
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="显示浏览器窗口（非无头模式，用于调试）"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细输出"
    )
    
    return parser


def main():
    """主函数."""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # 检查Playwright是否安装
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("错误: Playwright未安装")
        print("请运行以下命令安装:")
        print("  pip install playwright")
        print("  playwright install chromium")
        sys.exit(1)
    
    # 自动生成带日期的文件名
    if args.output is None:
        today = datetime.now().strftime("%Y%m%d")
        args.output = f"ggzy_tenders_{today}.xlsx"
    
    # 如果指定了--all，设置max_results为0
    if args.all:
        args.max_results = 0
    
    # 创建配置
    config = TenderConfig(
        keywords=args.keywords,
        output_file=args.output,
        max_results=args.max_results
    )
    
    if args.verbose:
        print("=" * 60)
        print("全国公共资源交易平台招标信息采集工具")
        print("=" * 60)
        print(f"\n配置信息:")
        print(f"  关键词: {', '.join(config.keywords)}")
        print(f"  输出文件: {config.output_file}")
        if config.max_results == 0:
            print(f"  最大结果数: 全部")
        else:
            print(f"  最大结果数: {config.max_results}")
        print(f"  浏览器模式: {'显示窗口' if args.show_browser else '无头模式'}")
        print()
    
    # 导入Playwright版本的fetcher
    from fetchers.ggzy_fetcher_playwright import GGZYFetcherPlaywright
    from exporters.excel_exporter import ExcelExporter
    
    # 创建抓取器
    fetcher = GGZYFetcherPlaywright(config, headless=not args.show_browser)
    
    try:
        # 搜索所有关键词
        results = fetcher.search_all_keywords()
        
        # 统计结果
        total_count = sum(len(tenders) for tenders in results.values())
        
        if args.verbose:
            print(f"\n{'=' * 60}")
            print(f"搜索完成，共找到 {total_count} 条招标信息")
            print(f"{'=' * 60}\n")
        
        if total_count == 0:
            print("未找到任何招标信息")
            return
        
        # 导出到Excel
        exporter = ExcelExporter()
        output_path = exporter.export(results, config.output_file)
        
        print(f"\n结果已保存到: {output_path}")
        print(f"共 {total_count} 条记录")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        fetcher.close()


if __name__ == "__main__":
    main()
