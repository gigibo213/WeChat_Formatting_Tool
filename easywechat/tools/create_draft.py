import json
import time
from collections.abc import Generator
from typing import Any

import requests
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class CreateDraftTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        创建微信草稿工具
        """
        try:
            access_token = tool_parameters.get("access_token")
            title = tool_parameters.get("title")
            content = tool_parameters.get("content")
            author = tool_parameters.get("author", "")
            digest = tool_parameters.get("digest", "")
            thumb_media_id = tool_parameters.get("thumb_media_id")
            
            if not access_token or not title or not content or not thumb_media_id:
                yield self.create_text_message("错误：access_token、title、content和thumb_media_id不能为空")
                return
            
            # 验证内容长度
            if len(content) > 20000:
                yield self.create_text_message("错误：文章内容不能超过20000字符")
                return
            
            # 如果没有提供摘要，自动生成（取前54个字符）
            if not digest:
                # 移除HTML标签来生成摘要
                import re
                clean_content = re.sub(r'<[^>]+>', '', content)
                digest = clean_content[:54]
            
            # 创建草稿
            result = self._create_draft_api(access_token, title, content, author, digest, thumb_media_id)
            
            if result:
                yield self.create_json_message(result)
            else:
                yield self.create_text_message("创建草稿失败")
                
        except Exception as e:
            yield self.create_text_message(f"创建草稿时发生错误: {str(e)}")
    
    def _create_draft_api(self, access_token: str, title: str, content: str, 
                         author: str, digest: str, thumb_media_id: str) -> dict:
        """
        调用微信API创建草稿，支持重试机制
        """
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
        
        # 构建请求数据
        articles = [{
            "title": title,
            "author": author,
            "digest": digest,
            "content": content,
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 0,
            "only_fans_can_comment": 0
        }]
        
        data = {
            "articles": articles
        }

        # 将数据手动序列化为JSON字符串，并确保中文字符不被转义为ASCII，然后编码为UTF-8
        json_payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url, 
                    data=json_payload, # 使用data参数并传入编码后的字节流
                    headers=headers,   # 使用包含charset的请求头
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                
                if "media_id" in result:
                    return {
                        "media_id": result["media_id"],
                        "title": title,
                        "author": author,
                        "digest": digest,
                        "thumb_media_id": thumb_media_id,
                        "content_length": len(content)
                    }
                else:
                    error_code = result.get("errcode", "未知")
                    error_msg = result.get("errmsg", "未知错误")
                    
                    if attempt == max_retries - 1:
                        raise Exception(f"微信API错误 {error_code}: {error_msg}")
                    
                    time.sleep(1)
                    
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise Exception(f"创建草稿请求失败: {str(e)}")
                time.sleep(1)
        
        return {}
