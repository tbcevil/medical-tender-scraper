"""HTTP客户端模块测试."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from src.http_client import HttpClient


class TestHttpClient:
    """HttpClient测试类."""
    
    def test_default_headers(self):
        """测试默认请求头."""
        client = HttpClient()
        
        assert "User-Agent" in client.headers
        assert "Mozilla/5.0" in client.headers["User-Agent"]
        assert client.headers["Accept-Language"] == "zh-CN,zh;q=0.9,en;q=0.8"
    
    def test_custom_headers(self):
        """测试自定义请求头."""
        custom_headers = {"X-Custom": "value"}
        client = HttpClient(headers=custom_headers)
        
        assert client.headers["X-Custom"] == "value"
        # 默认请求头仍然保留
        assert "User-Agent" in client.headers
    
    def test_custom_timeout(self):
        """测试自定义超时."""
        client = HttpClient(timeout=60)
        assert client.timeout == 60
    
    @patch("httpx.Client")
    def test_get_success(self, mock_client_class):
        """测试GET请求成功."""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html>test</html>"
        mock_response.raise_for_status = Mock()
        
        # 模拟客户端
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client.is_closed = False
        mock_client_class.return_value = mock_client
        
        http_client = HttpClient()
        http_client._client = mock_client
        
        response = http_client.get("http://example.com")
        
        assert response.status_code == 200
        mock_response.raise_for_status.assert_called_once()
    
    @patch("httpx.Client")
    def test_get_with_params(self, mock_client_class):
        """测试带参数的GET请求."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client.is_closed = False
        mock_client_class.return_value = mock_client
        
        http_client = HttpClient()
        http_client._client = mock_client
        
        params = {"key": "value", "page": 1}
        http_client.get("http://example.com", params=params)
        
        mock_client.get.assert_called_once_with(
            "http://example.com",
            params=params
        )
    
    @patch("httpx.Client")
    def test_get_text(self, mock_client_class):
        """测试获取文本内容."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html>中文内容</html>"
        mock_response.apparent_encoding = "utf-8"
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client.is_closed = False
        mock_client_class.return_value = mock_client
        
        http_client = HttpClient()
        http_client._client = mock_client
        
        text = http_client.get_text("http://example.com")
        
        assert text == "<html>中文内容</html>"
    
    @patch("httpx.Client")
    def test_get_text_with_encoding(self, mock_client_class):
        """测试指定编码获取文本."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html>内容</html>"
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client.is_closed = False
        mock_client_class.return_value = mock_client
        
        http_client = HttpClient()
        http_client._client = mock_client
        
        text = http_client.get_text("http://example.com", encoding="gb2312")
        
        assert text == "<html>内容</html>"
        mock_response.encoding = "gb2312"
    
    @patch("httpx.Client")
    def test_get_http_error(self, mock_client_class):
        """测试HTTP错误处理."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=Mock(),
            response=Mock(status_code=404)
        )
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client.is_closed = False
        mock_client_class.return_value = mock_client
        
        http_client = HttpClient()
        http_client._client = mock_client
        
        with pytest.raises(httpx.HTTPStatusError):
            http_client.get("http://example.com/notfound")
    
    @patch("httpx.Client")
    def test_context_manager(self, mock_client_class):
        """测试上下文管理器."""
        mock_client = Mock()
        mock_client.is_closed = False
        mock_client_class.return_value = mock_client
        
        with HttpClient() as client:
            assert isinstance(client, HttpClient)
        
        mock_client.close.assert_called_once()
    
    def test_close(self):
        """测试关闭客户端."""
        http_client = HttpClient()
        http_client._client = Mock()
        http_client._client.is_closed = False
        
        http_client.close()
        
        http_client._client.close.assert_called_once()
