"""HTTP客户端模块 - 使用httpx进行HTTP请求."""

import httpx
from typing import Optional, Dict, Any


class HttpClient:
    """HTTP客户端类."""
    
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    def __init__(self, timeout: int = 30, headers: Optional[Dict[str, str]] = None):
        """初始化HTTP客户端.
        
        Args:
            timeout: 请求超时时间(秒)
            headers: 自定义请求头
        """
        self.timeout = timeout
        
        # 合并默认请求头和自定义请求头
        self.headers = self.DEFAULT_HEADERS.copy()
        if headers:
            self.headers.update(headers)
        
        # 创建httpx客户端
        self._client: Optional[httpx.Client] = None
    
    def _get_client(self) -> httpx.Client:
        """获取或创建httpx客户端."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                timeout=self.timeout,
                headers=self.headers,
                follow_redirects=True
            )
        return self._client
    
    def get(
        self, 
        url: str, 
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> httpx.Response:
        """发送GET请求.
        
        Args:
            url: 请求URL
            params: URL参数
            **kwargs: 其他请求参数
            
        Returns:
            httpx.Response: 响应对象
            
        Raises:
            httpx.RequestError: 请求失败
        """
        client = self._get_client()
        response = client.get(url, params=params, **kwargs)
        response.raise_for_status()
        return response
    
    def get_text(
        self, 
        url: str, 
        params: Optional[Dict[str, Any]] = None,
        encoding: Optional[str] = None,
        **kwargs
    ) -> str:
        """发送GET请求并返回文本内容.
        
        Args:
            url: 请求URL
            params: URL参数
            encoding: 指定编码(默认自动检测)
            **kwargs: 其他请求参数
            
        Returns:
            str: 响应文本内容
            
        Raises:
            httpx.RequestError: 请求失败
        """
        response = self.get(url, params=params, **kwargs)
        
        if encoding:
            response.encoding = encoding
        else:
            # 尝试从Content-Type获取编码，否则使用UTF-8
            content_type = response.headers.get('Content-Type', '')
            if 'charset=' in content_type:
                response.encoding = content_type.split('charset=')[-1].split(';')[0]
            else:
                response.encoding = 'utf-8'
        
        return response.text
    
    def close(self) -> None:
        """关闭HTTP客户端."""
        if self._client and not self._client.is_closed:
            self._client.close()
    
    def __enter__(self) -> "HttpClient":
        """上下文管理器入口."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口."""
        self.close()
