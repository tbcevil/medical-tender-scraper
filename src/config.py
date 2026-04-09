"""配置模块 - 使用Pydantic进行配置管理."""

from datetime import datetime, timedelta
from typing import List, Tuple
from pydantic import BaseModel, Field


class TenderConfig(BaseModel):
    """招投标信息搜集配置类."""
    
    base_url: str = Field(
        default="http://www.ccgp.gov.cn",
        description="中国政府采购网基础URL"
    )
    
    keywords: List[str] = Field(
        default=["眼科"],
        description="搜索关键词列表"
    )
    
    days_back: int = Field(
        default=7,
        ge=1,
        le=30,
        description="搜索最近多少天的招标信息"
    )
    
    timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="HTTP请求超时时间(秒)"
    )
    
    max_results: int = Field(
        default=100,
        ge=0,
        le=500,
        description="每个关键词最大结果数，0表示获取所有结果"
    )
    
    output_file: str = Field(
        default="medical_tenders.xlsx",
        description="输出Excel文件名"
    )
    
    def get_search_url(self) -> str:
        """获取搜索URL模板."""
        return "http://search.ccgp.gov.cn/bxsearch"
    
    def get_date_range(self) -> Tuple[str, str]:
        """获取搜索日期范围.
        
        Returns:
            tuple: (开始日期, 结束日期) 格式: YYYY:MM:DD
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.days_back)
        
        return (
            start_date.strftime("%Y:%m:%d"),
            end_date.strftime("%Y:%m:%d")
        )
    
    class Config:
        """Pydantic配置."""
        validate_assignment = True
