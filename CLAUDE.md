# AI火柴人 / 长衫先生 视频工厂

脚本 → 每句配一张同画风 AI 插画 + 运镜 + Gemini 配音 + 字幕 → 输出**剪映草稿**（用 `pyjianyingdraft` 直接写草稿 JSON，不经剪映渲染）。用户在剪映里打开草稿、点导出得到 mp4。

## 运行

- 后端：`cd backend && .venv/Scripts/python.exe -m uvicorn app.main:app --port 8010`
- 前端：`cd frontend && npm run dev`
- Python 一律用 `backend/.venv/Scripts/python.exe`（系统 python 没装依赖）。
- 数据在 `backend/app.db`（gitignored）；改模型后用「挪走 app.db 重新 seed」，不写迁移。
- 密钥在 `backend/.env`（gitignored）：`GEMINI_API_KEY` 一个 key 就能跑「长衫先生/小黑」（gemini 渠道：生图+配音+LLM 全包）。

## 关键概念

- **画风 Style**：`image_provider`（gemini/openrouter）、`enforce_monochrome`/`enforce_color`（生成后按平均饱和度重试兜底）、`scene_mode`（drama 戏剧向 / teaching 教学向）、可挂 `reference_image_url` 锁定角色。
- **效果预设 EffectPreset**：字幕字体/字号/颜色/位置 + 特效 + 转场 + 推镜，跟画风独立、自由组合。
- **模板 Template**：画风 + 配音 + 效果预设的一套搭配。「长衫先生」=黑白长衫教学向 + charon + 漫画撕纸转场，用于八字/风水科普。
- 场景提示词引擎在 `app/services/scene_prompt.py`；teaching 模式按分镜序号轮换镜头类型（全景/特写/大图解/对比/俯视）。

## 每日出片 + 发 YouTube（半自动，用户一句话触发）

文件化在 `backend/scripts/`，不依赖对话记忆。任何会话在本仓库里都能跑。

- **「生成今天的视频」** → `cd backend && .venv/Scripts/python.exe scripts/make_today.py`
  自动从题库轮换选题 → LLM 写稿 + 生成 YouTube 标题/描述/标签 → 出图配音 → 剪映草稿 →
  元数据写到 `storage/projects/<id>/youtube_meta.json`。跑完打印草稿名。
  指定选题：`scripts/make_today.py "your topic"`。
- 用户在剪映打开该草稿 → **导出**到 `youtube_export_dir`（config，默认 `C:\Users\22460\Videos`，剪映默认文件名=草稿名，别改名）。
- **「发今天的视频」** → `cd backend && .venv/Scripts/python.exe scripts/publish_today.py`
  抓导出目录里最新的 mp4 → 按文件名（=草稿名）反查项目、读 youtube_meta.json → 调 YouTube API 上传。
  也可 `scripts/publish_today.py <path.mp4>` 指定文件。

一次性设置（用户自己做，助手不碰账号）：Google Cloud 建项目→启用 YouTube Data API v3→建 OAuth 桌面客户端→
下载 `client_secret.json` 放 `backend/`→`pip install google-api-python-client google-auth-oauthlib google-auth-httplib2`→
`python scripts/youtube_auth.py` 授权一次。OAuth 同意屏幕发布到 In production，否则刷新令牌 7 天过期。

隐私默认 `youtube_privacy=private`（config/.env 可改 unlisted/public）。合规：内容走「文化/性格/处世智慧」框架，不做吉凶预测。
