import time
from collections.abc import Generator
from typing import Any, Tuple
from urllib.parse import urlparse
import os

import requests
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class UploadPermanentMediaTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        上传永久图片素材工具 (type=image)
        用户输入 access_token 和网页图片的URL，
        工具下载图片，然后上传到微信作为永久图片素材。
        返回 media_id、图片在微信的URL或微信报错。
        """
        try:
            access_token = tool_parameters.get("access_token")
            image_url = tool_parameters.get("image_url")
            
            if not access_token or not image_url:
                yield self.create_text_message("错误：access_token 和 image_url 不能为空")
                return
            
            image_data, filename, content_type = self._download_image(image_url)
            # _download_image 会在失败时抛出异常，这里无需额外检查 image_data 是否为空

            # 校验图片格式和大小 (针对 type=image)
            supported_content_types = ['image/bmp', 'image/png', 'image/jpeg', 'image/jpg', 'image/gif']
            if content_type not in supported_content_types:
                yield self.create_text_message(f"错误：不支持的图片格式: {content_type}. 支持的格式有: BMP, PNG, JPEG, JPG, GIF.")
                return
            
            if len(image_data) > 10 * 1024 * 1024: # 10MB
                yield self.create_text_message(f"错误：图片文件过大: {len(image_data) / (1024*1024):.2f}MB，超过10MB限制")
                return
            
            result = self._upload_to_wechat(access_token, image_data, filename, content_type)
            
            if "media_id" in result and "url" in result: # 成功条件
                yield self.create_json_message(result)
            elif "error" in result: # 封装的错误信息
                 yield self.create_text_message(f"上传永久图片素材失败: {result['error']}")
            else: # 未知情况
                yield self.create_text_message("上传永久图片素材失败，未知错误。")
                
        except Exception as e:
            yield self.create_text_message(f"上传永久图片素材时发生错误: {str(e)}")
    
    def _download_image(self, image_url: str) -> Tuple[bytes, str, str]:
        """
        下载图片，支持重试机制.
        返回: (image_data, filename, content_type)
        失败时抛出异常.
        """
        max_retries = 3
        last_exception = None
        for attempt in range(max_retries):
            try:
                response = requests.get(image_url, timeout=30, stream=True) # 使用 stream=True 优化大文件下载
                response.raise_for_status()
                
                content_type = response.headers.get('content-type', '').lower()
                
                if not content_type.startswith('image/'): # 基础的内容类型检查
                     raise Exception(f"链接目标似乎不是有效的图片格式，或服务器未返回正确的Content-Type: {content_type}")

                image_data = response.content # 读取所有内容
                
                # 检查下载文件大小 (例如，不超过10MB，因为微信永久图片素材也限制10MB)
                if len(image_data) > 10 * 1024 * 1024: 
                     raise Exception(f"下载的图片文件过大: {len(image_data) / (1024*1024):.2f}MB, 超过10MB下载限制")

                parsed_url = urlparse(image_url)
                filename = os.path.basename(parsed_url.path)
                if not filename or '.' not in filename: # 如果URL路径中没有文件名或扩展名
                    ext_from_content_type = content_type.split('/')[-1]
                    # 确保扩展名是微信支持的图片类型之一
                    valid_exts = ['bmp', 'png', 'jpeg', 'jpg', 'gif']
                    if ext_from_content_type in valid_exts:
                         filename = f"image.{ext_from_content_type}"
                    elif 'jpeg' in ext_from_content_type: # common case for jpg
                         filename = "image.jpg"
                    else: # 如果Content-Type也不是标准图片类型，则给一个通用名称
                         filename = "image.bin" # 后续会在_invoke中根据Content-Type校验
                
                return image_data, filename, content_type
                
            except requests.RequestException as e:
                last_exception = e
                if attempt == max_retries - 1: # 最后一次尝试失败
                    raise Exception(f"下载图片失败 (尝试 {max_retries} 次): {str(e)}")
                time.sleep(1) # 重试前等待
        
        # 此处理论上不应到达，因为循环中会抛出异常
        raise Exception(f"下载图片失败: {str(last_exception if last_exception else '未知网络错误')}")

    def _upload_to_wechat(self, access_token: str, image_data: bytes, filename: str, content_type: str) -> dict:
        """
        上传图片到微信永久素材库 (type=image)，支持重试机制
        """
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image" # type 改为 image
        
        max_retries = 3
        last_exception = None
        for attempt in range(max_retries):
            try:
                # files 参数中的 content_type 应与实际图片类型匹配
                files = {'media': (filename, image_data, content_type)}
                
                response = requests.post(url, files=files, timeout=60) # 增加超时时间以支持较大文件
                response.raise_for_status() # 检查HTTP错误
                
                data = response.json()
                
                # type=image 成功时返回 media_id 和 url
                if "media_id" in data and "url" in data:
                    return {
                        "media_id": data["media_id"],
                        "url": data["url"], 
                        "filename": filename,
                        "size": len(image_data)
                    }
                elif "errcode" in data and data["errcode"] != 0: # 微信API返回错误
                    error_msg = f"微信API错误 {data.get('errcode')}: {data.get('errmsg', '未知错误')}"
                    if attempt == max_retries - 1:
                        return {"error": error_msg} # 返回错误信息字典
                    time.sleep(1) # 重试前等待
                else: # 未知响应格式
                    if attempt == max_retries - 1:
                        return {"error": "上传后收到未知响应格式"}
                    time.sleep(1)
                    
            except requests.RequestException as e:
                last_exception = e
                if attempt == max_retries - 1:
                    return {"error": f"上传请求失败 (尝试 {max_retries} 次): {str(e)}"}
                time.sleep(1)
        
        # 此处理论上不应到达
        return {"error": f"上传失败: {str(last_exception if last_exception else '未知网络错误')}"} 
