import { useEffect, useState } from "react";
import { createPlan, getPlans, updatePlan } from "../api/endpoints";

const emptyForm = {
  name: "",
  duration_days: 30,
  visit_limit: "",
  daily_limit: 1,
  price: "",
  freeze_days: 0,
};

export default function PlansPage() {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function load() {
    setLoading(true);
    getPlans().then((data) => setPlans(data.results ?? data)).finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleCreate(e) {
    e.preventDefault();
    setFormError("");
    setSubmitting(true);
    try {
      const payload = { ...form, visit_limit: form.visit_limit === "" ? null : Number(form.visit_limit) };
      await createPlan(payload);
      setForm(emptyForm);
      setShowForm(false);
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

  async function toggleActive(plan) {
    await updatePlan(plan.id, { is_active: !plan.is_active });
    load();
  }

  return (
    <div>
      <div className="toolbar">
        <div className="spacer" />
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          + Yangi tarif
        </button>
      </div>

      <div className="card">
        {loading ? (
          <div className="loading">Yuklanmoqda...</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Nomi</th>
                <th>Muddat (kun)</th>
                <th>Tashrif limiti</th>
                <th>Kunlik limit</th>
                <th>Narxi</th>
                <th>Muzlatish (kun)</th>
                <th>Holati</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {plans.map((p) => (
                <tr key={p.id}>
                  <td>{p.name}</td>
                  <td>{p.duration_days}</td>
                  <td>{p.visit_limit ?? "Cheksiz"}</td>
                  <td>{p.daily_limit}</td>
                  <td>{Number(p.price).toLocaleString("uz-UZ")} so'm</td>
                  <td>{p.freeze_days}</td>
                  <td>
                    {p.is_active ? (
                      <span className="badge badge-success">Faol</span>
                    ) : (
                      <span className="badge badge-muted">O'chirilgan</span>
                    )}
                  </td>
                  <td>
                    <button className="btn" onClick={() => toggleActive(p)}>
                      {p.is_active ? "O'chirish" : "Yoqish"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleCreate}>
            <h3>Yangi tarif</h3>
            {formError && <div className="alert alert-danger">{formError}</div>}
            <div className="form-row">
              <label>Nomi</label>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="form-row">
              <label>Muddati (kun)</label>
              <input
                required
                type="number"
                min="1"
                value={form.duration_days}
                onChange={(e) => setForm({ ...form, duration_days: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label>Jami tashrif limiti (bo'sh = cheksiz)</label>
              <input
                type="number"
                min="1"
                value={form.visit_limit}
                onChange={(e) => setForm({ ...form, visit_limit: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label>Kunlik limit</label>
              <input
                required
                type="number"
                min="1"
                value={form.daily_limit}
                onChange={(e) => setForm({ ...form, daily_limit: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label>Narxi (so'm)</label>
              <input
                required
                type="number"
                min="0"
                value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label>Muzlatish uchun ruxsat etilgan kunlar</label>
              <input
                type="number"
                min="0"
                value={form.freeze_days}
                onChange={(e) => setForm({ ...form, freeze_days: e.target.value })}
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
