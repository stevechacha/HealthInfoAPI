# Health Information Management API

[![GitHub stars](https://img.shields.io/github/stars/stevechacha/HealthInfoAPI?style=social)](https://github.com/stevechacha/HealthInfoAPI/stargazers)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A robust healthcare management system API built with FastAPI for managing patient records and health programs.

🔗 **Live Demo**: [Coming Soon]()  
📚 **API Documentation**: [View Swagger UI](https://healthinfoapi.example.com/docs) (after deployment)

## Table of Contents
- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Features

### Patient Management
- ✅ Patient registration with national ID verification
- 🔍 Advanced patient search functionality
- 📊 Patient profile with enrollment history
- 💡 Automated program recommendations

### Program Management
- 🏥 Multiple program types (Chronic, Preventive, etc.)
- 🎯 Age-specific program targeting
- 📈 Risk factor analysis
- 🤝 Program enrollment management

### Security
- 🔑 API key authentication
- 🛡️ Request validation middleware
- 📝 Comprehensive audit logging
- 🚦 Rate limiting (coming in v2.3)

## System Architecture

```mermaid
graph TD
    A[Client] --> B[API Gateway]
    B --> C[Authentication]
    C --> D[Patient Service]
    C --> E[Program Service]
    D --> F[Database]
    E --> F
````
## Installation & Setup

```bash
# Clone repository
git clone https://github.com/stevechacha/HealthInfoAPI.git
cd HealthInfoAPI

# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn main:app --reload
```

# API Documentation

## Endpoint Reference

### Register Patient
**Endpoint**  
`POST /patients`

**Request Body**
```json
{
  "national_id": "1234567890",
  "full_name": "Jane Doe",
  "date_of_birth": "1985-05-15",
  "blood_type": "O+"
}
```

## API Endpoints Reference

| Endpoint                | Method | Parameters                      | Description                      | Security  |
|-------------------------|--------|---------------------------------|----------------------------------|-----------|
| `/patients`             | POST   | `national_id`, `full_name`, `date_of_birth`, `blood_type` | Register new patient | API Key |
| `/patients/{id}`        | GET    | `id` (path parameter)           | Get full patient profile         | API Key   |
| `/programs`             | POST   | `name`, `program_type`, `target_age_group`, `risk_factors` | Create new health program | API Key |
| `/enroll`               | POST   | `patient_id`, `program_id`      | Enroll patient in program        | API Key   |
| `/patients/search`      | GET    | `name`, `program_id` (query params) | Search patients by criteria     | API Key   |
| `/health`               | GET    | -                               | System health status             | Public    |


## API Key Authentication

All endpoints require the following header:

```http
X-API-Key: securekey123
```

---

## Example API Usage

### 1. Create a New Patient

```bash
curl -X 'POST' \
  'http://localhost:8000/patients' \
  -H 'X-API-Key: securekey123' \
  -H 'Content-Type: application/json' \
  -d '{
    "national_id": "1234567890",
    "full_name": "John Doe",
    "date_of_birth": "1980-01-01",
    "blood_type": "A+"
  }'
```

**Response:**

```json
{
  "status": "success",
  "message": "Patient registered successfully",
  "data": {
    "patient_id": "PAT-567890",
    "national_id": "1234567890",
    "full_name": "John Doe",
    "date_of_birth": "1980-01-01",
    "blood_type": "A+",
    "enrolled_programs": [],
    "medical_history": [],
    "created_at": "2023-10-15"
  }
}
```

---

### 2. Get All Patients

```bash
curl -X 'GET' \
  'http://localhost:8000/patients' \
  -H 'X-API-Key: securekey123'
```

---

### 3. Create a New Program

```bash
curl -X 'POST' \
  'http://localhost:8000/programs' \
  -H 'X-API-Key: securekey123' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Cardiac Rehabilitation",
    "program_type": "rehabilitation",
    "target_age_group": "40-80",
    "risk_factors": ["heart disease", "high cholesterol"]
  }'
```

---

### 4. Enroll Patient in Program

```bash
curl -X 'POST' \
  'http://localhost:8000/enroll' \
  -H 'X-API-Key: securekey123' \
  -H 'Content-Type: application/json' \
  -d '{
    "patient_id": "PAT-567890",
    "program_id": "PROG-abcdef"
  }'
```

---

### 5. Get Program Recommendations

```bash
curl -X 'GET' \
  'http://localhost:8000/patients/PAT-567890/recommendations' \
  -H 'X-API-Key: securekey123'
```

**Sample Response:**

```json
{
  "status": "success",
  "message": "Recommendations generated",
  "data": [
    {
      "program_id": "PROG-a1b2c3d4",
      "program_name": "Diabetes Management",
      "match_reasons": ["Age appropriate", "Risk factors match"]
    }
  ]
}
```

---

## Key Endpoints

| Method | Path | Description |
|:------:|:---- |:----------- |
| `POST` | `/patients` | Register new patient |
| `GET` | `/patients/{patient_id}` | Get patient details |
| `POST` | `/programs` | Create new healthcare program |
| `POST` | `/enroll` | Enroll patient in program |
| `GET` | `/patients/search` | Search patients by name/program |
| `GET` | `/health` | System health check |

---

## Error Handling

The API returns structured error responses with details. Common errors include:

- **401 Unauthorized**: Missing/invalid API key
- **404 Not Found**: Resource not found
- **422 Validation Error**: Invalid request data

---

## Development

- The system initializes with sample data on startup:
  - 2 healthcare programs
  - Test patient records
- Use the included Swagger UI for interactive testing:
  
  ```
  http://localhost:8000
  ```

  
## Screenshots

![Screenshot 2025-04-27 at 17.40.32.png](images/Screenshot%202025-04-27%20at%2017.40.32.png)
![Screenshot 2025-04-27 at 17.40.51.png](images/Screenshot%202025-04-27%20at%2017.40.51.png)
![Screenshot 2025-04-27 at 17.40.54.png](images/Screenshot%202025-04-27%20at%2017.40.54.png)
![Screenshot 2025-04-27 at 17.41.06.png](images/Screenshot%202025-04-27%20at%2017.41.06.png)

## Swagger UI
![Screenshot 2025-04-27 at 17.41.46.png](images/Screenshot%202025-04-27%20at%2017.41.46.png)
![Screenshot 2025-04-27 at 17.42.21.png](images/Screenshot%202025-04-27%20at%2017.42.21.png)
![Screenshot 2025-04-27 at 17.43.24.png](images/Screenshot%202025-04-27%20at%2017.43.24.png)
![Screenshot 2025-04-27 at 17.43.38.png](images/Screenshot%202025-04-27%20at%2017.43.38.png)
![Screenshot 2025-04-27 at 17.44.11.png](images/Screenshot%202025-04-27%20at%2017.44.11.png)
![Screenshot 2025-04-27 at 17.44.28.png](images/Screenshot%202025-04-27%20at%2017.44.28.png)

## Video Demo
[Screen Recording 2025-04-27 at 17.29.42.mov](images/Screen%20Recording%202025-04-27%20at%2017.29.42.mov)
[Screen R
