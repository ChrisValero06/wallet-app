import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import PrivateRoute from "./components/PrivateRoute";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import PaymentMethods from "./pages/PaymentMethods";
import AddPaymentMethod from "./pages/AddPaymentMethod";
import PaymentMethodDetail from "./pages/PaymentMethodDetail";

export default function App() {
  const { user } = useAuth();

  return (
    <>
      <Navbar />
      <main className="container">
        <Routes>
          <Route path="/" element={<Navigate to={user ? "/dashboard" : "/login"} replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/payment-methods" element={<PrivateRoute><PaymentMethods /></PrivateRoute>} />
          <Route path="/payment-methods/new" element={<PrivateRoute><AddPaymentMethod /></PrivateRoute>} />
          <Route path="/payment-methods/:id" element={<PrivateRoute><PaymentMethodDetail /></PrivateRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
}
