"""Excel导出模块测试."""

import pytest
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from src.parser import TenderInfo
from src.exporters.excel_exporter import ExcelExporter


class TestExcelExporter:
    """ExcelExporter测试类."""
    
    def test_init_default_path(self):
        """测试默认路径初始化."""
        exporter = ExcelExporter()
        
        assert "medical_tenders_" in str(exporter.output_path)
        assert str(exporter.output_path).endswith(".xlsx")
    
    def test_init_custom_path(self):
        """测试自定义路径初始化."""
        exporter = ExcelExporter("custom_output.xlsx")
        
        assert str(exporter.output_path) == "custom_output.xlsx"
    
    def test_export_empty_list(self):
        """测试导出空列表."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_empty.xlsx"
            exporter = ExcelExporter(str(output_path))
            
            result = exporter.export([])
            
            assert Path(result).exists()
            assert Path(result).stat().st_size > 0
    
    def test_export_with_data(self):
        """测试导出数据."""
        tenders = [
            TenderInfo(
                title="眼科设备采购项目",
                url="http://example.com/1",
                publish_date="2024-01-15",
                source="中国政府采购网",
                keyword="眼科",
                description="采购眼科医疗设备",
                region="北京市",
                agency="北京代理公司",
                project_code="ABC123"
            ),
            TenderInfo(
                title="皮肤科治疗设备",
                url="http://example.com/2",
                publish_date="2024-01-14",
                source="中国政府采购网",
                keyword="皮肤科",
                description="采购皮肤科设备",
                region="上海市",
                agency="上海代理公司",
                project_code="DEF456"
            ),
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_data.xlsx"
            exporter = ExcelExporter(str(output_path))
            
            result = exporter.export(tenders)
            
            assert Path(result).exists()
            assert Path(result).stat().st_size > 0
    
    def test_export_with_summary(self):
        """测试导出带汇总."""
        tenders = [
            TenderInfo(
                title="项目1",
                url="http://example.com/1",
                publish_date="2024-01-15",
                source="中国政府采购网",
                keyword="眼科",
            ),
            TenderInfo(
                title="项目2",
                url="http://example.com/2",
                publish_date="2024-01-14",
                source="中国政府采购网",
                keyword="皮肤科",
            ),
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_summary.xlsx"
            exporter = ExcelExporter(str(output_path))
            
            result = exporter.export(tenders, include_summary=True)
            
            assert Path(result).exists()
    
    def test_export_without_summary(self):
        """测试导出不带汇总."""
        tenders = [
            TenderInfo(
                title="项目1",
                url="http://example.com/1",
                publish_date="2024-01-15",
                source="中国政府采购网",
                keyword="眼科",
            ),
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_no_summary.xlsx"
            exporter = ExcelExporter(str(output_path))
            
            result = exporter.export(tenders, include_summary=False)
            
            assert Path(result).exists()
    
    def test_calculate_stats(self):
        """测试统计数据计算."""
        tenders = [
            TenderInfo(
                title="项目1",
                url="http://example.com/1",
                publish_date="2024-01-15",
                source="中国政府采购网",
                keyword="眼科",
                region="北京市",
            ),
            TenderInfo(
                title="项目2",
                url="http://example.com/2",
                publish_date="2024-01-14",
                source="中国政府采购网",
                keyword="眼科",
                region="北京市",
            ),
            TenderInfo(
                title="项目3",
                url="http://example.com/3",
                publish_date="2024-01-13",
                source="中国政府采购网",
                keyword="皮肤科",
                region="上海市",
            ),
        ]
        
        exporter = ExcelExporter()
        stats = exporter._calculate_stats(tenders)
        
        assert stats["总记录数"] == 3
        assert stats["关键词 '眼科' 数量"] == 2
        assert stats["关键词 '皮肤科' 数量"] == 1
        assert stats["来源 '中国政府采购网' 数量"] == 3
        assert stats["地区 '北京市' 数量"] == 2
        assert stats["地区 '上海市' 数量"] == 1
    
    def test_export_multiple_sheets(self):
        """测试多工作表导出."""
        tenders_by_keyword = {
            "眼科": [
                TenderInfo(
                    title="眼科项目1",
                    url="http://example.com/1",
                    publish_date="2024-01-15",
                    source="中国政府采购网",
                    keyword="眼科",
                ),
            ],
            "皮肤科": [
                TenderInfo(
                    title="皮肤科项目1",
                    url="http://example.com/2",
                    publish_date="2024-01-14",
                    source="中国政府采购网",
                    keyword="皮肤科",
                ),
            ],
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_multi.xlsx"
            exporter = ExcelExporter(str(output_path))
            
            result = exporter.export_multiple_sheets(tenders_by_keyword)
            
            assert Path(result).exists()
    
    def test_export_multiple_sheets_empty(self):
        """测试空数据多工作表导出."""
        tenders_by_keyword = {
            "眼科": [],
            "皮肤科": [],
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_multi_empty.xlsx"
            exporter = ExcelExporter(str(output_path))
            
            result = exporter.export_multiple_sheets(tenders_by_keyword)
            
            assert Path(result).exists()
    
    def test_export_creates_directory(self):
        """测试导出创建目录."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "nested" / "dir"
            output_path = nested_dir / "test.xlsx"
            exporter = ExcelExporter(str(output_path))
            
            tenders = [
                TenderInfo(
                    title="项目1",
                    url="http://example.com/1",
                    publish_date="2024-01-15",
                    source="中国政府采购网",
                    keyword="眼科",
                ),
            ]
            
            result = exporter.export(tenders)
            
            assert Path(result).exists()
            assert nested_dir.exists()
