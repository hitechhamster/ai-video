import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, type Template } from "../api/client";

const GRADIENTS = [
  "linear-gradient(135deg, #7c3aed, #ec4899)",
  "linear-gradient(135deg, #2563eb, #7c3aed)",
  "linear-gradient(135deg, #059669, #2563eb)",
  "linear-gradient(135deg, #ea580c, #ec4899)",
  "linear-gradient(135deg, #0891b2, #7c3aed)",
];

const ICONS = ["🕺", "🎬", "🎨", "🎵", "✨", "📈", "💬"];

function pick<T>(arr: T[], seed: string): T {
  const sum = [...seed].reduce((acc, c) => acc + c.charCodeAt(0), 0);
  return arr[sum % arr.length];
}

export default function TemplateGallery() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api
      .listTemplates()
      .then(setTemplates)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>加载中…</p>;
  if (error) return <p className="error">加载失败：{error}</p>;

  return (
    <div className="template-gallery">
      <div className="gallery-header">
        <div>
          <h2>选一个模板开始</h2>
          <p className="hint">画风、配音、背景音乐都已经配好，只需要填脚本</p>
        </div>
        <Link className="btn btn-ghost" to="/new">
          自定义生成 →
        </Link>
      </div>

      <div className="template-grid">
        {templates.map((t) => (
          <div
            key={t.id}
            className="template-card"
            style={{ background: pick(GRADIENTS, t.id) }}
            onClick={() => navigate(`/new?template=${t.id}`)}
          >
            <div className="template-icon">{pick(ICONS, t.name)}</div>
            <h3>{t.name}</h3>
            <p>{t.description}</p>
            <div className="template-meta">
              <span>🎨 {t.style_name}</span>
              {t.music_name && <span>🎵 {t.music_name}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
