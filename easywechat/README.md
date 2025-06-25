# EasyWeChat Dify插件

**Author:** xc
**Version:** 0.0.1
**Type:** tool

这是一个为Dify平台开发的微信公众号开发工具插件，提供了微信公众号开发中常用的三个核心功能。

## 功能特性

### 1. 获取访问令牌 (get_access_token)
- 使用AppID和AppSecret获取微信访问令牌
- 内置重试机制，最多重试3次

**输入参数：**
- `appid`: 微信公众号AppID
- `appsecret`: 微信公众号AppSecret

**返回结果：**
```json
{
  "access_token": "访问令牌",
  "expires_in": 7200
}
```

### 2. 上传永久素材 (upload_permanent_media)
- 根据图片URL将图片上传到微信永久素材库
- 支持jpg、png、gif、bmp格式
- 自动验证文件大小（最大10MB）
- 返回media_id供后续使用

**输入参数：**
- `access_token`: 微信访问令牌
- `image_url`: 图片URL地址

**返回结果：**
```json
{
  "media_id": "素材ID",
  "url": "图片URL",
  "filename": "文件名",
  "size": 文件大小
}
```

### 3. 创建草稿 (create_draft)
- 创建微信公众号图文消息草稿
- 支持HTML格式内容
- 自动生成摘要（如未提供）
- 验证内容长度限制

**输入参数：**
- `access_token`: 微信访问令牌
- `title`: 文章标题
- `content`: 文章内容（HTML格式）
- `author`: 作者（可选）
- `digest`: 摘要（可选，自动生成）
- `thumb_media_id`: 封面图片媒体ID

**返回结果：**
```json
{
  "media_id": "草稿媒体ID",
  "title": "文章标题",
  "author": "作者",
  "digest": "摘要",
  "thumb_media_id": "封面图片ID",
  "content_length": 内容长度
}
```

## 使用流程

1. **获取访问令牌**
   ```
   使用get_access_token工具，输入appid和appsecret
   ```

2. **上传封面图片**
   ```
   使用upload_permanent_media工具，输入access_token和图片URL
   获得封面图片的media_id
   ```

3. **创建草稿**
   ```
   使用create_draft工具，输入所有必要参数
   获得草稿的media_id
   ```

## 技术特性

- **重试机制**: 所有API调用支持最多3次重试
- **错误处理**: 完善的错误码处理和异常管理
- **参数验证**: 严格的输入参数验证
- **安全性**: 支持微信API的所有安全要求

## 注意事项

1. 确保微信公众号已开通开发者权限
2. 将服务器IP地址添加到微信公众平台的IP白名单
3. 图片文件大小不能超过10MB
4. 文章内容不能超过20000字符
5. 封面图片必须是永久素材的media_id

## 错误处理

插件内置了完善的错误处理机制：
- 网络请求失败自动重试
- 微信API错误码详细说明
- 参数验证错误提示
- 文件格式和大小验证

## 依赖要求

- dify_plugin >= 0.2.0
- requests >= 2.31.0
