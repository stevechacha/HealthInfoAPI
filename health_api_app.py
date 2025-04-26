from datetime import date
from typing import List, Optional, Generic, TypeVar
from enum import Enum
import hashlib

from fastapi import FastAPI, HTTPException, Depends, status, Security
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field

# --- Initialize FastAPI ---
app = FastAPI(
    title="HealthCare Management System",
    version="2.1",
    description="Comprehensive patient and program management system",
    docs_url="/"
)

# --- Generic Response Model ---
T = TypeVar('T')

class GenericResponse(BaseModel, Generic[T]):
    status: str
    message: str
    data: Optional[T] = None

# --- Custom Exception Handlers ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "data": None
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Validation error",
            "data": exc.errors()
        }
    )

# --- Security Configuration ---
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME)
VALID_API_KEY = "securekey123"

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != VALID_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key"
        )
    return api_key

# --- Data Models ---
class ProgramType(str, Enum):
    CHRONIC = "chronic"
    INFECTIOUS = "infectious"
    PREVENTIVE = "preventive"
    REHABILITATION = "rehabilitation"

class ProgramBase(BaseModel):
    name: str = Field(..., example="Diabetes Care")
    program_type: ProgramType
    target_age_group: Optional[str] = None
    risk_factors: List[str] = []

class Program(ProgramBase):
    program_id: str

class PatientBase(BaseModel):
    national_id: str = Field(..., min_length=10, max_length=15)
    full_name: str = Field(..., min_length=3)
    date_of_birth: date
    blood_type: Optional[str] = None

class Patient(PatientBase):
    patient_id: str
    enrolled_programs: List[str] = []
    medical_history: List[str] = []

class EnrollmentRequest(BaseModel):
    patient_id: str
    program_id: str

# --- Database Simulation ---
class HealthDatabase:
    def __init__(self):
        self.patients = {}
        self.programs = {}
        self.users = {
            "doctor1": hashlib.sha256("password123".encode()).hexdigest()
        }

db = HealthDatabase()

# --- Helper Functions ---
def generate_patient_id(national_id: str):
    return f"PAT-{national_id[-6:]}"

def calculate_age(date_of_birth: date):
    today = date.today()
    return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))

def validate_program_eligibility(patient: Patient, program: Program):
    age = calculate_age(patient.date_of_birth)
    if program.target_age_group:
        min_age, max_age = map(int, program.target_age_group.split('-'))
        if not (min_age <= age <= max_age):
            return False
    return True

def create_response(data=None, message: str = "Success", status: str = "success"):
    return {
        "status": status,
        "message": message,
        "data": data
    }

# --- API Endpoints ---
@app.post("/patients", response_model=GenericResponse[Patient], tags=["Patients"])
def register_patient(patient: PatientBase, api_key: str = Depends(get_api_key)):
    """Register a new patient in the system"""
    if any(p.national_id == patient.national_id for p in db.patients.values()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Patient already registered"
        )

    patient_id = generate_patient_id(patient.national_id)
    new_patient = Patient(
        patient_id=patient_id,
        **patient.dict(),
        medical_history=[]
    )
    db.patients[patient_id] = new_patient
    return create_response(new_patient, "Patient registered successfully")

@app.post("/programs", response_model=GenericResponse[Program], tags=["Programs"])
def create_program(program: ProgramBase, api_key: str = Depends(get_api_key)):
    """Create a new health program"""
    program_id = f"PROG-{hashlib.sha1(program.name.encode()).hexdigest()[:8]}"
    new_program = Program(**program.dict(), program_id=program_id)

    if program_id in db.programs:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Program already exists"
        )

    db.programs[program_id] = new_program
    return create_response(new_program, "Program created successfully")

@app.post("/enroll", response_model=GenericResponse[Patient], tags=["Enrollments"])
def enroll_patient(request: EnrollmentRequest, api_key: str = Depends(get_api_key)):
    """Enroll patient in a health program"""
    patient = db.patients.get(request.patient_id)
    program = db.programs.get(request.program_id)

    if not patient:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")
    if not program:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Program not found")

    if not validate_program_eligibility(patient, program):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient not eligible for this program"
        )

    if request.program_id not in patient.enrolled_programs:
        patient.enrolled_programs.append(request.program_id)

    return create_response(patient, "Patient enrolled successfully")

@app.get("/patients/{patient_id}/recommendations", response_model=GenericResponse[dict], tags=["Recommendations"])
def get_recommendations(patient_id: str, api_key: str = Depends(get_api_key)):
    """Get recommended programs for a patient"""
    patient = db.patients.get(patient_id)
    if not patient:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")

    recommendations = []
    for program in db.programs.values():
        if validate_program_eligibility(patient, program):
            recommendations.append({
                "program_id": program.program_id,
                "program_name": program.name,
                "match_reasons": ["Age appropriate", "Risk factors match"]
            })

    return create_response(
        {"patient_id": patient_id, "recommendations": recommendations},
        "Recommendations generated"
    )

@app.get("/patients", response_model=GenericResponse[List[Patient]], tags=["Patients"])
def search_patients(name: Optional[str] = None, program_id: Optional[str] = None):
    """Search patients by name or program enrollment"""
    results = []
    for patient in db.patients.values():
        if name and name.lower() not in patient.full_name.lower():
            continue
        if program_id and program_id not in patient.enrolled_programs:
            continue
        results.append(patient)
    return create_response(results, "Patients found")

@app.get("/patients/{patient_id}", response_model=GenericResponse[Patient], tags=["Patients"])
def get_patient(patient_id: str):
    """Get complete patient profile"""
    patient = db.patients.get(patient_id)
    if not patient:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")
    return create_response(patient, "Patient retrieved")

@app.get("/health", response_model=GenericResponse[dict], tags=["System"])
def health_check():
    """System health check"""
    return create_response(
        {"status": "healthy", "patients": len(db.patients), "programs": len(db.programs)},
        "System health check"
    )

# --- Test Data Initialization ---
@app.on_event("startup")
async def startup_event():
    # Initialize with sample programs
    sample_programs = [
        ProgramBase(
            name="Diabetes Management",
            program_type=ProgramType.CHRONIC,
            target_age_group="30-80",
            risk_factors=["obesity", "family history"]
        ),
        ProgramBase(
            name="Child Vaccination Program",
            program_type=ProgramType.PREVENTIVE,
            target_age_group="0-12",
            risk_factors=["low birth weight"]
        )
    ]
    for program in sample_programs:
        create_program(program, VALID_API_KEY)