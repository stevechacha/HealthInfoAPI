# Healthcare Management System API

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A modern, secure, and scalable API for managing healthcare programs and patient data.

## Features

- **Patient Management**: Full CRUD operations for patient records
- **Program Management**: Create and manage health programs
- **Secure Authentication**: API key-based access control
- **Data Validation**: Strong typing with Pydantic models
- **Audit Logging**: Comprehensive request logging
- **Health Monitoring**: System status endpoints

## Tech Stack

- **Framework**: FastAPI
- **Authentication**: API Key Header
- **Validation**: Pydantic
- **Logging**: Python Standard logging
- **Testing**: pytest (with async support)

## Getting Started

### Prerequisites

- Python 3.9+
- pipenv

### Installation

```bash
git clone https://github.com/yourrepo/healthcare-api.git
cd healthcare-api
pipenv install --dev
```

### Configuration

Create `.env` file:

```ini
API_KEY=your_secure_key_here
APP_ENV=development
```

### Running the API

```bash
pipenv run uvicorn main:app --reload
```

## API Documentation

Access interactive documentation at `http://localhost:8000/docs`

### Example Requests

**Create Patient**
```bash
curl -X POST "http://localhost:8000/patients" \
  -H "X-API-Key: your_secure_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "national_id": "A123456789",
    "full_name": "Jane Doe",
    "date_of_birth": "1985-05-15",
    "blood_type": "O+"
  }'
```

**Response**
```json
{
  "status": "success",
  "message": "Patient registered successfully",
  "data": {
    "patient_id": "PAT-a1b2c3d4",
    "national_id": "A123456789",
    "full_name": "Jane Doe",
    "date_of_birth": "1985-05-15",
    "blood_type": "O+",
    "enrolled_programs": [],
    "medical_history": []
  }
}

```

## Testing

Run the test suite:

```bash
pipenv run pytest -v
```

## Deployment

Recommended deployment options:

1. **Docker Container**
```Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Kubernetes**: See sample deployment in `/kubernetes/`

## Security

- API key authentication for all endpoints
- Secure headers middleware
- Input validation for all requests
- Rate limiting (implemented via middleware)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## License

MIT License
