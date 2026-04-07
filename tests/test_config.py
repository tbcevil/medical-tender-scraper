"""配置模块测试."""

import pytest
from datetime import datetime, timedelta
from src.config import TenderConfig


class TestTenderConfig:
    """TenderConfig测试类."""
    
    def test_default_values(self):
        """测试默认值."""
        config = TenderConfig()
        
        assert config.base_url == "http://www.ccgp.gov.cn"
        assert config.keywords == ["眼科", "皮肤科"]
        assert config.days_back == 7
        assert config.timeout == 30
        assert config.max_results == 100
        assert config.output_file == "medical_tenders.xlsx"
    
    def test_custom_values(self):
        """测试自定义值."""
        config = TenderConfig(
            base_url="http://test.example.com",
            keywords=["测试关键词"],
            days_back=14,
            timeout=60,
            max_results=200,
            output_file="test.xlsx"
        )
        
        assert config.base_url == "http://test.example.com"
        assert config.keywords == ["测试关键词"]
        assert config.days_back == 14
        assert config.timeout == 60
        assert config.max_results == 200
        assert config.output_file == "test.xlsx"
    
    def test_get_search_url(self):
        """测试获取搜索URL."""
        config = TenderConfig()
        assert config.get_search_url() == "http://search.ccgp.gov.cn/bxsearch"
    
    def test_get_date_range(self):
        """测试获取日期范围."""
        config = TenderConfig(days_back=7)
        start_date, end_date = config.get_date_range()
        
        # 验证日期格式
        assert len(start_date) == 10  # YYYY:MM:DD
        assert len(end_date) == 10
        assert start_date.count(":") == 2
        assert end_date.count(":") == 2
        
        # 验证日期差值
        start = datetime.strptime(start_date, "%Y:%m:%d")
        end = datetime.strptime(end_date, "%Y:%m:%d")
        delta = end - start
        assert delta.days == 7
    
    def test_validation_days_back_min(self):
        """测试days_back最小值验证."""
        with pytest.raises(ValueError):
            TenderConfig(days_back=0)
    
    def test_validation_days_back_max(self):
        """测试days_back最大值验证."""
        with pytest.raises(ValueError):
            TenderConfig(days_back=31)
    
    def test_validation_timeout_min(self):
        """测试timeout最小值验证."""
        with pytest.raises(ValueError):
            TenderConfig(timeout=3)
    
    def test_validation_max_results_min(self):
        """测试max_results最小值验证."""
        with pytest.raises(ValueError):
            TenderConfig(max_results=5)
