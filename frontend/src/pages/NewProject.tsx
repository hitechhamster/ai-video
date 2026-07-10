import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, type EffectPreset, type Music, type Style, type Template, type Voice } from "../api/client";

export default function NewProject() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const templateId = searchParams.get("template");

  const [styles, setStyles] = useState<Style[]>([]);
  const [effectPresets, setEffectPresets] = useState<EffectPreset[]>([]);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [voicesError, setVoicesError] = useState<string | null>(null);
  const [musicList, setMusicList] = useState<Music[]>([]);
  const [template, setTemplate] = useState<Template | null>(null);

  const [name, setName] = useState("");
  const [script, setScript] = useState("");
  const [styleId, setStyleId] = useState("");
  const [effectPresetId, setEffectPresetId] = useState("");
  const [voiceId, setVoiceId] = useState("");
  const [musicId, setMusicId] = useState<string>("");
  const [mode, setMode] = useState<"ppt_image" | "ai_video">("ppt_image");

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [showSaveTemplate, setShowSaveTemplate] = useState(false);
  const [templateName, setTemplateName] = useState("");
  const [savingTemplate, setSavingTemplate] = useState(false);
  const [templateSaved, setTemplateSaved] = useState(false);

  useEffect(() => {
    api.listMusic().then(setMusicList).catch(() => {});
    api.listEffectPresets().then(setEffectPresets).catch(() => {});

    if (templateId) {
      api.listTemplates().then((list) => {
        const t = list.find((x) => x.id === templateId) ?? null;
        setTemplate(t);
        if (t) {
          setStyleId(t.style_id);
          setVoiceId(t.voice_id);
          setMusicId(t.music_id ?? "");
          setEffectPresetId(t.effect_preset_id ?? "");
        }
      });
      return;
    }

    api.listStyles().then((list) => {
      setStyles(list);
      if (list.length > 0) setStyleId(list[0].id);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [templateId]);

  // 配音渠道跟着画风的生图渠道走，所以换画风要重新拉音色列表
  const selectedStyle = styles.find((s) => s.id === styleId);
  const styleProvider = selectedStyle?.image_provider;

  useEffect(() => {
    if (templateId || !styleProvider) return;
    setVoicesError(null);
    api
      .listVoices(styleProvider)
      .then((list) => {
        setVoices(list);
        setVoiceId(list.length > 0 ? list[0].voice_id : "");
      })
      .catch((e) => setVoicesError(e.message));
  }, [templateId, styleProvider]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !script.trim() || !styleId || !voiceId.trim()) {
      setError("请完整填写项目名称、脚本、画风与配音");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const project = await api.createProject({
        name,
        script,
        style_id: styleId,
        voice_id: voiceId,
        music_id: musicId || null,
        effect_preset_id: effectPresetId || null,
        template_id: templateId,
      });
      const { job_id } = await api.generateProject(project.id);
      navigate(`/projects/${project.id}?job=${job_id}`);
    } catch (e) {
      setError((e as Error).message);
      setSubmitting(false);
    }
  };

  const saveAsTemplate = async () => {
    if (!templateName.trim() || !styleId || !voiceId.trim()) return;
    setSavingTemplate(true);
    try {
      await api.createTemplate({
        name: templateName,
        style_id: styleId,
        voice_id: voiceId,
        music_id: musicId || null,
        effect_preset_id: effectPresetId || null,
      });
      setTemplateSaved(true);
      setShowSaveTemplate(false);
      setTemplateName("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSavingTemplate(false);
    }
  };

  if (templateId && !template) {
    return <p>加载模板中…</p>;
  }

  return (
    <form className="form new-project" onSubmit={submit}>
      <h2>{template ? `新建项目 · 来自模板「${template.name}」` : "自定义生成"}</h2>

      <label>
        项目名称
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="例如：为什么越长大越孤独" />
      </label>

      {template ? (
        <div className="template-locked">
          <span className="chip">🎨 {template.style_name}</span>
          <span className="chip">🗣️ {template.voice_id}</span>
          {template.music_name && <span className="chip">🎵 {template.music_name}</span>}
          {template.effect_preset_id && (
            <span className="chip">
              ✨ {effectPresets.find((p) => p.id === template.effect_preset_id)?.name ?? "效果预设"}
            </span>
          )}
          <button type="button" className="btn-link" onClick={() => navigate("/new")}>
            改用自定义搭配
          </button>
        </div>
      ) : (
        <>
          <label>
            选画风
            <div className="style-picker">
              {styles.map((s) => (
                <button
                  type="button"
                  key={s.id}
                  className={`style-pick ${styleId === s.id ? "active" : ""}`}
                  onClick={() => setStyleId(s.id)}
                >
                  {s.name}
                </button>
              ))}
            </div>
          </label>

          <label>
            选效果预设（字幕样式/特效/转场，可选）
            <div className="style-picker">
              <button
                type="button"
                className={`style-pick ${effectPresetId === "" ? "active" : ""}`}
                onClick={() => setEffectPresetId("")}
              >
                默认
              </button>
              {effectPresets.map((p) => (
                <button
                  type="button"
                  key={p.id}
                  className={`style-pick ${effectPresetId === p.id ? "active" : ""}`}
                  onClick={() => setEffectPresetId(p.id)}
                >
                  {p.name}
                </button>
              ))}
            </div>
          </label>

          <label>
            选配音
            {voicesError ? (
              <>
                <p className="error">
                  获取音色列表失败（{voicesError}），请检查后端 .env 里的{" "}
                  {styleProvider === "gemini" ? "GEMINI_API_KEY" : "MINIMAX_API_KEY"}
                  ，或直接手动输入 voice_id：
                </p>
                <input
                  value={voiceId}
                  onChange={(e) => setVoiceId(e.target.value)}
                  placeholder="例如：male-qn-qingse"
                />
              </>
            ) : (
              <select value={voiceId} onChange={(e) => setVoiceId(e.target.value)}>
                {voices.map((v) => (
                  <option key={v.voice_id} value={v.voice_id}>
                    {v.voice_name}
                  </option>
                ))}
              </select>
            )}
          </label>

          <label>
            背景音乐（可选）
            <select value={musicId} onChange={(e) => setMusicId(e.target.value)}>
              <option value="">不使用背景音乐</option>
              {musicList.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
            {musicList.length === 0 && (
              <p className="hint">
                还没有上传背景音乐，去「音乐库」页面上传后就能在这里选了
              </p>
            )}
          </label>
        </>
      )}

      <label>
        输入脚本（会按句号/问号/感叹号自动分段，每段对应一张分镜图）
        <textarea
          rows={8}
          value={script}
          onChange={(e) => setScript(e.target.value)}
          placeholder="在这里粘贴或输入你的口播文案…"
        />
      </label>

      <label>
        生成模式
        <div className="mode-picker">
          <button
            type="button"
            className={`style-pick ${mode === "ppt_image" ? "active" : ""}`}
            onClick={() => setMode("ppt_image")}
          >
            PPT图片模式
          </button>
          <button type="button" className="style-pick disabled" disabled title="即将推出">
            AI短片拼接模式（即将推出）
          </button>
        </div>
      </label>

      {error && <p className="error">{error}</p>}

      <div className="form-actions">
        <button className="btn" type="submit" disabled={submitting}>
          {submitting ? "创建中…" : "生成视频"}
        </button>

        {!template && !templateSaved && (
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => setShowSaveTemplate(true)}
            disabled={!styleId || !voiceId}
          >
            保存当前搭配为模板
          </button>
        )}
        {templateSaved && <span className="hint">✅ 已保存为模板，可在首页模板墙看到</span>}
      </div>

      {showSaveTemplate && (
        <div className="save-template-box">
          <input
            value={templateName}
            onChange={(e) => setTemplateName(e.target.value)}
            placeholder="模板名称，例如：外汇教学"
          />
          <button type="button" className="btn" onClick={saveAsTemplate} disabled={savingTemplate}>
            {savingTemplate ? "保存中…" : "确认保存"}
          </button>
        </div>
      )}
    </form>
  );
}
