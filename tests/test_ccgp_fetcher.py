"""中国政府采购网抓取器测试."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.config import TenderConfig
from src.fetchers.ccgp_fetcher import CCGPFetcher
from src.parser import TenderInfo


class TestCCGPFetcher:
    """CCGPFetcher测试类."""
    
    def test_init_default_config(self):
        """测试默认配置初始化."""
        fetcher = CCGPFetcher()
        
        assert isinstance(fetcher.config, TenderConfig)
        assert fetcher.config.base_url == "http://www.ccgp.gov.cn"
    
    def test_init_custom_config(self):
        """测试自定义配置初始化."""
        config = TenderConfig(keywords=["测试"], timeout=60)
        fetcher = CCGPFetcher(config)
        
        assert fetcher.config.keywords == ["测试"]
        assert fetcher.config.timeout == 60
    
    def test_build_search_url(self):
        """测试构建搜索URL."""
        fetcher = CCGPFetcher()
        
        url = fetcher.build_search_url(
            keyword="眼科",
            page=1,
            start_time="2024:01:01",
            end_time="2024:01:31"
        )
        
        assert "search.ccgp.gov.cn/bxsearch" in url
        assert "kw=%E7%9C%BC%E7%A7%91" in url  # URL编码后的"眼科"
        assert "page_index=1" in url
        assert "startTime=2024%3A01%3A01" in url
        assert "endTime=2024%3A01%3A31" in url
    
    def test_build_search_url_default_dates(self):
        """测试使用默认日期构建URL."""
        config = TenderConfig(days_back=7)
        fetcher = CCGPFetcher(config)
        
        url = fetcher.build_search_url(keyword="测试")
        
        assert "search.ccgp.gov.cn/bxsearch" in url
        assert "kw=%E6%B5%8B%E8%AF%95" in url
        assert "startTime=" in url
        assert "endTime=" in url
    
    @patch("src.fetchers.ccgp_fetcher.HttpClient")
    def test_search_success(self, mock_http_client_class):
        """测试搜索成功."""
        # 模拟HTTP响应
        mock_response_html = """
        <html>
        <body>
            <ul class="vT-srch-result-list">
                <li>
                    <a href="http://example.com/1">眼科设备采购</a>
                    <span class="time">2024-01-15</span>
                    <span class="source">中国政府采购网</span>
                </li>
            </ul>
        </body>
        </html>
        """
        
        mock_http_client = Mock()
        mock_http_client.get_text.return_value = mock_response_html
        mock_http_client_class.return_value = mock_http_client
        
        config = TenderConfig(max_results=10)
        fetcher = CCGPFetcher(config)
        
        tenders = fetcher.search(
            keyword="眼科",
            start_time="2024:01:01",
            end_time="2024:01:31",
            max_pages=1
        )
        
        assert len(tenders) == 1
        assert tenders[0].title == "眼科设备采购"
        assert tenders[0].keyword == "眼科"
    
    @patch("src.fetchers.ccgp_fetcher.HttpClient")
    def test_search_empty_result(self, mock_http_client_class):
        """测试空结果."""
        mock_http_client = Mock()
        mock_http_client.get_text.return_value = "<html><body></body></html>"
        mock_http_client_class.return_value = mock_http_client
        
        fetcher = CCGPFetcher()
        
        tenders = fetcher.search(keyword="不存在的关键词12345", max_pages=1)
        
        assert tenders == []
    
    @patch("src.fetchers.ccgp_fetcher.HttpClient")
    def test_search_request_error(self, mock_http_client_class):
        """测试请求错误处理."""
        mock_http_client = Mock()
        mock_http_client.get_text.side_effect = Exception("网络错误")
        mock_http_client_class.return_value = mock_http_client
        
        fetcher = CCGPFetcher()
        
        tenders = fetcher.search(keyword="测试", max_pages=1)
        
        assert tenders == []
    
    @patch("src.fetchers.ccgp_fetcher.HttpClient")
    def test_search_all_keywords(self, mock_http_client_class):
        """测试搜索所有关键词."""
        mock_response_html = """
        <html>
        <body>
            <ul class="vT-srch-result-list">
                <li>
                    <a href="http://example.com/1">测试项目</a>
                    <span class="time">2024-01-15</span>
                    <span class="source">中国政府采购网</span>
                </li>
            </ul>
        </body>
        </html>
        """
        
        mock_http_client = Mock()
        mock_http_client.get_text.return_value = mock_response_html
        mock_http_client_class.return_value = mock_http_client
        
        config = TenderConfig(keywords=["眼科", "皮肤科"])
        fetcher = CCGPFetcher(config)
        
        results = fetcher.search_all_keywords(max_pages_per_keyword=1)
        
        assert "眼科" in results
        assert "皮肤科" in results
        assert len(results["眼科"]) == 1
        assert len(results["皮肤科"]) == 1
    
    @patch("src.fetchers.ccgp_fetcher.HttpClient")
    def test_get_all_tenders(self, mock_http_client_class):
        """测试获取所有招标信息（合并）."""
        # 模拟不同关键词返回相同结果
        mock_response_html = """
        <html>
        <body>
            <ul class="vT-srch-result-list">
                <li>
                    <a href="http://example.com/1">通用项目</a>
                    <span class="time">2024-01-15</span>
                    <span class="source">中国政府采购网</span>
                </li>
            </ul>
        </body>
        </html>
        """
        
        mock_http_client = Mock()
        mock_http_client.get_text.return_value = mock_response_html
        mock_http_client_class.return_value = mock_http_client
        
        config = TenderConfig(keywords=["眼科", "皮肤科"])
        fetcher = CCGPFetcher(config)
        
        tenders = fetcher.get_all_tenders(max_pages_per_keyword=1)
        
        # 应该去重，只保留一个
        assert len(tenders) == 1
        assert tenders[0].title == "通用项目"
    
    def test_context_manager(self):
        """测试上下文管理器."""
        with CCGPFetcher() as fetcher:
            assert isinstance(fetcher, CCGPFetcher)
    
    @patch("src.fetchers.ccgp_fetcher.HttpClient")
    def test_close(self, mock_http_client_class):
        """测试关闭."""
        mock_http_client = Mock()
        mock_http_client_class.return_value = mock_http_client
        
        fetcher = CCGPFetcher()
        fetcher.close()
        
        mock_http_client.close.assert_called_once()
