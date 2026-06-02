import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";

const TYPE_LABELS = {
  card: "Tarjeta",
  bank_account: "Cuenta bancaria",
  clabe: "CLABE",
  other: "Otro",
};

export default function PaymentMethods() {
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState("");

  const fetch = (p = page) => {
    const params = new URLSearchParams({ page: p, page_size: 10 });
    if (typeFilter) params.append("type_filter", typeFilter);
    if (statusFilter) params.append("status_filter", statusFilter);
    api.get(`/api/payment-methods?${params}`)
      .then((r) => setData(r.data))
      .catch(() => setError("Error al cargar los métodos de pago"));
  };

  useEffect(() => { fetch(1); setPage(1); }, [typeFilter, statusFilter]);
  useEffect(() => { fetch(page); }, [page]);

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Métodos de pago</h1>
        <Link to="/payment-methods/new" className="btn btn-primary">+ Agregar</Link>
      </div>

      <div className="card" style={{ padding: "1rem", marginBottom: "1rem" }}>
        <div className="flex gap-2">
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} style={{ padding: ".4rem .6rem", border: "1px solid var(--gray-200)", borderRadius: "var(--radius)" }}>
            <option value="">Todos los tipos</option>
            <option value="card">Tarjeta</option>
            <option value="bank_account">Cuenta bancaria</option>
            <option value="clabe">CLABE</option>
            <option value="other">Otro</option>
          </select>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{ padding: ".4rem .6rem", border: "1px solid var(--gray-200)", borderRadius: "var(--radius)" }}>
            <option value="">Todos los estados</option>
            <option value="active">Activo</option>
            <option value="inactive">Inactivo</option>
          </select>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {!data ? (
        <p className="text-muted">Cargando...</p>
      ) : data.total === 0 ? (
        <div className="card">
          <p className="text-muted" style={{ textAlign: "center", padding: "2rem 0" }}>
            No tienes métodos de pago registrados.{" "}
            <Link to="/payment-methods/new">Agrega uno</Link>.
          </p>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table className="table">
            <thead>
              <tr>
                <th>Alias</th>
                <th>Tipo</th>
                <th>Institución</th>
                <th>Identificador</th>
                <th>Moneda</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((pm) => (
                <tr key={pm.id}>
                  <td><Link to={`/payment-methods/${pm.id}`}>{pm.alias}</Link></td>
                  <td><span className="type-label">{TYPE_LABELS[pm.type] || pm.type}</span></td>
                  <td>{pm.institution}</td>
                  <td style={{ fontFamily: "monospace" }}>{pm.identifier_masked}</td>
                  <td>{pm.currency}</td>
                  <td>
                    <span className={`badge badge-${pm.status}`}>
                      {pm.status === "active" ? "Activo" : "Inactivo"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && data.pages > 1 && (
        <div className="pagination">
          <button className="btn btn-ghost btn-sm" disabled={page === 1} onClick={() => setPage(page - 1)}>← Anterior</button>
          <span className="text-muted">Página {page} de {data.pages}</span>
          <button className="btn btn-ghost btn-sm" disabled={page === data.pages} onClick={() => setPage(page + 1)}>Siguiente →</button>
        </div>
      )}
    </div>
  );
}
