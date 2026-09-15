import { useEffect, useState } from "react";
import { createClient, getClients } from "../api/endpoints";
import Pagination from "../components/Pagination";

const emptyForm = { full_name: "", birth_date: "", card_code: "", phone: "" };

export default function ClientsPage() {
  const [clients, setClients] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [createdInfo, setCreatedInfo] = useState(null);

  function load() {
    setLoading(true);
    getClients({ page, search: search || undefined })
      .then((data) => {
        setClients(data.results);
        setCount(data.count);
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, [page, search]);

  async function handleCreate(e) {
    e.preventDefault();
    setFormError("");
    setSubmitting(true);
    try {
      const payload = { ...form };
      if (!payload.birth_date) delete payload.birth_date;
      const created = await createClient(payload);
      setCreatedInfo(created);
      setForm(emptyForm);
      setShowForm(false);
      setPage(1);
      load();
    } catch (err) {
      const detail = err.response?.data;
      setFormError(
        typeof detail === "object" ? Object.values(detail).flat().join(" ") : "Xatolik yuz berdi."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      {createdInfo && (
        <div className="alert alert-success">
          Mijoz yaratildi: <strong>{createdInfo.full_name}</strong>. Vaqtinchalik parol:{" "}
          <strong>{createdInfo.generated_password}</strong> (buni mijozga yetkazing, keyin
          o'zgartirishi mumkin).{" "}
          <button className="btn" style={{ marginLeft: 10 }} onClick={() => setCreatedInfo(null)}>
            Yopish
          </button>
        </div>
      )}

      <div className="toolbar">
        <input
          placeholder="Qidirish: F.I.SH, telefon, karta"
          value={search}
          onChange={(e) => {
            setPage(1);
            setSearch(e.target.value);
          }}
          style={{ minWidth: 260 }}
        />
        <div className="spacer" />
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          + Yangi mijoz
        </button>
      </div>

      <div className="card">
        {loading ? (
          <div className="loading">Yuklanmoqda...</div>
        ) : clients.length === 0 ? (
          <div className="empty-state">Mijozlar topilmadi.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>F.I.SH</th>
                <th>Telefon</th>
                <th>Karta</th>
                <th>Tug'ilgan sana</th>
                <th>Telegram</th>
                <th>Ro'yxatdan o'tgan</th>
              </tr>
            </thead>
            <tbody>
              {clients.map((c) => (
                <tr key={c.id}>
                  <td>{c.full_name}</td>
                  <td>{c.phone}</td>
                  <td>{c.card_code}</td>
                  <td>{c.birth_date ?? "—"}</td>
                  <td>
                    {c.telegram_id ? (
                      <span className="badge badge-success">Ulangan</span>
                    ) : (
                      <span className="badge badge-muted">Ulanmagan</span>
                    )}
                  </td>
                  <td>{new Date(c.created_at).toLocaleDateString("uz-UZ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <Pagination page={page} setPage={setPage} count={count} />
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleCreate}>
            <h3>Yangi mijoz</h3>
            {formError && <div className="alert alert-danger">{formError}</div>}
            <div className="form-row">
              <label>F.I.SH</label>
              <input
                required
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label>Telefon (+998...)</label>
              <input
                required
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label>Karta raqami</label>
              <input
                required
                value={form.card_code}
                onChange={(e) => setForm({ ...form, card_code: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label>Tug'ilgan sana (ixtiyoriy)</label>
              <input
                type="date"
                value={form.birth_date}
                onChange={(e) => setForm({ ...form, birth_date: e.target.value })}
              />
            </div>
            <div className="form-actions">
              <button className="btn" type="button" onClick={() => setShowForm(false)}>
                Bekor qilish
              </button>
              <button className="btn btn-primary" type="submit" disabled={submitting}>
                {submitting ? "Saqlanmoqda..." : "Saqlash"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
