# GigFlow Server

The **GigFlow Server** is the backend system for the GigFlow platform, built using the **FastAPI** Python framework. It provides RESTful APIs for the application, handles user authentication, manages data storage, and integrates with external services. The server uses **PostgreSQL** as the primary database for secure and reliable data management.

---

## 📌 Overview

The GigFlow server is a high-performance microservice backend designed to:
- Handle user authentication using OAuth2 and JWT tokens.
- Manage earnings, expenses, and tax data for gig workers.
- Integrate with third-party APIs like Uber, Lyft, DoorDash, Upwork, and Fiverr.
- Provide endpoints for the admin panel and mobile app.
- Ensure data security and compliance with GDPR, CCPA, and SOC 2 standards.

---

## 🏗️ Features

### 1. **User Authentication**
- OAuth2-based authentication for third-party platforms (e.g., Uber, Lyft).
- JWT-based token management for secure access.
- Role-based access control (RBAC) for admin and user privileges.

### 2. **Earnings and Data Management**
- Fetch gig earnings via third-party APIs or RPA bots.
- Store and organize earnings data in PostgreSQL for efficient query access.
- Support for multiple gig platforms like Uber, Lyft, DoorDash, Upwork, and Fiverr.

### 3. **Expense Categorization**
- Use AI (NLP-based classification) to categorize user expenses.
- Map transactions to tax-deductible categories with high accuracy.

### 4. **Tax Estimation**
- Calculate tax estimates based on earnings and categorized expenses.
- Generate actionable tax recommendations for users.

### 5. **Financial Reporting**
- Aggregate data to provide financial insights through APIs.
- Generate detailed weekly, monthly, and yearly reports.

---

## 📂 Directory Structure

Here’s the directory structure of the GigFlow server project:

```
GigFlow-Server/
├── app/
│   ├── api/                 # API endpoints and route definitions
│   ├── core/                # Core application settings and configuration
│   ├── db/                  # Database models and session management
│   ├── services/            # Business logic (e.g., API integrations, RPA tasks)
│   ├── schemas/             # Pydantic models for request/response validation
│   ├── tests/               # Unit and integration tests
│   ├── utils/               # Helper functions and utilities
│   └── main.py              # Application entry point
├── migrations/              # Alembic database migrations
├── .env                     # Environment variables for configuration
├── requirements.txt         # Python dependencies
├── Dockerfile               # Dockerfile for containerization
├── README.md                # Documentation
└── pyproject.toml           # Python project configuration
```

---

## 🛠️ Installation & Setup

### Prerequisites
- **Python 3.9+**
- **PostgreSQL** (v12+ recommended)
- **Docker** (optional, for containerized deployment)

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/Gig-Flow/gig-flow-server.git
   cd GigFlow-Server
   ```

2. Set up a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/Mac
   venv\Scripts\activate     # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Create a `.env` file in the root directory and add the following variables:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/gigflow
   SECRET_KEY=your-secret-key
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ALLOWED_ORIGINS=http://localhost:3000
   ```

5. Apply database migrations:
   ```bash
   alembic upgrade head
   ```

6. Run the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

7. Access the API documentation:
   Open your browser and go to [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI) or [http://localhost:8000/redoc](http://localhost:8000/redoc).

---

## 🗄️ Database Configuration

The server uses **PostgreSQL** as the primary database. Database models are defined using **SQLAlchemy** and migrations are managed using **Alembic**.

### Example Database Model:
```python
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.base_class import Base

class Earnings(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    platform = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
```

### Alembic Commands
- Initialize migrations:
  ```bash
  alembic init migrations
  ```
- Create a migration script:
  ```bash
  alembic revision --autogenerate -m "Add earnings table"
  ```
- Apply migrations:
  ```bash
  alembic upgrade head
  ```

---

## 🔌 API Endpoints

### Authentication
- `POST /auth/login`: Authenticate users and issue JWT tokens.
- `POST /auth/register`: Register a new user.
- `POST /auth/refresh`: Refresh the access token.

### Earnings
- `GET /earnings`: Fetch earnings for the authenticated user.
- `POST /earnings`: Add new earnings data manually.

### Expenses
- `GET /expenses`: Fetch categorized expenses.
- `POST /expenses`: Manually add or adjust expenses.

### Tax Estimation
- `GET /tax/estimate`: Fetch tax estimation report for the user.

### Admin
- `GET /admin/users`: Fetch a list of all users (requires admin role).
- `GET /admin/logs`: Fetch system logs for debugging.

Full API documentation is available at [Swagger UI](http://localhost:8000/docs).

---

## 🐳 Docker Deployment

To run the server in a Docker container:

1. Build the Docker image:
   ```bash
   docker build -t gigflow-server .
   ```

2. Run the container:
   ```bash
   docker run -d --name gigflow-server -p 8000:8000 --env-file .env gigflow-server
   ```

3. The server will be accessible at `http://localhost:8000`.

---

## 🛠️ Available Scripts

### 1. Run the Development Server
```bash
uvicorn app.main:app --reload
```

### 2. Run Tests
```bash
pytest
```

### 3. Run Linter
```bash
flake8 app
```

---

## 📦 Key Technologies Used

- **FastAPI**: High-performance Python framework for building APIs.
- **PostgreSQL**: Relational database for secure and scalable data storage.
- **SQLAlchemy**: ORM for database modeling and interaction.
- **Alembic**: Database migration tool.
- **Uvicorn**: ASGI server for running the FastAPI application.
- **Pytest**: Testing framework for unit and integration tests.
- **Docker**: Containerization for deployment.

---

## 🔒 Security

- **JWT Authentication**: Provides secure token-based authentication.
- **Environment Variables**: Sensitive configurations (e.g., database credentials) are managed via `.env` files.
- **Data Encryption**: Sensitive data is encrypted before storage.
- **Compliance**: The backend ensures compliance with **GDPR**, **CCPA**, and **SOC 2** standards.

---

## 🧑‍💻 Contribution Guidelines

We welcome contributions to improve the GigFlow server! To contribute:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature-name`.
3. Commit changes: `git commit -m "Add your message here"`.
4. Push to the branch: `git push origin feature-name`.
5. Submit a pull request for review.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 💬 Contact

For questions, issues, or feedback, please contact us at **support@gigflow.com**.

Happy Coding! 🚀