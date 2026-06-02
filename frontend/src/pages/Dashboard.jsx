import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";

export default function Dashboard() {
  const { user } = useAuth();
  const [count, setCount] = useState(null);

  useEffect(() => {
    api.get("/api/payment-methods?page_size=1")
      .then((r) => setCount(r.data.total))
      .catch(() => {});
  }, []);

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Bienvenido, {user?.full_name}</h1>
      </div>

      <div className="card" style={{ marginBottom: "1rem" }}>
        <h2 className="card-title">Perfil</h2>
        <div className="detail-grid">
          <div className="detail-item">
            <label>Nombre</label>
            <p>{user?.full_name}</p>
          </div>
          <div className="detail-item">
            <label>Correo</label>
            <p>{user?.email}</p>
          </div>
          <div className="detail-item">
            <label>Estado</label>
            <p><span className="badge badge-active">Activo</span></p>
          </div>
          <div className="detail-item">
            <label>Miembro desde</label>
            <p>{user?.created_at ? new Date(user.created_at).toLocaleDateString("es-MX") : "—"}</p>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between" style={{ marginBottom: "1rem" }}>
          <h2 className="card-title" style={{ margin: 0 }}>Métodos de pago</h2>
          <Link to="/payment-methods/new" className="btn btn-primary btn-sm">+ Agregar</Link>
        </div>
        <p className="text-muted">
          {count === null ? "Cargando..." : `Tienes ${count} método${count !== 1 ? "s" : ""} de pago registrado${count !== 1 ? "s" : ""}.`}
        </p>
        <div className="mt-4">
          <Link to="/payment-methods" className="btn btn-ghost">Ver todos</Link>
        </div>
      </div>
    </div>
  );
}
