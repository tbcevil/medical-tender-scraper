"""实际抓取测试 - 需要网络连接.

这些测试会实际访问中国政府采购网，默认跳过。
运行前请确保网络连接正常。

使用方法:
    pytest tests/test_live_fetch.py -v --run-live
    
或者在环境变量中设置:
    RUN_LIVE_TESTS=1 pytest tests/test_live_fetch.py -v
"""

import os
import pytest
import tempfile
from pathlib import Path

# 检查是否应该运行实时测试
RUN_LIVE_TESTS = os.environ.get("RUN_LIVE_TESTS", "0") == "1" or pytest.config.getoption("--run-live", False) if hasattr(pytest, "config") else False

pytestmark = pytest.mark.skipif(
    not RUN_LIVE_TESTS,
    reason="需要 --run-live 参数或 RUN_LIVE_TESTS=1 环境变量"
)

from src.config import TenderConfig
from src.fetchers.ccgp_fetcher import CCGPFetcher
from src.exporters.excel_exporter import ExcelExporter
from src.http_client import HttpClient


def test_http_client_live():
    """测试HTTP客户端实际请求."""
    with HttpClient(timeout=30) as client:
        # 测试访问中国政府采购网
        html = client.get_text("http://www.ccgp.gov.cn")
        
        assert html is not None
        assert len(html) > 0
        assert "政府采购" in html or "ccgp" in html.lower()


def test_search_page_live():
    """测试搜索页面实际访问."""
    config = TenderConfig(
        keywords=["医疗设备"],
        days_back=7,
        max_results=10
    )
    
    with CCGPFetcher(config) as fetcher:
        # 构建搜索URL
        url = fetcher.build_search_url(
            keyword="医疗设备",
            page=1
        )
        
        print(f"搜索URL: {url}")
        
        # 实际请求
        html = fetcher.http_client.get_text(url)
        
        assert html is not None
        assert len(html) > 0
        print(f"页面大小: {len(html)} 字节")


def test_fetch_single_keyword_live():
    """测试实际抓取单个关键词."""
    config = TenderConfig(
        keywords=["眼科"],
        days_back=7,
        max_results=20
    )
    
    with CCGPFetcher(config) as fetcher:
        tenders = fetcher.search(
            keyword="眼科",
            max_pages=1  # 只抓取第一页
        )
        
        print(f"抓取到 {len(tenders)} 条招标信息")
        
        if tenders:
            for i, tender in enumerate(tenders[:3], 1):
                print(f"{i}. {tender.title} ({tender.publish_date})")
            
            assert tenders[0].title is not None
            assert tenders[0].url is not None


def test_fetch_multiple_keywords_live():
    """测试实际抓取多个关键词."""
    config = TenderConfig(
        keywords=["眼科", "皮肤科"],
        days_back=7,
        max_results=10
    )
    
    with CCGPFetcher(config) as fetcher:
        results = fetcher.search_all_keywords(max_pages_per_keyword=1)
        
        total = sum(len(tenders) for tenders in results.values())
        print(f"总共抓取到 {total} 条招标信息")
        
        for keyword, tenders in results.items():
            print(f"关键词 '{keyword}': {len(tenders)} 条")
            if tenders:
                print(f"  示例: {tenders[0].title}")


def test_full_workflow_live():
    """测试完整工作流程（实际抓取并导出）."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "live_test.xlsx"
        
        config = TenderConfig(
            keywords=["眼科"],
            days_back=7,
            max_results=10,
            output_file=str(output_path)
        )
        
        print(f"开始抓取...")
        
        with CCGPFetcher(config) as fetcher:
            tenders = fetcher.get_all_tenders(max_pages_per_keyword=1)
        
        print(f"抓取完成，共 {len(tenders)} 条记录")
        
        if tenders:
            # 导出
            exporter = ExcelExporter(str(output_path))
            result_path = exporter.export(tenders, include_summary=True)
            
            print(f"导出完成: {result_path}")
            
            # 验证文件
            assert Path(result_path).exists()
            file_size = Path(result_path).stat().st_size
            print(f"文件大小: {file_size} 字节")
            assert file_size > 0
        else:
            print("未抓取到数据，跳过导出")
            pytest.skip("未抓取到数据")


def test_website_structure():
    """测试网站结构是否变化."""
    config = TenderConfig()
    
    with CCGPFetcher(config) as fetcher:
        url = fetcher.build_search_url("医疗设备", page=1)
        html = fetcher.http_client.get_text(url)
        
        # 检查关键元素是否存在
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        
        # 检查搜索结果列表
        result_list = soup.find("ul", class_="vT-srch-result-list")
        
        if result_list:
            print("找到搜索结果列表 (vT-srch-result-list)")
            items = result_list.find_all("li")
            print(f"列表中有 {len(items)} 个条目")
        else:
            # 尝试其他可能的选择器
            alt_selectors = [
                ("ul", {"class": lambda x: x and "result" in x.lower()}),
                ("div", {"class": lambda x: x and "list" in x.lower()}),
                ("table", {"class": lambda x: x and "result" in x.lower()}),
            ]
            
            for tag, attrs in alt_selectors:
                elements = soup.find_all(tag, attrs)
                if elements:
                    print(f"找到备选元素: {tag} {attrs}")
                    break
            else:
                print("警告: 未找到预期的搜索结果列表结构")
                print("页面可能需要更新解析器")
                
        # 检查是否有结果
        no_result = soup.find(text=lambda t: t and ("暂无" in t or "没有" in t or "no result" in t.lower()))
        if no_result:
            print("页面显示无搜索结果")
        else:
            print("页面可能有搜索结果")


# pytest钩子，添加命令行选项
def pytest_addoption(parser):
    """添加命令行选项."""
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="运行实际网络请求测试"
    )
