# Backend Portfolio API

A backend REST API built with FastAPI for managing users, products, and orders.

The project includes JWT authentication, role-based access control, inventory management, database migrations, and automated testing.

## Features

### Authentication

- User registration
- Password hashing
- OAuth2 password login
- JWT access token authentication
- Disabled account validation

### Product Management

- Get product list
- Get product by ID
- Filter products by name, minimum price, and minimum stock
- Sort products by price
- Pagination support
- Admin-only product creation, update, and deletion

### Order Management

- Authenticated order creation
- Users can access only their own orders
- Admins can access all orders
- Inventory validation before order creation
- Automatic stock deduction when an order is created
- Automatic stock adjustment when order quantity changes
- Automatic stock restoration when an order is deleted

### Administration

- Role-based access control
- View all users
- Change user roles
- Activate or suspend user accounts
- Prevent administrators from changing their own role
- Prevent administrators from suspending their own account

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- Alembic
- PyJWT
- pwdlib
- Pytest
- Git / GitHub

## Project Structure

```text
backend-portfolio/
│
├── main.py
├── database.py
├── security.py
│
├── models/
│   ├── user.py
│   ├── product.py
│   └── order.py
│
├── schemas/
│   ├── user.py
│   ├── product.py
│   └── order.py
│
├── routers/
│   ├── users.py
│   ├── products.py
│   ├── orders.py
│   └── admin.py
│
├── tests/
│   ├── conftest.py
│   ├── test_users.py
│   ├── test_products.py
│   └── test_orders.py
│
├── alembic/
├── alembic.ini
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd backend-portfolio
```

Create and activate a Python virtual environment, then install the dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```text
SECRET_KEY=your-secret-key
```

Do not commit the actual `.env` file to version control.

## Running the API

Start the development server:

```bash
uvicorn main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

### Users

| Method | Endpoint | Authentication | Description |
|---|---|---|---|
| POST | `/users` | No | Register a new user |
| POST | `/users/login` | No | Login and receive a JWT access token |

### Products

| Method | Endpoint | Authentication | Description |
|---|---|---|---|
| GET | `/products` | No | Get products with filtering, sorting, and pagination |
| GET | `/products/{id}` | No | Get a product by ID |
| POST | `/products` | Admin | Create a product |
| PUT | `/products/{id}` | Admin | Update a product |
| DELETE | `/products/{id}` | Admin | Delete a product |

### Orders

| Method | Endpoint | Authentication | Description |
|---|---|---|---|
| GET | `/orders` | User/Admin | Get own orders; admins can get all orders |
| GET | `/orders/{id}` | Owner/Admin | Get an order by ID |
| POST | `/orders` | User/Admin | Create an order and deduct inventory |
| PUT | `/orders/{id}` | Owner/Admin | Update order quantity and synchronize inventory |
| DELETE | `/orders/{id}` | Owner/Admin | Delete an order and restore inventory |

### Admin

| Method | Endpoint | Authentication | Description |
|---|---|---|---|
| GET | `/admin/users` | Admin | Get all users |
| PATCH | `/admin/users/{id}/role` | Admin | Change a user's role |
| PATCH | `/admin/users/{id}/status` | Admin | Activate or suspend a user |

## Testing

Run the automated tests with:

```bash
pytest
```

Tests cover the main user, product, and order API workflows.

## Database Migration

Database schema migrations are managed with Alembic.

Apply migrations with:

```bash
alembic upgrade head
```