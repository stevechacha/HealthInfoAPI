"""
Healthcare Management System API
Updated for Pydantic v2 compatibility
"""

from datetime import date
from enum import Enum
from typing import List, Optional, Generic, TypeVar
import hashlib
import logging

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    status,
    Security,
    Request,
)
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from pydantic import ConfigDict

# ======================
# Configuration
# ======================
class Settings(BaseModel):
    API_KEY_NAME: str = "X-API-Key"
    API_KEY: str = "securekey123"  # In production, load from environment
    LOG_LEVEL: str = "INFO"

settings = Settings()

# ======================
# Logging Configuration
# ======================
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ======================
# FastAPI Application
# ======================
app = FastAPI(
    title="HealthCare Management System",
    version="2.2",
    description="Comprehensive patient and program management system",
    docs_url="/",
    redoc_url=None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# Security
# ======================
api_key_header = APIKeyHeader(name=settings.API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.API_KEY:
        logger.warning(f"Invalid API key attempt: {api_key}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key"
        )
    return api_key

# ======================
# Models
# ======================
class ProgramType(str, Enum):
    CHRONIC = "chronic"
    INFECTIOUS = "infectious"
    PREVENTIVE = "preventive"
    REHABILITATION = "rehabilitation"

T = TypeVar('T')

class ResponseModel(BaseModel, Generic[T]):
    status: str
    message: str
    data: Optional[T] = None

    @classmethod
    def success(cls, data: T = None, message: str = "Success"):
        return cls(status="success", message=message, data=data)

    @classmethod
    def error(cls, message: str, data: T = None):
        return cls(status="error", message=message, data=data)

class ProgramBase(BaseModel):
    name: str = Field(..., example="Diabetes Care", min_length=3, max_length=100)
    program_type: ProgramType
    target_age_group: Optional[str] = Field(
        None,
        pattern=r"^\d+-\d+$",
        example="18-65",
        description="Age range in format 'min-max'"
    )
    risk_factors: List[str] = Field(
        default_factory=list,
        example=["diabetes", "hypertension"],
        description="List of risk factors addressed by this program"
    )

    @validator("risk_factors", each_item=True)
    def validate_risk_factors(cls, v):
        if not v.strip():
            raise ValueError("Risk factor cannot be empty")
        return v.lower()

    model_config = ConfigDict(extra="forbid")

class ProgramCreate(ProgramBase):
    pass

class Program(ProgramBase):
    program_id: str
    created_at: date = Field(default_factory=date.today)

class PatientBase(BaseModel):
    national_id: str = Field(
        ...,
        min_length=10,
        max_length=15,
        example="1234567890",
        description="Government-issued national ID"
    )
    full_name: str = Field(..., min_length=3, max_length=100, example="John Doe")
    date_of_birth: date = Field(..., example="1980-01-01")
    blood_type: Optional[str] = Field(
        None,
        pattern=r"^(A|B|AB|O)[+-]$",
        example="A+",
        description="Blood type in ABO system"
    )

    model_config = ConfigDict(extra="forbid")

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    patient_id: str
    enrolled_programs: List[str] = Field(default_factory=list)
    medical_history: List[str] = Field(default_factory=list)
    created_at: date = Field(default_factory=date.today)

class EnrollmentRequest(BaseModel):
    patient_id: str = Field(..., example="PAT-123456")
    program_id: str = Field(..., example="PROG-abcdef")

class RecommendationResponse(BaseModel):
    program_id: str
    program_name: str
    match_reasons: List[str]

# ======================
# Database Layer
# ======================
class HealthDatabase:
    def __init__(self):
        self._patients = {}
        self._programs = {}
        self._users = {
            "doctor1": hashlib.sha256("password123".encode()).hexdigest()
        }

    # Patients
    def get_patient(self, patient_id: str) -> Optional[Patient]:
        return self._patients.get(patient_id)

    def get_all_patients(self) -> List[Patient]:
        return list(self._patients.values())

    def add_patient(self, patient: Patient) -> None:
        self._patients[patient.patient_id] = patient

    def patient_exists(self, national_id: str) -> bool:
        return any(p.national_id == national_id for p in self._patients.values())

    # Programs
    def get_program(self, program_id: str) -> Optional[Program]:
        return self._programs.get(program_id)

    def get_all_programs(self) -> List[Program]:
        return list(self._programs.values())

    def add_program(self, program: Program) -> None:
        self._programs[program.program_id] = program

    def program_exists(self, name: str) -> bool:
        return any(p.name.lower() == name.lower() for p in self._programs.values())

db = HealthDatabase()

# ======================
# Services
# ======================
class PatientService:
    @staticmethod
    def generate_patient_id(national_id: str) -> str:
        return f"PAT-{national_id[-6:]}"

    @staticmethod
    def calculate_age(date_of_birth: date) -> int:
        today = date.today()
        return today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )

    @classmethod
    def register_patient(cls, patient_data: PatientCreate) -> Patient:
        if db.patient_exists(patient_data.national_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Patient already registered"
            )

        patient_id = cls.generate_patient_id(patient_data.national_id)
        patient = Patient(
            patient_id=patient_id,
            **patient_data.model_dump()
        )
        db.add_patient(patient)
        logger.info(f"Registered new patient: {patient_id}")
        return patient

class ProgramService:
    @staticmethod
    def generate_program_id(name: str) -> str:
        return f"PROG-{hashlib.sha1(name.encode()).hexdigest()[:8]}"

    @classmethod
    def create_program(cls, program_data: ProgramCreate) -> Program:
        if db.program_exists(program_data.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Program already exists"
            )

        program_id = cls.generate_program_id(program_data.name)
        program = Program(
            program_id=program_id,
            **program_data.model_dump()
        )
        db.add_program(program)
        logger.info(f"Created new program: {program_id}")
        return program

class EnrollmentService:
    @staticmethod
    def validate_eligibility(patient: Patient, program: Program) -> bool:
        age = PatientService.calculate_age(patient.date_of_birth)
        if program.target_age_group:
            min_age, max_age = map(int, program.target_age_group.split('-'))
            return min_age <= age <= max_age
        return True

    @classmethod
    def enroll_patient(cls, request: EnrollmentRequest) -> Patient:
        patient = db.get_patient(request.patient_id)
        program = db.get_program(request.program_id)

        if not patient:
            logger.error(f"Patient not found: {request.patient_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )

        if not program:
            logger.error(f"Program not found: {request.program_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found"
            )

        if not cls.validate_eligibility(patient, program):
            logger.warning(
                f"Patient {patient.patient_id} not eligible for program {program.program_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient not eligible for this program"
            )

        if request.program_id not in patient.enrolled_programs:
            patient.enrolled_programs.append(request.program_id)
            logger.info(
                f"Enrolled patient {patient.patient_id} in program {program.program_id}"
            )

        return patient

# ======================
# Exception Handlers
# ======================
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseModel.error(
            message=exc.detail,
            data=None
        ).model_dump()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ResponseModel.error(
            message="Validation error",
            data=exc.errors()
        ).model_dump()
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ResponseModel.error(
            message="Internal server error",
            data=None
        ).model_dump()
    )

# ======================
# API Endpoints
# ======================

# Patients Endpoints
@app.get(
    "/patients",
    response_model=ResponseModel[List[Patient]],
    tags=["Patients"],
    summary="Get all patients"
)
async def get_all_patients(api_key: str = Depends(get_api_key)):
    """Get a list of all registered patients"""
    patients = db.get_all_patients()
    return ResponseModel.success(
        data=patients,
        message=f"Found {len(patients)} patients"
    )

@app.post(
    "/patients",
    response_model=ResponseModel[Patient],
    status_code=status.HTTP_201_CREATED,
    tags=["Patients"],
    summary="Register a new patient"
)
async def register_patient(
    patient: PatientCreate,
    api_key: str = Depends(get_api_key)
):
    """Register a new patient in the system"""
    new_patient = PatientService.register_patient(patient)
    return ResponseModel.success(
        data=new_patient,
        message="Patient registered successfully"
    )

@app.get(
    "/patients/search",
    response_model=ResponseModel[List[Patient]],
    tags=["Patients"],
    summary="Search patients"
)
async def search_patients(
    name: Optional[str] = None,
    program_id: Optional[str] = None,
    api_key: str = Depends(get_api_key)
):
    """Search patients by name or program enrollment"""
    results = []
    for patient in db.get_all_patients():
        if name and name.lower() not in patient.full_name.lower():
            continue
        if program_id and program_id not in patient.enrolled_programs:
            continue
        results.append(patient)
    return ResponseModel.success(
        data=results,
        message=f"Found {len(results)} matching patients"
    )

@app.get(
    "/patients/{patient_id}",
    response_model=ResponseModel[Patient],
    tags=["Patients"],
    summary="Get patient by ID"
)
async def get_patient(
    patient_id: str,
    api_key: str = Depends(get_api_key)
):
    """Get complete patient profile"""
    patient = db.get_patient(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    return ResponseModel.success(
        data=patient,
        message="Patient retrieved"
    )

@app.get(
    "/patients/{patient_id}/recommendations",
    response_model=ResponseModel[List[RecommendationResponse]],
    tags=["Patients"],
    summary="Get program recommendations for patient"
)
async def get_recommendations(
    patient_id: str,
    api_key: str = Depends(get_api_key)
):
    """Get recommended programs for a patient"""
    patient = db.get_patient(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    recommendations = []
    for program in db.get_all_programs():
        if EnrollmentService.validate_eligibility(patient, program):
            recommendations.append(
                RecommendationResponse(
                    program_id=program.program_id,
                    program_name=program.name,
                    match_reasons=["Age appropriate", "Risk factors match"]
                )
            )

    return ResponseModel.success(
        data=recommendations,
        message="Recommendations generated"
    )

# Programs Endpoints
@app.get(
    "/programs",
    response_model=ResponseModel[List[Program]],
    tags=["Programs"],
    summary="Get all programs"
)
async def get_all_programs(api_key: str = Depends(get_api_key)):
    """Get a list of all health programs"""
    programs = db.get_all_programs()
    return ResponseModel.success(
        data=programs,
        message=f"Found {len(programs)} programs"
    )

@app.post(
    "/programs",
    response_model=ResponseModel[Program],
    status_code=status.HTTP_201_CREATED,
    tags=["Programs"],
    summary="Create new program"
)
async def create_program(
    program: ProgramCreate,
    api_key: str = Depends(get_api_key)
):
    """Create a new health program"""
    new_program = ProgramService.create_program(program)
    return ResponseModel.success(
        data=new_program,
        message="Program created successfully"
    )

# Enrollment Endpoints
@app.post(
    "/enroll",
    response_model=ResponseModel[Patient],
    tags=["Enrollments"],
    summary="Enroll patient in program"
)
async def enroll_patient(
    request: EnrollmentRequest,
    api_key: str = Depends(get_api_key)
):
    """Enroll patient in a health program"""
    updated_patient = EnrollmentService.enroll_patient(request)
    return ResponseModel.success(
        data=updated_patient,
        message="Patient enrolled successfully"
    )

# System Endpoints
@app.get(
    "/health",
    response_model=ResponseModel[dict],
    tags=["System"],
    summary="System health check"
)
async def health_check():
    """System health check"""
    return ResponseModel.success(
        data={
            "status": "healthy",
            "patients": len(db.get_all_patients()),
            "programs": len(db.get_all_programs())
        },
        message="System health check"
    )

# ======================
# Startup Event
# ======================
@app.on_event("startup")
async def startup_event():
    """Initialize with sample data"""
    logger.info("Initializing sample data...")

    sample_programs = [
        ProgramCreate(
            name="Diabetes Management",
            program_type=ProgramType.CHRONIC,
            target_age_group="30-80",
            risk_factors=["obesity", "family history"]
        ),
        ProgramCreate(
            name="Child Vaccination Program",
            program_type=ProgramType.PREVENTIVE,
            target_age_group="0-12",
            risk_factors=["low birth weight"]
        )
    ]

    for program in sample_programs:
        ProgramService.create_program(program)

    logger.info("Sample data initialization complete")