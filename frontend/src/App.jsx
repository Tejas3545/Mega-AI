import { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const STREAM_ID = "default-stream";

export default function App() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [running, setRunning] = useState(false);
  const [rois, setRois] = useState([]);
  const streamUrl = useMemo(() => `${API_BASE}/api/v1/stream/${STREAM_ID}/video`, []);

  useEffect(() => {
    let interval;
    let media;

    async function start() {
      media = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      videoRef.current.srcObject = media;
      await videoRef.current.play();

      interval = setInterval(async () => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(async (blob) => {
          if (!blob) return;
          const form = new FormData();
          form.append("stream_id", STREAM_ID);
          form.append("timestamp_ms", String(Date.now()));
          form.append("frame", blob, "frame.jpg");
          await fetch(`${API_BASE}/api/v1/stream/frame`, { method: "POST", body: form });
        }, "image/jpeg", 0.8);
      }, 150);
    }

    if (running) {
      start();
    }

    return () => {
      if (interval) clearInterval(interval);
      if (media) media.getTracks().forEach((t) => t.stop());
    };
  }, [running]);

  useEffect(() => {
    const timer = setInterval(async () => {
      const res = await fetch(`${API_BASE}/api/v1/stream/${STREAM_ID}/rois`);
      if (res.ok) {
        const data = await res.json();
        setRois(data.slice(0, 10));
      }
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <main className="page">
      <h1>Mega AI Real-Time Face Detection</h1>
      <div className="controls">
        <button onClick={() => setRunning((x) => !x)}>{running ? "Stop" : "Start"} Camera Stream</button>
      </div>

      <section className="grid">
        <div>
          <h2>Camera Input</h2>
          <video ref={videoRef} className="video" muted playsInline />
          <canvas ref={canvasRef} style={{ display: "none" }} />
        </div>

        <div>
          <h2>Processed Feed (ROI Drawn by Backend)</h2>
          <img className="video" src={streamUrl} alt="Processed Stream" />
        </div>
      </section>

      <section>
        <h2>Recent ROI Data</h2>
        <table>
          <thead>
            <tr>
              <th>Frame</th><th>X</th><th>Y</th><th>W</th><th>H</th><th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {rois.map((r) => (
              <tr key={r.id}>
                <td>{r.frame_number}</td><td>{r.x}</td><td>{r.y}</td><td>{r.width}</td><td>{r.height}</td><td>{r.confidence.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
