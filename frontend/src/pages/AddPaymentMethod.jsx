import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../services/api";

export default function AddPaymentMethod() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    type: "card",
    alias: "",
    institution: "",
    currency: "MXN",
    identifier: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await api.post("/api/payment-methods", form);
      navigate(`/payment-methods/${data.id}`);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg).join(", "));
      } else {
        setError(detail || "Error al guardar el método de pago");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 560 }}>
      <div className="page-header">
        <h1 className="page-title">Agregar método de pago</h1>
        <Link to="/payment-methods" className="btn btn-ghost btn-sm">← Volver</Link>
      </div>

      <div className="card">
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Tipo</label>
            <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
              <option value="card">Tarjeta</option>
              <option value="bank_account">Cuenta bancaria</option>
              <option value="clabe">CLABE</option>
              <option value="other">Otro</option>
            </select>
          </div>
          <div className="form-group">
            <label>Alias</label>
            <input
              type="text" required placeholder="Ej. Mi Visa Platinum"
              value={form.alias}
              onChange={(e) => setForm({ ...form, alias: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Institución</label>
            <input
              type="text" required placeholder="Ej. BBVA, Banorte, HSBC"
              value={form.institution}
              onChange={(e) => setForm({ ...form, institution: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Moneda</label>
            <select value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })}>
              <option value="MXN">MXN — Peso mexicano</option>
              <option value="USD">USD — Dólar americano</option>
              <option value="EUR">EUR — Euro</option>
            </select>
          </div>
          <div className="form-group">
            <label>
              {form.type === "card" ? "Número de tarjeta" :
               form.type === "clabe" ? "CLABE interbancaria" :
               form.type === "bank_account" ? "Número de cuenta" : "Identificador"}
            </label>
            <input
              type="text" required
              placeholder={
                form.type === "card" ? "16 dígitos" :
                form.type === "clabe" ? "18 dígitos" : "Identificador del método"
              }
              value={form.identifier}
              onChange={(e) => setForm({ ...form, identifier: e.target.value })}
            />
            <p className="text-muted mt-1">Este dato se almacenará de forma cifrada.</p>
          </div>
          <div className="flex gap-2">
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? "Guardando..." : "Guardar método de pago"}
            </button>
            <Link to="/payment-methods" className="btn btn-ghost">Cancelar</Link>
          </div>
        </form>
      </div>
    </div>
  );
}
