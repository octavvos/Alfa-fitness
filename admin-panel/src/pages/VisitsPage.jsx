import { useEffect, useState } from "react";
import { getVisits } from "../api/endpoints";
import Pagination from "../components/Pagination";

export default function VisitsPage() {
  const [visits, setVisits] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getVisits({ page, date_from: dateFrom || undefined, date_to: dateTo || undefined })
      .then((data) => {
        setVisits(data.results);
        setCount(data.count);
      })
      .finally(() => setLoading(false));
  }, [page, dateFrom, dateTo]);

  return (
    <div>
      <div className="toolbar">
        <label className="muted">Dan:</label>
        <input type="date" value={dateFrom} onChange={(e) => { setPage(1); setDateFrom(e.target.value); }} />
        <label className="muted">Gacha:</label>
        <input type="date" value={dateTo} onChange={(e) => { setPage(1); setDateTo(e.target.value); }} />
      </div>

      <div className="card">
        {loading ? (
          <div className="loading">Yuklanmoqda...</div>
        ) : visits.length === 0 ? (
          <div className="empty-state">Tashriflar topilmadi.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Mijoz</th>
                <th>Kirish vaqti</th>
              </tr>
            </thead>
            <tbody>
              {visits.map((v) => (
                <tr key={v.id}>
                  <td>{v.client}</td>
                  <td>{new Date(v.checked_in_at).toLocaleString("uz-UZ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <Pagination page={page} setPage={setPage} count={count} />
      </div>
    </div>
  );
}
