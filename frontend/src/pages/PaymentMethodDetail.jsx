import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "../services/api";

const TYPE_LABELS = {
  card: "Tarjeta",
  bank_account: "Cuenta bancaria",
  clabe: "CLABE",
  other: "Otro",
};

export default function PaymentMethodDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [pm, setPm] = useState(null);
  const [error, setError] = useState("");
  const [confirm, setConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    api.get(`/api/payment-methods/${id}`)
      .then((r) => setPm(r.data))
      .catch((err) => {
        if (err.response?.status === 404) setError("Método de pago no encontrado");
        else setError("Error al cargar el método de pago");
      });
  }, [id]);

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await api.delete(`/api/payment-methods/${id}`);
      navigate("/payment-methods");
    } catch (err) {
      setError(err.response?.data?.detail || "Error al desactivar");
      setDeleting(false);
      setConfirm(false);
    }
  };

  if (error) return (
    <div>
      <div className="alert alert-error">{error}</div>
      <Link to="/payment-methods" className="btn btn-ghost">← Volver</Link>
    </div>
  );

  if (!pm) return <p className="text-muted">Cargando...</p>;

  return (
    <div style={{ maxWidth: 600 }}>
      <div className="page-header">
        <h1 className="page-title">{pm.alias}</h1>
        <Link to="/payment-methods" className="btn btn-ghost btn-sm">← Volver</Link>
      </div>

      <div className="card">
        <div className="detail-grid">
          <div className="detail-item">
            <label>Tipo</label>
            <p><span className="type-label">{TYPE_LABELS[pm.type] || pm.type}</span></p>
          </div>
          <div className="detail-item">
            <label>Estado</label>
            <p><span className={`badge badge-${pm.status}`}>{pm.status === "active" ? "Activo" : "Inactivo"}</span></p>
          </div>
          <div className="detail-item">
            <label>Institución</label>
            <p>{pm.institution}</p>
          </div>
          <div className="detail-item">
            <label>Moneda</label>
            <p>{pm.currency}</p>
          </div>
          <div className="detail-item" style={{ gridColumn: "span 2" }}>
            <label>Identificador</label>
            <p style={{ fontFamily: "monospace", fontSize: "1.1rem", letterSpacing: ".1em" }}>
              {pm.identifier_masked}
            </p>
          </div>
          <div className="detail-item">
            <label>Registrado</label>
            <p>{new Date(pm.created_at).toLocaleString("es-MX")}</p>
          </div>
          <div className="detail-item">
            <label>Actualizado</label>
            <p>{new Date(pm.updated_at).toLocaleString("es-MX")}</p>
          </div>
        </div>
      </div>

      {pm.status === "active" && (
        <div className="card" style={{ borderLeft: "3px solid var(--danger)" }}>
          <h3 style={{ marginBottom: ".5rem", color: "var(--danger)" }}>Desactivar método de pago</h3>
          <p className="text-muted" style={{ marginBottom: "1rem" }}>
            Esta acción desactivará el método de pago. No se eliminará permanentemente.
          </p>
          {!confirm ? (
            <button className="btn btn-danger btn-sm" onClick={() => setConfirm(true)}>
              Desactivar
            </button>
          ) : (
            <div className="flex gap-2 items-center">
              <span className="text-muted" style={{ fontSize: ".9rem" }}>¿Confirmas la desactivación?</span>
              <button className="btn btn-danger btn-sm" onClick={handleDelete} disabled={deleting}>
                {deleting ? "Desactivando..." : "Sí, desactivar"}
              </button>
              <button className="btn btn-ghost btn-sm" onClick={() => setConfirm(false)}>Cancelar</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
