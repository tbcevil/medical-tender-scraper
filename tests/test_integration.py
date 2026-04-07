"""集成测试 - 测试整个流程."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.config import TenderConfig
from src.fetchers.ccgp_fetcher import CCGPFetcher
from src.exporters.excel_exporter import ExcelExporter
from src.parser import TenderInfo


class TestIntegration:
    """集成测试类."""
    
    @patch("src.fetchers.ccgp_fetcher.HttpClient")
    def test_full_workflow_mocked(self, mock_http_client_class):
        """测试完整流程（模拟HTTP）."""
        # 模拟HTML响应
        mock_html = """
        <html>
        <body>
            <ul class="vT-srch-result-list">
                <li>
                    <a href="http://example.com/tender/1">眼科手术显微镜采购项目</a>
                    <span class="time">2024-01-15</span>
                    <span class="source">中国政府采购网</span>
                    <span class="region">北京市</span>
                    <span class="agency">北京中技招标公司</span>
                    <span class="code">ZB2024-001</span>
                    <p class="des">采购眼科手术显微镜设备一套</p>
                </li>
                <li>
                    <a href="http://example.com/tender/2">皮肤科激光治疗设备采购</a>
                    <span class="time">2024-01-14</span>
                    <span class="source">中国政府采购网</span>
                    <span class="region">上海市</span>
                    <span class="agency">上海国际招标公司</span>
                    <span class="code">ZB2024-002</span>
                    <p class="des">采购皮肤科激光治疗设备</p>
                </li>
            </ul>
        </body>
        </html>
        """
        
        mock_http_client = Mock()
        mock_http_client.get_text.return_value = mock_html
        mock_http_client_class.return_value = mock_http_client
        
        # 1. 创建配置
        config = TenderConfig(
            keywords=["眼科", "皮肤科"],
            days_back=30,
            max_results=50
        )
        
        # 2. 抓取数据
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_integration.xlsx"
            
            with CCGPFetcher(config) as fetcher:
                tenders = fetcher.get_all_tenders(max_pages_per_keyword=1)
            
            # 3. 验证抓取结果
            assert len(tenders) == 2
            assert tenders[0].title == "眼科手术显微镜采购项目"
            assert tenders[1].title == "皮肤科激光治疗设备采购"
            
            # 4. 导出数据
            exporter = ExcelExporter(str(output_path))
            result_path = exporter.export(tenders, include_summary=True)
            
            # 5. 验证导出结果
            assert Path(result_path).exists()
            assert Path(result_path).stat().st_size > 0
    
    @patch("src.fetchers.ccgp_fetcher.HttpClient")
    def test_multi_keyword_workflow(self, mock_http_client_class):
        """测试多关键词流程."""
        # 为不同关键词返回不同结果
        def mock_get_text(url, **kwargs):
            if "眼科" in url:
                return """
                <html><body>
                    <ul class="vT-srch-result-list">
                        <li>
                            <a href="http://example.com/eye/1">眼科设备1</a>
                            <span class="time">2024-01-15</span>
                            <span class="source">中国政府采购网</span>
                        </li>
                    </ul>
                </body></html>
                """
            else:
                return """
                <html><body>
                    <ul class="vT-srch-result-list">
                        <li>
                            <a href="http://example.com/skin/1">皮肤科设备1</a>
                            <span class="time">2024-01-14</span>
                            <span class="source">中国政府采购网</span>
                        </li>
                    </ul>
                </body></html>
                """
        
        mock_http_client = Mock()
        mock_http_client.get_text = mock_get_text
        mock_http_client_class.return_value = mock_http_client
        
        config = TenderConfig(
            keywords=["眼科", "皮肤科"],
            days_back=30
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "multi_keyword.xlsx"
            
            with CCGPFetcher(config) as fetcher:
                results = fetcher.search_all_keywords(max_pages_per_keyword=1)
            
            # 验证每个关键词都有结果
            assert "眼科" in results
            assert "皮肤科" in results
            assert len(results["眼科"]) == 1
            assert len(results["皮肤科"]) == 1
            
            # 多工作表导出
            exporter = ExcelExporter(str(output_path))
            result_path = exporter.export_multiple_sheets(results)
            
            assert Path(result_path).exists()
    
    @patch("src.fetchers.ccgp_fetcher.HttpClient")
    def test_empty_result_handling(self, mock_http_client_class):
        """测试空结果处理."""
        mock_http_client = Mock()
        mock_http_client.get_text.return_value = "<html><body></body></html>"
        mock_http_client_class.return_value = mock_http_client
        
        config = TenderConfig(keywords=["不存在的关键词"])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty.xlsx"
            
            with CCGPFetcher(config) as fetcher:
                tenders = fetcher.get_all_tenders(max_pages_per_keyword=1)
            
            assert len(tenders) == 0
            
            # 空列表导出
            exporter = ExcelExporter(str(output_path))
            result_path = exporter.export(tenders)
            
            # 空列表也应该能导出（只有表头）
            assert Path(result_path).exists()
    
    @patch("src.fetchers.ccgp_fetcher.HttpClient")
    def test_deduplication_in_workflow(self, mock_http_client_class):
        """测试工作流程中的去重."""
        # 两个关键词返回相同的结果
        mock_html = """
        <html><body>
            <ul class="vT-srch-result-list">
                <li>
                    <a href="http://example.com/same">相同项目</a>
                    <span class="time">2024-01-15</span>
                    <span class="source">中国政府采购网</span>
                </li>
            </ul>
        </body></html>
        """
        
        mock_http_client = Mock()
        mock_http_client.get_text.return_value = mock_html
        mock_http_client_class.return_value = mock_http_client
        
        config = TenderConfig(keywords=["眼科", "皮肤科"])
        
        with CCGPFetcher(config) as fetcher:
            tenders = fetcher.get_all_tenders(max_pages_per_keyword=1)
        
        # 应该去重，只保留一个
        assert len(tenders) == 1
        assert tenders[0].title == "相同项目"
    
    @patch("src.fetchers.ccgp_fetcher.HttpClient")
    def test_date_filtering_in_workflow(self, mock_http_client_class):
        """测试工作流程中的日期过滤."""
        mock_html = """
        <html><body>
            <ul class="vT-srch-result-list">
                <li>
                    <a href="http://example.com/1">近期项目</a>
                    <span class="time">2024-01-15</span>
                    <span class="source">中国政府采购网</span>
                </li>
                <li>
                    <a href="http://example.com/2">早期项目</a>
                    <span class="time">2023-12-01</span>
                    <span class="source">中国政府采购网</span>
                </li>
            </ul>
        </body></html>
        """
        
        mock_http_client = Mock()
        mock_http_client.get_text.return_value = mock_html
        mock_http_client_class.return_value = mock_http_client
        
        # 只搜索最近7天
        config = TenderConfig(
            keywords=["测试"],
            days_back=7
        )
        
        with CCGPFetcher(config) as fetcher:
            # 设置日期范围为2024-01-01到2024-01-31
            tenders = fetcher.search(
                keyword="测试",
                start_time="2024:01:01",
                end_time="2024:01:31",
                max_pages=1
            )
        
        # 应该只保留日期范围内的项目
        assert len(tenders) == 1
        assert tenders[0].title == "近期项目"
