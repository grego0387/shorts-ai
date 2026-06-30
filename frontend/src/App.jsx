import { useState, useEffect, useRef } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const PLATFORMS = [
  { id: "youtube", label: "YouTube Shorts", color: "#FF0000" },
  { id: "tiktok", label: "TikTok", color: "#000000" },
  { id: "instagram", label: "Instagram Reels", color: "#E1306C" },
];

export default function App() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [job, setJob] = useState(null);
  const [selected, setSelected] = useState(new Set());
  const [activePlatforms, setActivePlatforms] = useState(new Set(["youtube", "tiktok", "instagram"]));
  const [publishing, setPublishing] = useState(false);
  const [published, setPublished] = useState(false);
  const pollRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!jobId) return;
    pollRef.current = setInterval(async () => {
      const res = await fetch(`${API_URL}/status/${jobId}`);
      const data = await res.json();
      setJob(data);
      if (data.status === "done" || data.status === "error") {
        clearInterval(pollRef.current);
      }
    }, 2000);
    return () => clearInterval(pollRef.current);
  }, [jobId]);

  const handleFileSelect = (e) => {
    const f = e.target.files[0];
    if (f) setFile(f);
  };

  const upload = async () => {
    if (!file) return;
    setUploading(true);
    setJob(null); setSelected(new Set()); setPublished(false);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      setJobId(data.job_id);
      setJob({ status: "analyzing", clips: [] });
    } catch (err) {
      setJob({ status: "error", error: "No se pudo subir el video", clips: [] });
    }
    setUploading(false);
  };

  const toggleClip = (id) => {
    setSelected(prev => {
      const s = new Set(prev);
      s.has(id) ? s.delete(id) : s.add(id);
      return s;
    });
  };

  const togglePlatform = (id) => {
    setActivePlatforms(prev => {
      const s = new Set(prev);
      s.has(id) ? s.delete(id) : s.add(id);
      return s;
    });
  };

  const downloadClip = (clip) => {
    const a = document.createElement("a");
    a.href = `${API_URL}/download/${jobId}/${clip.id}`;
    a.download = `${clip.title}.mp4`;
    a.click();
  };

  const publish = async () => {
    setPublishing(true);
    await new Promise(r => setTimeout(r, 2000));
    setPublishing(false);
    setPublished(true);
  };

  const reset = () => {
    setFile(null); setJobId(null); setJob(null);
    setSelected(new Set()); setPublished(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const statusLabel = {
    analyzing: "🤖 IA analizando momentos...",
    cutting: "✂️ Cortando clips...",
    done: "✅ ¡Clips listos!",
    error: "❌ Error procesando el video"
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f5f5f7", padding: "2rem 1rem", fontFamily: "system-ui, sans-serif" }}>
      <div style={{ maxWidth: 640, margin: "0 auto" }}>

        <div style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 22, fontWeight: 600, color: "#1d1d1f", margin: 0 }}>⚡ Shorts AI</h1>
          <p style={{ fontSize: 14, color: "#6e6e73", margin: "4px 0 0" }}>Sube tu video, la IA detecta los mejores momentos</p>
        </div>

        <div style={card}>
          <div style={stepLabel}>Paso 1 — Sube tu video</div>

          <div
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: "2px dashed #d1d1d6",
              borderRadius: 12,
              padding: "2rem 1rem",
              textAlign: "center",
              cursor: "pointer",
              background: file ? "#f0effe" : "#fafafa"
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              onChange={handleFileSelect}
              style={{ display: "none" }}
            />
            {file ? (
              <div>
                <p style={{ fontSize: 14, fontWeight: 500, color: "#1d1d1f", margin: 0 }}>🎬 {file.name}</p>
                <p style={{ fontSize: 12, color: "#6e6e73", margin: "4px 0 0" }}>{(file.size / (1024*1024)).toFixed(1)} MB · Haz clic para cambiar</p>
              </div>
            ) : (
              <div>
                <p style={{ fontSize: 32, margin: 0 }}>📹</p>
                <p style={{ fontSize: 14, color: "#1d1d1f", margin: "8px 0 0", fontWeight: 500 }}>Haz clic para seleccionar un video</p>
                <p style={{ fontSize: 12, color: "#6e6e73", margin: "4px 0 0" }}>MP4, MOV, AVI — hasta 500MB</p>
              </div>
            )}
          </div>

          {file && (!job || job.status === "error") && (
            <button onClick={upload} style={{ ...btnPrimary, width: "100%", marginTop: 12 }} disabled={uploading}>
              {uploading ? "Subiendo..." : "🚀 Analizar video"}
            </button>
          )}

          {job && job.status !== "done" && job.status !== "error" && (
            <div style={{ marginTop: 12 }}>
              <div style={{ height: 4, background: "#e5e5ea", borderRadius: 2, overflow: "hidden" }}>
                <div style={{ height: "100%", background: "#534AB7", borderRadius: 2, width: job.status === "analyzing" ? "50%" : "85%", transition: "width 0.5s" }} />
              </div>
              <p style={{ fontSize: 12, color: "#6e6e73", marginTop: 6 }}>{statusLabel[job.status]}</p>
            </div>
          )}

          {job?.status === "error" && (
            <p style={{ fontSize: 13, color: "#ff3b30", marginTop: 8 }}>❌ {job.error}</p>
          )}
        </div>

        {job?.status === "done" && job.clips.length > 0 && !published && (
          <div style={card}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <div style={stepLabel}>Paso 2 — Selecciona los clips</div>
              <button onClick={() => setSelected(new Set(job.clips.map(c => c.id)))} style={btnGhost}>
                Todos
              </button>
            </div>

            {job.clips.map(clip => (
              <div
                key={clip.id}
                onClick={() => toggleClip(clip.id)}
                style={{
                  ...clipRow,
                  border: selected.has(clip.id) ? "2px solid #534AB7" : "1px solid #e5e5ea",
                  background: selected.has(clip.id) ? "#f0effe" : "#fff"
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{ width: 44, height: 44, background: "#e5e5ea", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, flexShrink: 0 }}>
                    🎬
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: 14, fontWeight: 500, color: "#1d1d1f", margin: 0, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{clip.title}</p>
                    <p style={{ fontSize: 12, color: "#6e6e73", margin: "2px 0 0" }}>{clip.start}s – {clip.end}s · {clip.end - clip.start}s</p>
                    <p style={{ fontSize: 11, color: "#8e8e93", margin: "2px 0 0" }}>{clip.reason}</p>
                  </div>
                  <div style={{ background: "#534AB7", color: "#fff", fontSize: 12, fontWeight: 600, padding: "3px 8px", borderRadius: 6, flexShrink: 0 }}>
                    {clip.score}%
                  </div>
                </div>
                <button
                  onClick={e => { e.stopPropagation(); downloadClip(clip); }}
                  style={{ ...btnGhost, marginTop: 8, fontSize: 12 }}
                >
                  ⬇️ Descargar este clip
                </button>
              </div>
            ))}

            <div style={{ marginTop: 20 }}>
              <div style={stepLabel}>Paso 3 — Publicar en</div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
                {PLATFORMS.map(p => (
                  <button
                    key={p.id}
                    onClick={() => togglePlatform(p.id)}
                    style={{
                      ...btnGhost,
                      borderColor: activePlatforms.has(p.id) ? "#534AB7" : "#e5e5ea",
                      background: activePlatforms.has(p.id) ? "#f0effe" : "#fff",
                      color: activePlatforms.has(p.id) ? "#3C3489" : "#1d1d1f",
                      display: "flex", alignItems: "center", gap: 6
                    }}
                  >
                    <span style={{ width: 8, height: 8, borderRadius: "50%", background: p.color, display: "inline-block" }} />
                    {p.label}
                  </button>
                ))}
              </div>

              <div style={{ display: "flex", gap: 8 }}>
                <button onClick={publish} style={{ ...btnPrimary, flex: 1 }} disabled={selected.size === 0 || publishing}>
                  {publishing ? "Publicando..." : `🚀 Publicar ${selected.size} clip${selected.size !== 1 ? "s" : ""}`}
                </button>
              </div>
              {selected.size === 0 && <p style={{ fontSize: 12, color: "#ff9500", marginTop: 6 }}>Selecciona al menos un clip</p>}
            </div>
          </div>
        )}

        {published && (
          <div style={card}>
            <p style={{ fontSize: 16, fontWeight: 600, color: "#34c759", margin: "0 0 12px" }}>✅ ¡Publicado exitosamente!</p>
            {[...activePlatforms].map(pid => {
              const p = PLATFORMS.find(x => x.id === pid);
              return (
                <div key={pid} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, padding: "6px 0", borderBottom: "1px solid #f2f2f7" }}>
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ width: 8, height: 8, borderRadius: "50%", background: p.color, display: "inline-block" }} />
                    {p.label}
                  </span>
                  <span style={{ color: "#34c759" }}>{selected.size} clips</span>
                </div>
              );
            })}
            <button onClick={reset} style={{ ...btnGhost, marginTop: 14, width: "100%" }}>🔄 Procesar otro video</button>
          </div>
        )}

      </div>
    </div>
  );
}

const card = { background: "#fff", borderRadius: 14, padding: "1.25rem", marginBottom: "1rem", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" };
const stepLabel = { fontSize: 11, fontWeight: 600, color: "#8e8e93", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 10 };
const btnPrimary = { height: 40, padding: "0 18px", borderRadius: 10, border: "none", background: "#534AB7", color: "#fff", fontSize: 14, fontWeight: 500, cursor: "pointer", whiteSpace: "nowrap" };
const btnGhost = { padding: "6px 12px", borderRadius: 8, border: "1px solid #e5e5ea", background: "#fff", fontSize: 13, cursor: "pointer", color: "#1d1d1f" };
const clipRow = { borderRadius: 10, padding: "10px 12px", marginBottom: 8, cursor: "pointer", transition: "all 0.15s" };
