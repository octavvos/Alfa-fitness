import { useEffect, useState } from "react";
import {
  cancelMembership,
  createMembership,
  freezeMembership,
  getClients,
  getMemberships,
  getPlans,
} from "../api/endpoints";
import Pagination from "../components/Pagination";
import StatusBadge from "../components/StatusBadge";

function ClientPicker({ value, onChange }) {
  const [query, setQuery] = useState("");
  const [options, setOptions] = useState([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!query) {
      setOptions([]);
      return;
    }
    const timer = setTimeout(() => {
      getClients({ search: query }).then((data) => setOptions(data.results));
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  return (
    <div style={{ position: "relative" }}>
      <input
        placeholder="F.I.SH, telefon yoki karta bo'yicha qidiring"
        value={value ? value.full_name : query}
        onChange={(e) => {
          onChange(null);
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
      />
      {open && options.length > 0 && (
        <div
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            background: "#fff",
            border: "1px solid var(--border)",
            borderRadius: 8,
            marginTop: 4,
            zIndex: 10,
            maxHeight: 180,
            overflowY: "auto",
          }}
        >
          {options.map((c) => (
            <div
              key={c.id}
              style={{ padding: "8px 12px", cursor: "pointer" }}
              onMouseDown={() => {
                onChange(c);
                setQuery("");
                setOpen(false);
              }}
            >
              {c.full_name} — {c.phone} ({c.card_code})
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function MembershipsPage() {
  const [memberships, setMemberships] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  const [showSellForm, setShowSellForm] = useState(false);
  const [selectedClient, setSelectedClient] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState("");
  const [startDate, setStartDate] = useState("");
  const [sellError, setSellError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [freezeTarget, setFreezeTarget] = useState(null);
  const [freezeForm, setFreezeForm] = useState({ start_date: "", days: "", reason: "" });
  const [freezeError, setFreezeError] = useState("");

  function load() {
    setLoading(true);
    getMemberships({ page, status: statusFilter || undefined })
      .then((data) => {
        setMemberships(data.results);
        setCount(data.count);
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, [page, statusFilter]);
  useEffect(() => {
    getPlans({ is_active: true }).then((data) => setPlans(data.results ?? data));
  }, []);

  async function handleSell(e) {
    e.preventDefault();
    setSellError("");
    if (!selectedClient || !selectedPlan) {
      setSellError("Mijoz va tarifni tanlang.");
      return;
    }
    setSubmitting(true);
    try {
      const payload = { client: selectedClient.id, plan: Number(selectedPlan) };
      if (startDate) payload.start_date = startDate;
      await createMembership(payload);
      setShowSellForm(false);
      setSelectedClient(null);
      setSelectedPlan("");
      setStartDate("");
      setPage(1);
      load();
    } catch (err) {
      const detail = err.response?.data;
      setSellError(
        typeof detail === "object" ? Object.values(detail).flat().join(" ") : "Xatolik yuz berdi."
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleFreeze(e) {
    e.preventDefault();
    setFreezeError("");
    try {
      await freezeMembership(freezeTarget.id, {
        start_date: freezeForm.start_date,
        days: Number(freezeForm.days),
        reason: freezeForm.reason,
      });
      setFreezeTarget(null);
      setFreezeForm({ start_date: "", days: "", reason: "" });
      load();
    } catch (err) {
      const detail = err.response?.data;
      setFreezeError(
        typeof detail === "object" ? Object.values(detail).flat().join(" ") : "Xatolik yuz berdi."
      );
    }
  }

  async function handleCancel(m) {
    if (!window.confirm(`${m.client.full_name} abonementini bekor qilasizmi?`)) return;
    await cancelMembership(m.id);
    load();
  }

  return (
    <div>
      <div className="toolbar">
        <select value={statusFilter} onChange={(e) => { setPage(1); setStatusFilter(e.target.value); }}>
          <option value="">Barcha statuslar</option>
          <option value="faol">Faol</option>
          <option value="muzlatilgan">Muzlatilgan</option>
          <option value="tugagan">Tugagan</option>
          <option value="bekor">Bekor qilingan</option>
        </select>
        <div className="spacer" />
        <button className="btn btn-primary" onClick={() => setShowSellForm(true)}>
          + Abonement sotish
        </button>
      </div>

      <div className="card">
        {loading ? (
          <div className="loading">Yuklanmoqda...</div>
        ) : memberships.length === 0 ? (
          <div className="empty-state">Abonementlar topilmadi.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Mijoz</th>
                <th>Tarif</th>
                <th>Boshlanish</th>
                <th>Tugash</th>
                <th>Tashrif</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {memberships.map((m) => (
                <tr key={m.id}>
                  <td>{m.client.full_name}</td>
                  <td>{m.plan.name}</td>
                  <td>{m.start_date}</td>
                  <td>{m.end_date}</td>
                  <td>
                    {m.visits_used}
                    {m.left_visits !== null ? ` / ${m.plan.visit_limit}` : ""}
                  </td>
                  <td>
                    <StatusBadge status={m.status} />
                  </td>
                  <td style={{ display: "flex", gap: 6 }}>
                    {m.status === "faol" && (
                      <>
                        <button className="btn" onClick={() => setFreezeTarget(m)}>
                          Muzlatish
                        </button>
                        <button className="btn btn-danger" onClick={() => handleCancel(m)}>
                          Bekor qilish
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <Pagination page={page} setPage={setPage} count={count} />
      </div>

      {showSellForm && (
        <div className="modal-overlay" onClick={() => setShowSellForm(false)}>
          <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSell}>
            <h3>Abonement sotish</h3>
            {sellError && <div className="alert alert-danger">{sellError}</div>}
            <div className="form-row">
              <label>Mijoz</label>
              <ClientPicker value={selectedClient} onChange={setSelectedClient} />
            </div>
            <div className="form-row">
              <label>Tarif</label>
              <select required value={selectedPlan} onChange={(e) => setSelectedPlan(e.target.value)}>
                <option value="">Tanlang...</option>
                {plans.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} — {Number(p.price).toLocaleString("uz-UZ")} so'm
                  </option>
                ))}
              </select>
            </div>
            <div className="form-row">
              <label>Boshlanish sanasi (bo'sh = bugun)</label>
              <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </div>
            <div className="form-actions">
              <button className="btn" type="button" onClick={() => setShowSellForm(false)}>
                Bekor qilish
              </button>
              <button className="btn btn-primary" type="submit" disabled={submitting}>
                {submitting ? "Saqlanmoqda..." : "Sotish"}
              </button>
            </div>
          </form>
        </div>
      )}

      {freezeTarget && (
        <div className="modal-overlay" onClick={() => setFreezeTarget(null)}>
          <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleFreeze}>
            <h3>Muzlatish — {freezeTarget.client.full_name}</h3>
            <p className="muted">
              Qolgan muzlatish kuni: <strong>{freezeTarget.freeze_days_left}</strong>
            </p>
            {freezeError && <div className="alert alert-danger">{freezeError}</div>}
            <div className="form-row">
              <label>Boshlanish sanasi</label>
              <input
                required
                type="date"
                value={freezeForm.start_date}
                onChange={(e) => setFreezeForm({ ...freezeForm, start_date: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label>Necha kun</label>
              <input
                required
                type="number"
                min="1"
                value={freezeForm.days}
                onChange={(e) => setFreezeForm({ ...freezeForm, days: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label>Sababi</label>
              <input
                required
                value={freezeForm.reason}
                onChange={(e) => setFreezeForm({ ...freezeForm, reason: e.target.value })}
              />
            </div>
            <div className="form-actions">
              <button className="btn" type="button" onClick={() => setFreezeTarget(null)}>
                Bekor qilish
              </button>
              <button className="btn btn-primary" type="submit">
                Tasdiqlash
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
