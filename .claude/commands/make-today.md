---
description: 生成今天的长衫先生八字/风水视频（选题→写稿→出图配音→剪映草稿）
---

跑每日出片脚本，生成今天的视频草稿和 YouTube 元数据：

```
cd backend && .venv/Scripts/python.exe scripts/make_today.py
```

如果用户在 `$ARGUMENTS` 里给了具体选题，就把它作为参数传进去：

```
cd backend && .venv/Scripts/python.exe scripts/make_today.py "$ARGUMENTS"
```

脚本会自动选题（题库轮换）、用 LLM 写英文教学脚本、生成 YouTube 标题/描述/标签、
出图配音并装配成剪映草稿，最后把元数据写到 `storage/projects/<id>/youtube_meta.json`。

跑完把**草稿名**告诉用户，并提醒：在剪映里打开这个草稿 → 导出到 `youtube_export_dir`
（剪映默认导出文件名就是草稿名，别改）→ 然后用 `/publish-today` 发布。

生成较慢（出图+配音几分钟），用后台任务跑并轮询，别干等。失败要把 `job.error_message` 如实报出来。
