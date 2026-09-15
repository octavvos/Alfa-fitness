import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Link } from "react-router-dom";
import { getAttendanceReport, getDailyReport, getExpiringReport } from "../api/endpoints";

function buildHourlyChartData(rows) {
  const byHour = Array.from({ length: 24 }, (_, hour) => ({ hour: `${hour}:00`, tashrif: 0 }));
  rows.forEach((row) => {
    byHour[row.hour].tashrif += row.total;
  });
  return byHour;
}

export default function DashboardPage() {
  const [daily, setDaily] = useState(null);
  const [expiring, setExpiring] = useState([]);
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getDailyReport(), getExpiringReport(7), getAttendanceReport()])
      .then(([d, e, a]) => {
        setDaily(d);
        setExpiring(e);
        setAttendance(a);
      })
      .catch(() => setError("Hisobotlarni yuklab bo'lmadi."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Yuklanmoqda...</div>;
  if (error) return <div className="alert alert-danger">{error}</div>;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div className="grid grid-cols-3">
        <div className="card stat-card">
          <div className="label">Bugungi tashriflar</div>
          <div className="value">{daily.visits_count}</div>
        </div>
        <div className="card stat-card">
          <div className="label">Bugungi yangi abonementlar</div>
          <div className="value">{daily.new_memberships}</div>
        </div>
        <div className="card stat-card">
          <div className="label">Bugungi sotuv summasi</div>
          <div className="value">{Number(daily.sales_sum).toLocaleString("uz-UZ")} so'm</div>
        </div>
      </div>

      <div className="card">
        <h3>So'nggi 7 kun — soat bo'yicha bandlik</h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={buildHourlyChartData(attendance)}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="hour" interval={2} fontSize={12} />
            <YAxis allowDecimals={false} fontSize={12} />
            <Tooltip />
            <Bar dataKey="tashrif" fill="#3457d5" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h3>7 kun ichida muddati tugaydigan abonementlar</h3>
        {expiring.length === 0 ? (
          <div className="empty-state">Hozircha yo'q.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Mijoz</th>
                <th>Tarif</th>
                <th>Tugash sanasi</th>
                <th>Qolgan kun</th>
              </tr>
            </thead>
            <tbody>
              {expiring.map((m) => (
                <tr key={m.id}>
                  <td>
                    <Link to="/memberships">{m.client.full_name}</Link>
                  </td>
                  <td>{m.plan.name}</td>
                  <td>{m.end_date}</td>
                  <td>{m.left_days}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
