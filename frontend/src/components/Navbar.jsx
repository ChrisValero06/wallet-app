import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <nav>
      <Link to="/" className="nav-brand">Wallet</Link>
      <div className="nav-links">
        {user ? (
          <>
            <Link to="/dashboard">Inicio</Link>
            <Link to="/payment-methods">Métodos de pago</Link>
            <span style={{ color: "var(--gray-400)" }}>{user.full_name}</span>
            <button className="btn btn-ghost btn-sm" onClick={handleLogout}>Salir</button>
          </>
        ) : (
          <>
            <Link to="/login">Iniciar sesión</Link>
            <Link to="/register">Registrarse</Link>
          </>
        )}
      </div>
    </nav>
  );
}
