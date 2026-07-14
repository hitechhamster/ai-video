---
description: 把剪映刚导出的 mp4 发到 YouTube（自动读标题/描述/标签）
---

把用户刚在剪映导出的视频上传到 YouTube：

```
cd backend && .venv/Scripts/python.exe scripts/publish_today.py
```

如果用户在 `$ARGUMENTS` 里指定了某个 mp4 路径，就传给脚本：

```
cd backend && .venv/Scripts/python.exe scripts/publish_today.py "$ARGUMENTS"
```

脚本会抓 `youtube_export_dir` 里最新的 mp4，按文件名（=草稿名）反查项目、
读它的 `youtube_meta.json` 拿标题/描述/标签，然后调 YouTube API 上传，最后打印视频链接。

注意：
- 这会**对外发布**内容（隐私取决于 meta/config，默认 private）。如果脚本报「未授权 / 缺 client_secret」，
  照它打印的指引让用户先做一次性设置（`scripts/youtube_auth.py`），**不要**替用户碰账号密码。
- 上传成功后把视频链接回给用户。
