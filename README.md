# Backend Portfolio API

A backend REST API built with FastAPI for managing users, products, and
orders.

The project includes JWT authentication, role-based access control
(RBAC), inventory management, PostgreSQL database migrations, automated
testing, and cloud deployment.

## Live Demo

The API is deployed on Render and uses PostgreSQL hosted on Neon.

-   **Swagger UI:** https://backend-portfolio-a8qy.onrender.com/docs
-   **API Base URL:** https://backend-portfolio-a8qy.onrender.com/

> The service uses Render's free tier, so the first request may take a
> short time if the service has been inactive.

## Features

### Authentication

-   User registration
-   Password hashing with Argon2
-   OAuth2 password login
-   JWT access token authentication
-   Disabled account validation
-   Protected endpoints using FastAPI dependencies

### Product Management

-   Get product list
-   Get product by ID
-   Filter products by name, minimum price, and minimum stock
-   Sort products by price
-   Pagination support
-   Admin-only product creation, update, and deletion

### Order Management

-   Authenticated order creation
-   Users can access only their own orders
-   Admins can access all orders
-   Inventory validation before order creation
-   Automatic stock deduction when an order is created
-   Automatic stock adjustment when order quantity changes
-   Automatic stock restoration when an order is deleted
-   Owner/Admin authorization for individual order operations

### Administration

-   Role-based access control
-   View all users
-   Change user roles
-   Activate or suspend user accounts
-   Prevent administrators from changing their own role
-   Prevent administrators from suspending their own account

## Tech Stack

-   Python
-   FastAPI
-   Uvicorn
-   SQLAlchemy ORM
-   PostgreSQL
-   Neon
-   Pydantic
-   Alembic
-   PyJWT
-   pwdlib / Argon2
-   Pytest
-   Git / GitHub
-   Render

## Architecture

``` text
Client / Swagger UI
        |
        v
Render Web Service
        |
        v
FastAPI
        |
        +--------------------+
        |                    |
        v                    v
     Routers          Authentication / RBAC
        |                    |
        +---------+----------+
                  |
                  v
          SQLAlchemy ORM
                  |
               Session
                  |
               Engine
                  |
            Connection
                  |
                  v
        PostgreSQL (Neon)
```

## Project Structure

``` text
backend-portfolio/
|
|-- main.py
|-- database.py
|-- security.py
|
|-- models/
|   |-- user.py
|   |-- product.py
|   `-- order.py
|
|-- schemas/
|   |-- user.py
|   |-- product.py
|   `-- order.py
|
|-- routers/
|   |-- users.py
|   |-- products.py
|   |-- orders.py
|   `-- admin.py
|
|-- tests/
|   |-- conftest.py
|   |-- test_users.py
|   |-- test_products.py
|   `-- test_orders.py
|
|-- alembic/
|   `-- versions/
|
|-- alembic.ini
|-- requirements.txt
|-- .env.example
`-- README.md
```

## Database

The application uses PostgreSQL in the deployed environment, hosted on
Neon.

SQLAlchemy is used as the ORM layer. Database connection information is
provided through the `DATABASE_URL` environment variable instead of
being stored directly in the source code.

## Installation

Clone the repository:

``` bash
git clone <repository-url>
cd backend-portfolio
```

Create and activate a Python virtual environment, then install the
dependencies:

``` bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file based on `.env.example`:

``` text
SECRET_KEY=your-secret-key
DATABASE_URL=your-postgresql-database-url
```

The real `.env` file contains sensitive information and should not be
committed to version control.

In the deployed environment, these values are configured as Render
environment variables.

## Running the API Locally

Start the development server:

``` bash
uvicorn main:app --reload
```

The API will be available at:

``` text
http://127.0.0.1:8000
```

Interactive API documentation:

``` text
http://127.0.0.1:8000/docs
```

## API Endpoints

### Users

  Method   Endpoint         Authentication   Description
  -------- ---------------- ---------------- --------------------------------------
  POST     `/users`         No               Register a new user
  POST     `/users/login`   No               Login and receive a JWT access token

### Products

  ------------------------------------------------------------------------
  Method            Endpoint           Authentication    Description
  ----------------- ------------------ ----------------- -----------------
  GET               `/products`        No                Get products with
                                                         filtering,
                                                         sorting, and
                                                         pagination

  GET               `/products/{id}`   No                Get a product by
                                                         ID

  POST              `/products`        Admin             Create a product

  PUT               `/products/{id}`   Admin             Update a product

  DELETE            `/products/{id}`   Admin             Delete a product
  ------------------------------------------------------------------------

### Orders

  -----------------------------------------------------------------------
  Method            Endpoint          Authentication    Description
  ----------------- ----------------- ----------------- -----------------
  GET               `/orders`         User/Admin        Get own orders;
                                                        admins can get
                                                        all orders

  GET               `/orders/{id}`    Owner/Admin       Get an order by
                                                        ID

  POST              `/orders`         User/Admin        Create an order
                                                        and deduct
                                                        inventory

  PUT               `/orders/{id}`    Owner/Admin       Update order
                                                        quantity and
                                                        synchronize
                                                        inventory

  DELETE            `/orders/{id}`    Owner/Admin       Delete an order
                                                        and restore
                                                        inventory
  -----------------------------------------------------------------------

### Admin

  ----------------------------------------------------------------------------------
  Method            Endpoint                     Authentication    Description
  ----------------- ---------------------------- ----------------- -----------------
  GET               `/admin/users`               Admin             Get all users

  PATCH             `/admin/users/{id}/role`     Admin             Change a user's
                                                                   role

  PATCH             `/admin/users/{id}/status`   Admin             Activate or
                                                                   suspend a user
  ----------------------------------------------------------------------------------

## Authentication and Authorization

The API uses OAuth2 password login and JWT bearer tokens.

After a successful login, the API returns an access token. Protected
endpoints decode the JWT to identify the current user and validate
account status.

Role-based authorization is implemented through FastAPI dependencies:

``` text
Request
   |
   v
JWT Authentication
   |
   v
Current User
   |
   +--> Regular User --> User-owned resources
   |
   `--> Admin --------> Administrative operations
```

Unauthorized or forbidden operations return the appropriate HTTP status
codes, such as `401 Unauthorized` or `403 Forbidden`.

## Order and Inventory Logic

Order operations are synchronized with product inventory.

``` text
Create Order
    |
    v
Validate Stock
    |
    v
Deduct Product Stock
    |
    v
Create Order
    |
    v
Commit Transaction
```

When an order quantity is updated, the stock difference is calculated
and synchronized with the product inventory.

When an order is deleted, the ordered quantity is restored to product
stock.

## Database Migration

Database schema migrations are managed with Alembic.

After changing SQLAlchemy models, generate a migration:

``` bash
alembic revision --autogenerate -m "migration description"
```

Review the generated migration file before applying it.

Apply pending migrations:

``` bash
alembic upgrade head
```

Alembic compares the SQLAlchemy model metadata with the current database
schema when generating migrations and tracks the applied database
revision through its migration version history.

## Testing

Run the automated test suite with:

``` bash
python -m pytest -v
```

The project currently includes **37 automated tests** covering the main
API workflows, including:

-   User registration and authentication
-   Product operations
-   Order operations
-   Authorization and ownership rules
-   Inventory deduction and restoration

Current verified result:

``` text
37 passed
```

## Deployment

The production API is deployed using:

``` text
GitHub
   |
   v
Render
   |
   v
FastAPI / Uvicorn
   |
   v
SQLAlchemy
   |
   v
PostgreSQL (Neon)
```

Render installs the project dependencies from `requirements.txt` and
starts the API with:

``` bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Sensitive configuration such as `DATABASE_URL` and `SECRET_KEY` is
stored in Render environment variables and is not committed to GitHub.

## Production Verification

The deployed API has been manually verified for the following workflows:

-   Public Swagger documentation
-   User registration
-   User login and JWT generation
-   Protected endpoint authentication
-   Regular-user permission restrictions
-   Admin-only product creation
-   Order creation
-   Automatic inventory deduction
-   Order deletion
-   Automatic inventory restoration

## Notes

Database primary-key IDs are unique identifiers and are not expected to
remain sequential after rows are deleted.

For example, deleting order ID `2` does not require the next order to
reuse ID `2`. PostgreSQL may continue with the next generated
identifier.
