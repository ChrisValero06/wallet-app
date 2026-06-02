# Wallet Segura — Gestión de Métodos de Pago

Aplicación web fullstack para registro y administración segura de métodos de pago.

---

## Arquitectura

```
┌─────────────────────┐        ┌─────────────────────────────────┐
│     Frontend        │        │           Backend               │
│   React 18 + Vite   │──────▶│  FastAPI  (Python)              │
│   React Router v6   │  HTTP  │                                 │
│   Axios + JWT       │        │  ┌──────────┐  ┌────────────┐  │
└─────────────────────┘        │  │  Routes  │  │  Services  │  │
                               │  │ /auth    │  │ encryption │  │
                               │  │ /users   │  │ audit_log  │  │
                               │  │ /methods │  └────────────┘  │
                               │  └──────────┘                  │
                               │       │                         │
                               │  ┌────▼────────────────────┐   │
                               │  │   SQLAlchemy ORM        │   │
                               │  │   Alembic Migrations    │   │
                               │  └────────────────────────┘   │
                               │       │                         │
                               └───────┼─────────────────────────┘
                                       │
                               ┌───────▼──────┐
                               │  SQLite /    │
                               │  PostgreSQL  │
                               └──────────────┘
```

**Stack:**
- **Backend:** Python · FastAPI · SQLAlchemy · Alembic
- **Base de datos:** SQLite (desarrollo) / PostgreSQL (producción)
- **Auth:** JWT (python-jose) + bcrypt
- **Cifrado de datos sensibles:** Fernet (cryptography)
- **Frontend:** React 18 · Vite · React Router v6 · Axios

---

## Requisitos

- Python 3.11+
- Node.js 18+

---

## Levantar el proyecto

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd "Sistema de wallet"
```

### 2. Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
copy .env.example .env
```

Editar `.env` y generar la clave Fernet:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Pegar el resultado en `ENCRYPTION_KEY` del archivo `.env`.

```bash
# Ejecutar migraciones
alembic upgrade head

# Iniciar el servidor
uvicorn app.main:app --reload
```

API disponible en: http://localhost:8000  
Documentación Swagger: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Configurar variables de entorno (opcional, hay proxy en vite.config.js)
copy .env.example .env

# Iniciar servidor de desarrollo
npm run dev
```

Frontend disponible en: http://localhost:5173

---

## Ejecutar tests

```bash
cd backend
pytest tests/ -v
```

---

## Variables de entorno

### Backend (`backend/.env`)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DATABASE_URL` | URL de la base de datos | `sqlite:///./wallet.db` |
| `SECRET_KEY` | Clave secreta para JWT | Cadena aleatoria segura |
| `ALGORITHM` | Algoritmo JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiración del token (minutos) | `30` |
| `ENCRYPTION_KEY` | Clave Fernet para cifrado | Generada con el comando arriba |
| `FRONTEND_URL` | URL del frontend (para CORS) | `http://localhost:5173` |

### Frontend (`frontend/.env`)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `VITE_API_URL` | URL base del API | `http://localhost:8000` |

---

## Endpoints API

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/api/auth/register` | Registro de usuario | No |
| POST | `/api/auth/login` | Inicio de sesión → JWT | No |
| POST | `/api/auth/logout` | Cierre de sesión | Sí |
| GET | `/api/users/me` | Perfil del usuario autenticado | Sí |
| GET | `/api/payment-methods` | Listar métodos (paginado, filtros) | Sí |
| POST | `/api/payment-methods` | Registrar método de pago | Sí |
| GET | `/api/payment-methods/{id}` | Detalle de un método | Sí |
| DELETE | `/api/payment-methods/{id}` | Desactivar método (soft delete) | Sí |
| GET | `/health` | Health check | No |

---

## Diseño de base de datos

### `users`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Clave primaria |
| email | VARCHAR | Único, indexado |
| full_name | VARCHAR | Nombre completo |
| hashed_password | VARCHAR | Bcrypt |
| is_active | BOOLEAN | Estado de la cuenta |
| created_at / updated_at | TIMESTAMP | Auditoría |

### `payment_methods`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Clave primaria |
| user_id | UUID FK | Propietario |
| type | VARCHAR | card / bank_account / clabe / other |
| alias | VARCHAR | Nombre amigable |
| institution | VARCHAR | Banco o institución |
| currency | VARCHAR(3) | MXN, USD, EUR, etc. |
| identifier_encrypted | TEXT | Identificador cifrado con Fernet |
| identifier_hash | VARCHAR(64) | SHA-256 para detección de duplicados |
| identifier_last4 | VARCHAR(4) | Últimos 4 dígitos para display |
| status | VARCHAR | active / inactive |
| is_deleted | BOOLEAN | Soft delete |
| created_at / updated_at | TIMESTAMP | Auditoría |

**Restricción única:** `(user_id, type, identifier_hash)` — previene duplicados.

### `audit_logs`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Clave primaria |
| user_id | UUID FK | Usuario que ejecutó la acción |
| action | VARCHAR | LOGIN, LOGOUT, REGISTER, CREATE_PAYMENT_METHOD, VIEW_PAYMENT_METHOD, DELETE_PAYMENT_METHOD, DUPLICATE_ATTEMPT |
| entity_type | VARCHAR | user / payment_method |
| entity_id | UUID | ID de la entidad afectada |
| metadata | JSON | Contexto adicional |
| ip_address | VARCHAR | IP del cliente |
| created_at | TIMESTAMP | Timestamp de la operación |

---

## Seguridad

- **Contraseñas:** Hashing bcrypt con salt automático. Nunca se almacena texto plano.
- **JWT:** Tokens con expiración configurable. Blacklist en memoria para invalidación en logout.
- **Datos sensibles:** El identificador del método de pago (número de tarjeta, CLABE, cuenta) se cifra con AES-128 (Fernet) antes de persistirse. Solo se muestra enmascarado en la interfaz (`**** **** **** 1234`).
- **Detección de duplicados:** Se compara el SHA-256 del identificador (sin cifrar) para evitar duplicados sin necesidad de descifrar.
- **Autorización:** Cada endpoint verifica que el recurso pertenece al usuario autenticado.
- **CORS:** Configurado solo para el origen del frontend.
- **Validación:** Pydantic valida todos los inputs (tipos, longitudes, formatos).
- **SQL Injection:** Prevenida por SQLAlchemy ORM (nunca SQL raw con interpolación de usuario).

---

## Trazabilidad

Todas las operaciones relevantes quedan registradas en `audit_logs`:
- Registro de usuario
- Login y logout
- Creación, consulta y eliminación de métodos de pago
- Intentos de registro duplicado

Cada registro incluye: usuario, acción, entidad afectada, IP del cliente y timestamp.

---

## Deploy

La aplicación está desplegada en:

- **Frontend:** [Vercel](https://wallet-app-chrisvalero.vercel.app) — React SPA con build automático
- **Backend:** [Render](https://wallet-backend-xxx.onrender.com) — FastAPI web service

### CI/CD

El repositorio incluye un workflow de GitHub Actions (`.github/workflows/ci.yml`) que en cada push o PR a `main`:

1. **Backend:** Instala dependencias, ejecuta tests unitarios y linting con ruff.
2. **Frontend:** Instala dependencias y verifica que el build compile sin errores.

### Configuración de deploy

**Frontend (Vercel):**
- Framework: Vite
- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `dist`
- Variable de entorno: `VITE_API_URL` → URL del backend en Render

**Backend (Render):**
- Runtime: Python
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Variables de entorno: `SECRET_KEY`, `ENCRYPTION_KEY`, `DATABASE_URL`, `ALLOWED_ORIGINS`

---

## Estructura del proyecto

```
Sistema de wallet/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/          # config, database, security
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── api/           # routes + deps
│   │   └── services/      # encryption, audit
│   ├── alembic/           # migraciones
│   ├── tests/             # pytest
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── context/       # AuthContext
│   │   ├── services/      # axios instance
│   │   ├── components/    # Navbar, PrivateRoute
│   │   └── pages/         # Login, Register, Dashboard, PaymentMethods, …
│   ├── package.json
│   └── .env.example
└── README.md
```
