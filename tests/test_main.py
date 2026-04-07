"""主程序模块测试."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.main import (
    setup_argument_parser,
    create_config_from_args,
    scrape_tenders,
    export_tenders,
    main
)
from src.config import TenderConfig
from src.parser import TenderInfo


class TestArgumentParser:
    """命令行参数解析测试."""
    
    def test_parser_default_values(self):
        """测试默认值."""
        parser = setup_argument_parser()
        args = parser.parse_args([])
        
        assert args.keywords is None
        assert args.days == 7
        assert args.output is None
        assert args.max_results == 100
        assert args.max_pages == 5
        assert args.timeout == 30
        assert args.multi_sheet is False
        assert args.no_summary is False
        assert args.verbose is False
    
    def test_parser_custom_values(self):
        """测试自定义值."""
        parser = setup_argument_parser()
        args = parser.parse_args([
            "-k", "眼科", "皮肤科",
            "-d", "14",
            "-o", "output.xlsx",
            "-m", "200",
            "-p", "10",
            "-t", "60",
            "--multi-sheet",
            "--no-summary",
            "-v"
        ])
        
        assert args.keywords == ["眼科", "皮肤科"]
        assert args.days == 14
        assert args.output == "output.xlsx"
        assert args.max_results == 200
        assert args.max_pages == 10
        assert args.timeout == 60
        assert args.multi_sheet is True
        assert args.no_summary is True
        assert args.verbose is True
    
    def test_parser_short_options(self):
        """测试短选项."""
        parser = setup_argument_parser()
        args = parser.parse_args(["-k", "测试"])
        
        assert args.keywords == ["测试"]


class TestCreateConfig:
    """配置创建测试."""
    
    def test_create_config_default(self):
        """测试默认配置."""
        parser = setup_argument_parser()
        args = parser.parse_args([])
        
        config = create_config_from_args(args)
        
        assert isinstance(config, TenderConfig)
        assert config.days_back == 7
        assert config.keywords == ["眼科", "皮肤科"]
    
    def test_create_config_custom(self):
        """测试自定义配置."""
        parser = setup_argument_parser()
        args = parser.parse_args([
            "-k", "测试1", "测试2",
            "-d", "14",
            "-o", "test.xlsx",
            "-m", "50",
            "-t", "45"
        ])
        
        config = create_config_from_args(args)
        
        assert config.keywords == ["测试1", "测试2"]
        assert config.days_back == 14
        assert config.output_file == "test.xlsx"
        assert config.max_results == 50
        assert config.timeout == 45


class TestScrapeTenders:
    """抓取功能测试."""
    
    @patch("src.main.CCGPFetcher")
    def test_scrape_tenders_success(self, mock_fetcher_class):
        """测试抓取成功."""
        # 模拟抓取结果
        mock_tenders = [
            TenderInfo("项目1", "url1", "2024-01-15", "source", keyword="眼科"),
            TenderInfo("项目2", "url2", "2024-01-14", "source", keyword="皮肤科"),
        ]
        
        mock_fetcher = Mock()
        mock_fetcher.search.return_value = mock_tenders
        mock_fetcher_class.return_value.__enter__ = Mock(return_value=mock_fetcher)
        mock_fetcher_class.return_value.__exit__ = Mock(return_value=False)
        
        config = TenderConfig(keywords=["眼科", "皮肤科"])
        
        result = scrape_tenders(config, max_pages=1, verbose=False)
        
        assert len(result) == 2
        assert result[0].title == "项目1"
    
    @patch("src.main.CCGPFetcher")
    def test_scrape_tenders_deduplication(self, mock_fetcher_class):
        """测试去重功能."""
        # 模拟重复结果
        mock_tenders = [
            TenderInfo("项目1", "http://same-url", "2024-01-15", "source", keyword="眼科"),
            TenderInfo("项目1重复", "http://same-url", "2024-01-15", "source", keyword="皮肤科"),
        ]
        
        mock_fetcher = Mock()
        mock_fetcher.search.return_value = mock_tenders
        mock_fetcher_class.return_value.__enter__ = Mock(return_value=mock_fetcher)
        mock_fetcher_class.return_value.__exit__ = Mock(return_value=False)
        
        config = TenderConfig(keywords=["眼科", "皮肤科"])
        
        result = scrape_tenders(config, max_pages=1, verbose=False)
        
        # 应该去重，只保留一个
        assert len(result) == 1
    
    @patch("src.main.CCGPFetcher")
    def test_scrape_tenders_error(self, mock_fetcher_class):
        """测试抓取错误."""
        mock_fetcher_class.side_effect = Exception("网络错误")
        
        config = TenderConfig(keywords=["测试"])
        
        with pytest.raises(Exception, match="网络错误"):
            scrape_tenders(config, max_pages=1)


class TestExportTenders:
    """导出功能测试."""
    
    @patch("src.main.ExcelExporter")
    def test_export_tenders_success(self, mock_exporter_class):
        """测试导出成功."""
        mock_exporter = Mock()
        mock_exporter.export.return_value = "/path/to/output.xlsx"
        mock_exporter_class.return_value = mock_exporter
        
        tenders = [
            TenderInfo("项目1", "url1", "2024-01-15", "source"),
        ]
        config = TenderConfig()
        
        result = export_tenders(tenders, config)
        
        assert result == "/path/to/output.xlsx"
        mock_exporter.export.assert_called_once()
    
    @patch("src.main.ExcelExporter")
    def test_export_tenders_empty(self, mock_exporter_class):
        """测试空数据导出."""
        config = TenderConfig()
        
        result = export_tenders([], config)
        
        assert result == ""
        mock_exporter_class.assert_not_called()
    
    @patch("src.main.ExcelExporter")
    def test_export_tenders_multi_sheet(self, mock_exporter_class):
        """测试多工作表导出."""
        mock_exporter = Mock()
        mock_exporter.export_multiple_sheets.return_value = "/path/to/output.xlsx"
        mock_exporter_class.return_value = mock_exporter
        
        tenders = [
            TenderInfo("项目1", "url1", "2024-01-15", "source", keyword="眼科"),
            TenderInfo("项目2", "url2", "2024-01-14", "source", keyword="皮肤科"),
        ]
        config = TenderConfig()
        
        result = export_tenders(tenders, config, multi_sheet=True)
        
        assert result == "/path/to/output.xlsx"
        mock_exporter.export_multiple_sheets.assert_called_once()


class TestMain:
    """主函数测试."""
    
    @patch("src.main.scrape_tenders")
    @patch("src.main.export_tenders")
    @patch("src.main.create_config_from_args")
    def test_main_success(self, mock_create_config, mock_export, mock_scrape):
        """测试主函数成功."""
        mock_config = Mock()
        mock_config.output_file = "test.xlsx"
        mock_create_config.return_value = mock_config
        
        mock_scrape.return_value = [
            TenderInfo("项目1", "url1", "2024-01-15", "source"),
        ]
        mock_export.return_value = "test.xlsx"
        
        result = main(["-k", "测试"])
        
        assert result == 0
        mock_scrape.assert_called_once()
        mock_export.assert_called_once()
    
    @patch("src.main.scrape_tenders")
    @patch("src.main.create_config_from_args")
    def test_main_no_results(self, mock_create_config, mock_scrape):
        """测试无结果."""
        mock_config = Mock()
        mock_create_config.return_value = mock_config
        mock_scrape.return_value = []
        
        result = main([])
        
        assert result == 0
    
    @patch("src.main.scrape_tenders")
    @patch("src.main.create_config_from_args")
    def test_main_error(self, mock_create_config, mock_scrape):
        """测试错误处理."""
        mock_config = Mock()
        mock_create_config.return_value = mock_config
        mock_scrape.side_effect = Exception("测试错误")
        
        result = main([])
        
        assert result == 1
    
    @patch("src.main.scrape_tenders")
    @patch("src.main.create_config_from_args")
    def test_main_keyboard_interrupt(self, mock_create_config, mock_scrape):
        """测试键盘中断."""
        mock_config = Mock()
        mock_create_config.return_value = mock_config
        mock_scrape.side_effect = KeyboardInterrupt()
        
        result = main([])
        
        assert result == 130
