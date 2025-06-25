import json
import time
from collections.abc import Generator
from typing import Any

import requests
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class GetAccessTokenTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        获取微信访问令牌工具 (根据新文档，无缓存)
        """
        try:
            appid = tool_parameters.get("appid")
            appsecret = tool_parameters.get("appsecret")
            
            if not appid or not appsecret:
                yield self.create_text_message("错误：AppID 和 AppSecret 不能为空。")
                return
            
            # 直接从API获取新的access_token
            success, result = self._get_access_token_from_api(appid, appsecret)
            
            if success:
                # API调用成功，result是包含access_token的字典
                yield self.create_json_message({
                    "access_token": result.get("access_token"),
                    "expires_in": result.get("expires_in", 7200), # 通常微信返回7200
                    # "from_cache" 字段不再需要，因为没有缓存了
                })
            else:
                # API调用失败，result是错误信息字符串
                yield self.create_text_message(f"获取 access_token 失败: {result}")
                
        except Exception as e:
            # 捕获其他意外错误
            yield self.create_text_message(f"执行工具时发生意外错误: {str(e)}")
    
    def _get_access_token_from_api(self, appid: str, appsecret: str) -> tuple[bool, Any]:
        """
        从微信API获取access_token。
        返回一个元组 (success: bool, data: dict | str)。
        如果成功，success为True，data为包含token的字典。
        如果失败，success为False，data为错误信息字符串。
        """
        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": appid,
            "secret": appsecret
        }
        
        max_retries = 3 # 可以保留重试机制
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status() # 如果HTTP状态码是4xx或5xx，则抛出异常
                
                data = response.json()
                
                if "access_token" in data and "expires_in" in data:
                    return True, data # 成功，返回整个data字典
                elif "errcode" in data and data["errcode"] != 0:
                    # 微信API返回了明确的错误
                    error_message = f"微信API错误码 {data['errcode']}: {data.get('errmsg', '未知微信API错误')}"
                    if attempt == max_retries - 1:
                        return False, error_message
                    # 否则继续重试
                else:
                    # 未知的响应格式
                    unknown_error = "从微信API获取access_token时收到未知响应格式。"
                    if attempt == max_retries - 1:
                        return False, unknown_error
                
            except requests.exceptions.HTTPError as e:
                # HTTP错误 (4xx, 5xx)
                http_error_msg = f"HTTP错误 {e.response.status_code}: {e.response.reason}. 响应内容: {e.response.text}"
                if attempt == max_retries - 1:
                    return False, http_error_msg
            except requests.exceptions.RequestException as e:
                # 其他网络请求相关的错误 (例如超时, DNS解析失败)
                network_error_msg = f"网络请求失败: {str(e)}"
                if attempt == max_retries - 1:
                    return False, network_error_msg
            except json.JSONDecodeError:
                # 响应不是有效的JSON
                json_error_msg = "解析微信API响应失败，不是有效的JSON。"
                if attempt == max_retries - 1:
                    return False, json_error_msg

            if attempt < max_retries - 1:
                time.sleep(1) # 重试前等待1秒
        
        return False, "尝试所有重试次数后仍无法获取access_token。"
