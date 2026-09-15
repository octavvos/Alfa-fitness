import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(username, password);
      navigate("/");
    } catch (err) {
      setError(
        err.response?.status === 401
          ? "Login yoki parol noto'g'ri."
          : err.message || "Kirishda xatolik yuz berdi."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-shell">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>Fitness klub</h1>
        <p>Administrator paneliga kirish</p>
        {error && <div className="alert alert-danger">{error}</div>}
        <input
          placeholder="Login"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoFocus
          required
        />
        <input
          type="password"
          placeholder="Parol"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button className="btn btn-primary" type="submit" disabled={submitting}>
          {submitting ? "Tekshirilmoqda..." : "Kirish"}
        </button>
      </form>
    </div>
  );
}
