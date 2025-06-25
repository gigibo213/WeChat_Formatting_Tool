from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class EasywechatProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        """
        验证微信开发工具的凭据
        目前不需要全局凭据验证，每个工具都有自己的参数验证
        """
        try:
            # 微信工具不需要全局凭据验证
            # 每个工具都会验证自己的参数（appid, appsecret, access_token等）
            pass
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
