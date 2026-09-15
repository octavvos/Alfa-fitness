import { useEffect, useState } from "react";
import { getAccessLogs } from "../api/endpoints";
import Pagination from "../components/Pagination";

const RESULT_LABELS = {
  ruxsat: { text: "Ruxsat", cls: "badge-success" },
  muddati_tugagan: { text: "Muddati tugagan", cls: "badge-warning" },
  muzlatilgan: { text: "Muzlatilgan", cls: "badge-warning" },
  limit_tugagan: { text: "Limit tugagan", cls: "badge-warning" },
  topilmadi: { text: "Topilmadi", cls: "badge-danger" },
};

export default function AccessLogsPage() {
  const [logs, setLogs] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getAccessLogs({ page, result: result || undefined })
      .then((data) => {
        setLogs(data.results);
        setCount(data.count);
      })
      .finally(() => setLoading(false));
  }, [page, result]);

  return (
    <div>
      <div className="toolbar">
        <select value={result} onChange={(e) => { setPage(1); setResult(e.target.value); }}>
          <option value="">Barcha natijalar</option>
          <option value="ruxsat">Ruxsat</option>
          <option value="muddati_tugagan">Muddati tugagan</option>
          <option value="muzlatilgan">Muzlatilgan</option>
          <option value="limit_tugagan">Limit tugagan</option>
          <option value="topilmadi">Topilmadi</option>
        </select>
      </div>

      <div className="card">
        {loading ? (
          <div className="loading">Yuklanmoqda...</div>
        ) : logs.length === 0 ? (
          <div className="empty-state">Yozuvlar topilmadi.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Token</th>
                <th>Natija</th>
                <th>Vaqt</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => {
                const info = RESULT_LABELS[l.result] ?? { text: l.result, cls: "badge-muted" };
                return (
                  <tr key={l.id}>
                    <td>
                      <code>{l.qr_token.slice(0, 8)}…</code>
                    </td>
                    <td>
                      <span className={`badge ${info.cls}`}>{info.text}</span>
                    </td>
                    <td>{new Date(l.created_at).toLocaleString("uz-UZ")}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
        <Pagination page={page} setPage={setPage} count={count} />
      </div>
    </div>
  );
}
