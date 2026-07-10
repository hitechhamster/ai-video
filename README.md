# AI火柴人

自己搭建的火柴人风格短视频生成工具：选画风 → 输脚本 → 配音 → 自动生成一个**剪映草稿**，打开剪映App即可预览/二次编辑/导出竖屏短视频。

当前实现 **PPT图片模式**：
1. 脚本按句子切分（仅用于后续对齐，脚本本身手动输入，不用AI写稿）
2. 整段脚本一次性调用 MiniMax TTS 合成配音（保留原有的标点/停顿节奏，避免逐句合成的割裂感），再用 ffmpeg 静音检测把整段配音切回每句的时间线
3. 生成一张"角色定妆图"，后续每句配图都拿它当参考图（图生图），锁定跨分镜的角色一致性
4. 每段先调用 MiniMax LLM 把原始旁白转成结构化场景提示词（主题→背景色/构图自动匹配、配角视觉体系，参考自原 Coze 工作流的规则），再调用火山引擎方舟豆包·Seedream 生成分镜图
5. 用 `pyjianyingdraft` 库把整段配音、逐句分镜图（带推镜关键帧动画）、字幕、背景音乐（自动铺满循环）、剪映内置"震动"+"荧幕噪点"特效，一次性装配成一个剪映草稿，写入本地剪映草稿文件夹

AI短片拼接模式（每段直接生成视频片段而非静态图）尚未实现，架构上已预留 `VideoProvider` 扩展点。

## 目录结构

- `backend/` — Python FastAPI 服务，负责画风/项目管理、调用 TTS 和文生图 API、把配音+分镜图+字幕+特效装配成剪映草稿
- `frontend/` — Vite + React + TypeScript 网页界面

## 前置条件

- Python 3.10+
- Node.js 18+
- 本地安装 `ffmpeg` 并加入 PATH（`ffmpeg -version` 能正常输出即可，仅用于配音静音检测切分和探测音频/视频时长）
- 本机安装**剪映专业版**（草稿要落在剪映本地草稿文件夹里，剪映App才能打开预览/编辑/导出；生成草稿这一步本身不需要剪映在后台运行）
- [MiniMax 开放平台](https://platform.minimax.io) 账号 + API Key（配音）
- [火山引擎方舟(Ark)](https://console.volcengine.com/ark) 账号 + API Key（豆包·Seedream 文生图）

## 启动方式

### 后端

```bash
cd backend
python -m venv .venv
./.venv/Scripts/pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # macOS/Linux

cp .env.example .env
# 编辑 .env，填入 MINIMAX_API_KEY、ARK_API_KEY
# 再确认 JIANYING_DRAFTS_DIR 是否等于剪映App "全局设置 -> 草稿位置" 里显示的路径

./.venv/Scripts/python -m uvicorn app.main:app --reload --port 8010
```

启动后访问 `http://127.0.0.1:8010/docs` 可以看到自动生成的接口文档。

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173`。

## 使用流程

1. 「音乐库」：上传自己的背景音乐（本工具不会预置任何曲目，避免版权问题）
2. 「画风」：使用内置画风，或点击「制作画风」自定义一个新风格
3. 首页「模板」：选一个模板（画风+配音+背景音乐已经配好）→ 只填脚本 → 生成；或者点「自定义生成」手动选画风/配音/音乐，选完后可以「保存当前搭配为模板」，下次直接复用
4. 生成时自动跳转到结果页，实时轮询显示「整段配音合成中/按停顿切分句子时间线/生成角色定妆图/第X/N段：画面生成中/装配剪映草稿」的进度
5. 生成完成后结果页会显示草稿名和剪映草稿文件夹路径，打开剪映App在草稿箱里找到它即可预览/二次编辑/导出

内置了两个示例模板（外汇科普、情感治愈），都没有配背景音乐——上传音乐后可以在「自定义生成」里另存一份带音乐的模板。

## 已知限制 / 后续计划

- AI短片拼接模式未实现
- 脚本需要用户自己写好再粘贴进来，暂无 AI 自动写稿
- 静音检测切分句子时间线依赖脚本本身的标点停顿，如果整段话说得非常连贯没有停顿，会自动降级成按字数比例切分（时间线会不如静音检测精确）
- 原Coze工作流里的"鼠标点击音效"轨道本次未实现
- 本地个人使用设计，未做多用户/鉴权/云端部署
- 通义万相适配器仍保留在 `backend/app/providers/image/tongyi_wanxiang.py` 作为备用，想换回去只需在 `pipeline.py` 里改一行 import
- 结构化场景提示词生成失败时（LLM调用异常/解析失败）会自动降级成"画风+原文"拼接的简单提示词，不会中断整体生成
- `pyjianyingdraft` 库的剪映版本兼容性仍在演进中，如果升级剪映后草稿打不开/特效加载不出来，多半是字体名/特效名在新版本变了，需要重新跑一遍 `backend/scripts/probe_jianying_draft.py` 验证
