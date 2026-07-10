import { useEffect, useState } from "react";
import { api, type Style, type StyleInput } from "../api/client";

const EMPTY_FORM: StyleInput = {
  name: "",
  prompt_suffix: "",
  negative_prompt: "",
  reference_image_url: "",
};

export default function StyleManager() {
  const [styles, setStyles] = useState<Style[]>([]);
  const [form, setForm] = useState<StyleInput>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [previewingId, setPreviewingId] = useState<string | null>(null);

  const load = () => api.listStyles().then(setStyles).catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, []);

  const generatePreview = async (id: string) => {
    setPreviewingId(id);
    setError(null);
    try {
      await api.previewStyle(id);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPreviewingId(null);
    }
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim() || !form.prompt_suffix.trim()) {
      setError("画风名称和风格提示词不能为空");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.createStyle(form);
      setForm(EMPTY_FORM);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const remove = async (id: string) => {
    if (!confirm("确定删除这个自定义画风吗？")) return;
    try {
      await api.deleteStyle(id);
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div className="style-manager">
      <section>
        <h2>画风预设</h2>
        <div className="style-grid">
          {styles.map((s) => {
            const thumbnailUrl = api.styleThumbnailUrl(s);
            return (
              <div key={s.id} className="style-card">
                {thumbnailUrl && (
                  <img className="style-thumb" src={thumbnailUrl} alt={`${s.name} 预览`} />
                )}
                <h4>
                  {s.name} {s.is_builtin && <span className="tag">内置</span>}
                </h4>
                <p>{s.prompt_suffix}</p>
                <div className="style-card-actions">
                  <button
                    type="button"
                    className="btn-link"
                    onClick={() => generatePreview(s.id)}
                    disabled={previewingId === s.id}
                  >
                    {previewingId === s.id ? "生成中…" : thumbnailUrl ? "重新生成预览" : "一键生成预览"}
                  </button>
                  {!s.is_builtin && (
                    <button type="button" className="btn-link danger" onClick={() => remove(s.id)}>
                      删除
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section>
        <h2>制作画风</h2>
        <form className="form" onSubmit={submit}>
          <label>
            画风名称
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="例如：赛博朋克火柴人"
            />
          </label>
          <label>
            风格提示词（会拼接到每段分镜画面提示词后面）
            <textarea
              rows={3}
              value={form.prompt_suffix}
              onChange={(e) => setForm({ ...form, prompt_suffix: e.target.value })}
              placeholder="例如：霓虹色彩，赛博朋克风格，火柴人剪影，故障艺术效果，竖版构图"
            />
          </label>
          <label>
            反向提示词（不希望出现的元素，可选）
            <input
              value={form.negative_prompt}
              onChange={(e) => setForm({ ...form, negative_prompt: e.target.value })}
              placeholder="例如：写实,照片,文字,水印,模糊"
            />
          </label>
          <label>
            参考图URL（可选，暂不参与生成，仅作展示）
            <input
              value={form.reference_image_url ?? ""}
              onChange={(e) => setForm({ ...form, reference_image_url: e.target.value })}
              placeholder="https://..."
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button className="btn" type="submit" disabled={saving}>
            {saving ? "保存中…" : "保存画风"}
          </button>
        </form>
      </section>
    </div>
  );
}
