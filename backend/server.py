from fastapi import FastAPI, APIRouter, HTTPException, Depends, File, UploadFile, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from enum import Enum
import json
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create the main app without a prefix
app = FastAPI(title="Bibliothèque Scolaire API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Enums
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    SCHOOL_ADMIN = "school_admin"
    LIBRARIAN = "librarian" 
    TEACHER = "teacher"
    USER = "user"

class SchoolStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved" 
    REJECTED = "rejected"

class BookFormat(str, Enum):
    PHYSICAL = "physical"
    DIGITAL = "digital"
    BOTH = "both"

class LoanStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"  # Demande en attente de validation admin
    APPROVED = "approved"  # Approuvé par admin, en attente de retrait
    RESERVED = "reserved"  # Réservé (ancien système - garde pour compatibilité)
    BORROWED = "borrowed"  # Emprunté
    RETURNED = "returned"  # Rendu, en attente de validation du rapport
    COMPLETED = "completed"  # Rapport validé par admin, processus terminé
    REJECTED = "rejected"  # Demande rejetée par admin
    OVERDUE = "overdue"

# Pydantic Models
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str
    school_id: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    verified: bool = False
    school_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SchoolBase(BaseModel):
    name: str
    address: str
    country: str = "France"
    description: Optional[str] = None

class SchoolCreate(SchoolBase):
    admin_email: EmailStr
    admin_name: str
    admin_password: str

class School(SchoolBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: SchoolStatus = SchoolStatus.PENDING
    admin_user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BookBase(BaseModel):
    title: str
    authors: List[str]
    isbn: Optional[str] = None
    description: Optional[str] = None
    categories: List[str] = []
    language: str = "fr"
    format: BookFormat = BookFormat.PHYSICAL
    price: Optional[float] = 0.0
    cover_image: Optional[str] = None
    file_path: Optional[str] = None

class BookCreate(BookBase):
    school_id: str
    physical_copies: int = 0

class Book(BookBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    school_id: str
    published_by_user: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BookCopy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    book_id: str
    barcode: Optional[str] = None
    condition: str = "good"
    status: str = "available"  # available, borrowed, reserved, damaged
    location: Optional[str] = None

class LoanBase(BaseModel):
    book_id: str
    copy_id: Optional[str] = None
    user_id: str
    due_date: datetime

class LoanCreate(LoanBase):
    pass

class LoanStatusUpdate(BaseModel):
    status: LoanStatus
    admin_notes: Optional[str] = None

class Loan(LoanBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: LoanStatus = LoanStatus.PENDING_APPROVAL
    borrowed_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    return_report: Optional[str] = None  # Rapport de retour soumis par l'utilisateur
    admin_notes: Optional[str] = None  # Notes de l'admin lors de validation
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="Utilisateur introuvable")
        
        return User(**user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, dict):
                data[key] = prepare_for_mongo(value)
            elif isinstance(value, list):
                data[key] = [prepare_for_mongo(item) if isinstance(item, dict) else item for item in value]
    return data

def parse_from_mongo(item):
    """Parse datetime strings from MongoDB"""
    if isinstance(item, dict):
        for key, value in item.items():
            if isinstance(value, str) and key.endswith(('_at', '_date')) and 'T' in value:
                try:
                    item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    pass
            elif isinstance(value, dict):
                item[key] = parse_from_mongo(value)
            elif isinstance(value, list):
                item[key] = [parse_from_mongo(v) if isinstance(v, dict) else v for v in value]
    return item

# Authentication endpoints
@api_router.post("/auth/register", response_model=User)
async def register_user(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Un utilisateur avec cet email existe déjà")
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    user_dict = user_data.dict(exclude={"password"})
    user = User(**user_dict)
    
    # Prepare for MongoDB with password hash
    user_mongo = prepare_for_mongo(user.dict())
    user_mongo["password_hash"] = hashed_password
    await db.users.insert_one(user_mongo)
    
    return user

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    # Find user
    user = await db.users.find_one({"email": user_data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    # Verify password
    if not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    # Create access token
    access_token = create_access_token(data={"sub": user["id"]})
    
    user_obj = User(**parse_from_mongo(user))
    return Token(access_token=access_token, user=user_obj)

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# School endpoints
@api_router.post("/schools", response_model=School)
async def create_school(school_data: SchoolCreate):
    # Check if school exists
    existing_school = await db.schools.find_one({"name": school_data.name})
    if existing_school:
        raise HTTPException(status_code=400, detail="Une école avec ce nom existe déjà")
    
    # Create admin user
    hashed_password = hash_password(school_data.admin_password)
    admin_user = User(
        email=school_data.admin_email,
        full_name=school_data.admin_name,
        role=UserRole.SCHOOL_ADMIN,
        verified=False
    )
    
    admin_dict = admin_user.dict()
    admin_dict["password_hash"] = hashed_password
    admin_mongo = prepare_for_mongo(admin_dict)
    await db.users.insert_one(admin_mongo)
    
    # Create school
    school_dict = school_data.dict(exclude={"admin_email", "admin_name", "admin_password"})
    school = School(**school_dict, admin_user_id=admin_user.id)
    
    # Update admin user with school_id
    await db.users.update_one({"id": admin_user.id}, {"$set": {"school_id": school.id}})
    
    school_mongo = prepare_for_mongo(school.dict())
    await db.schools.insert_one(school_mongo)
    
    return school

@api_router.get("/schools", response_model=List[School])
async def get_schools(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.SUPER_ADMIN:
        # Non-admin users can only see approved schools
        schools = await db.schools.find({"status": SchoolStatus.APPROVED}).to_list(length=None)
    else:
        # Admin can see all schools
        schools = await db.schools.find().to_list(length=None)
    
    return [School(**parse_from_mongo(school)) for school in schools]

@api_router.put("/schools/{school_id}/status")
async def update_school_status(school_id: str, status: SchoolStatus, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Seuls les super administrateurs peuvent modifier le statut des écoles")
    
    result = await db.schools.update_one({"id": school_id}, {"$set": {"status": status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="École introuvable")
    
    # If approved, verify the admin user
    if status == SchoolStatus.APPROVED:
        school = await db.schools.find_one({"id": school_id})
        await db.users.update_one({"id": school["admin_user_id"]}, {"$set": {"verified": True}})
    
    return {"message": "Statut de l'école mis à jour"}

# Book endpoints
@api_router.post("/books", response_model=Book)
async def create_book(book_data: BookCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.LIBRARIAN, UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à créer des livres")
    
    # Use current user's school_id if not provided
    if current_user.school_id:
        book_data.school_id = current_user.school_id
    
    book_dict = book_data.dict(exclude={"physical_copies"})
    book = Book(**book_dict, published_by_user=current_user.id)
    
    book_mongo = prepare_for_mongo(book.dict())
    await db.books.insert_one(book_mongo)
    
    # Create physical copies if specified
    if book_data.physical_copies > 0 and book_data.format in [BookFormat.PHYSICAL, BookFormat.BOTH]:
        copies = []
        for i in range(book_data.physical_copies):
            copy = BookCopy(book_id=book.id, barcode=f"{book.id}-{i+1:03d}")
            copies.append(prepare_for_mongo(copy.dict()))
        
        await db.book_copies.insert_many(copies)
    
    return book

@api_router.get("/books", response_model=List[Book])
async def get_books(
    search: Optional[str] = None,
    category: Optional[str] = None,
    format: Optional[BookFormat] = None,
    school_id: Optional[str] = None
):
    query = {}
    
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"authors": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    if category:
        query["categories"] = {"$in": [category]}
    
    if format:
        query["format"] = format
    
    if school_id:
        query["school_id"] = school_id
    
    books = await db.books.find(query).to_list(length=None)
    return [Book(**parse_from_mongo(book)) for book in books]

@api_router.get("/books/{book_id}", response_model=Book)
async def get_book(book_id: str):
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Livre introuvable")
    
    return Book(**parse_from_mongo(book))

@api_router.put("/books/{book_id}", response_model=Book)
async def update_book(book_id: str, book_data: BookCreate, current_user: User = Depends(get_current_user)):
    # Check if book exists
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Livre introuvable")
    
    # Check permissions
    if book["published_by_user"] != current_user.id and current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.LIBRARIAN]:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à modifier ce livre")
    
    # Update book data
    update_data = book_data.dict(exclude={"physical_copies"})
    update_data = prepare_for_mongo(update_data)
    
    await db.books.update_one({"id": book_id}, {"$set": update_data})
    
    # Get updated book
    updated_book = await db.books.find_one({"id": book_id})
    return Book(**parse_from_mongo(updated_book))

@api_router.delete("/books/{book_id}")
async def delete_book(book_id: str, current_user: User = Depends(get_current_user)):
    # Check if book exists
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Livre introuvable")
    
    # Check permissions
    if book["published_by_user"] != current_user.id and current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.LIBRARIAN]:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à supprimer ce livre")
    
    # Delete associated copies
    await db.book_copies.delete_many({"book_id": book_id})
    
    # Delete loans associated with this book
    await db.loans.delete_many({"book_id": book_id})
    
    # Delete the book
    await db.books.delete_one({"id": book_id})
    
    return {"message": "Livre supprimé avec succès"}

# Loan endpoints
@api_router.post("/loans", response_model=Loan)
async def create_loan(loan_data: LoanCreate, current_user: User = Depends(get_current_user)):
    # Check if book exists
    book = await db.books.find_one({"id": loan_data.book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Livre introuvable")
    
    # For physical books, find available copy
    if book["format"] in [BookFormat.PHYSICAL, BookFormat.BOTH]:
        available_copy = await db.book_copies.find_one({
            "book_id": loan_data.book_id,
            "status": "available"
        })
        if not available_copy:
            raise HTTPException(status_code=400, detail="Aucun exemplaire disponible")
        
        loan_data.copy_id = available_copy["id"]
        # Reserve the copy
        await db.book_copies.update_one(
            {"id": available_copy["id"]},
            {"$set": {"status": "reserved"}}
        )
    
    # Create loan
    loan = Loan(**loan_data.dict(), user_id=current_user.id)
    loan_mongo = prepare_for_mongo(loan.dict())
    await db.loans.insert_one(loan_mongo)
    
    return loan

@api_router.get("/loans/my", response_model=List[Loan])
async def get_my_loans(current_user: User = Depends(get_current_user)):
    loans = await db.loans.find({"user_id": current_user.id}).to_list(length=None)
    return [Loan(**parse_from_mongo(loan)) for loan in loans]

@api_router.get("/loans", response_model=List[Loan])
async def get_all_loans(current_user: User = Depends(get_current_user)):
    # Only admins and librarians can see all loans
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.SCHOOL_ADMIN, UserRole.LIBRARIAN]:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    # School admins and librarians only see loans for books from their school
    if current_user.role in [UserRole.SCHOOL_ADMIN, UserRole.LIBRARIAN]:
        # Get all books from the user's school
        school_books = await db.books.find({"school_id": current_user.school_id}).to_list(length=None)
        book_ids = [book["id"] for book in school_books]
        loans = await db.loans.find({"book_id": {"$in": book_ids}}).to_list(length=None)
    else:
        # Super admin can see all loans
        loans = await db.loans.find({}).to_list(length=None)
    
    return [Loan(**parse_from_mongo(loan)) for loan in loans]

@api_router.put("/loans/{loan_id}/status")
async def update_loan_status(loan_id: str, status: LoanStatus, current_user: User = Depends(get_current_user)):
    loan = await db.loans.find_one({"id": loan_id})
    if not loan:
        raise HTTPException(status_code=404, detail="Emprunt introuvable")
    
    # Check permissions
    if current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.LIBRARIAN] and loan["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à modifier cet emprunt")
    
    update_data = {"status": status}
    
    if status == LoanStatus.BORROWED:
        update_data["borrowed_at"] = datetime.now(timezone.utc).isoformat()
        # Update copy status
        if loan["copy_id"]:
            await db.book_copies.update_one(
                {"id": loan["copy_id"]},
                {"$set": {"status": "borrowed"}}
            )
    elif status == LoanStatus.RETURNED:
        update_data["returned_at"] = datetime.now(timezone.utc).isoformat()
        # Update copy status
        if loan["copy_id"]:
            await db.book_copies.update_one(
                {"id": loan["copy_id"]},
                {"$set": {"status": "available"}}
            )
    
    result = await db.loans.update_one({"id": loan_id}, {"$set": update_data})
    
    return {"message": "Statut de l'emprunt mis à jour"}

# File upload endpoint (for digital books)
@api_router.post("/books/{book_id}/upload-file")
async def upload_book_file(
    book_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Check if book exists and user has permission
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Livre introuvable")
    
    if book["published_by_user"] != current_user.id and current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.LIBRARIAN]:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à modifier ce livre")
    
    # Check file type
    if not file.filename.endswith(('.pdf', '.epub')):
        raise HTTPException(status_code=400, detail="Format de fichier non supporté. Utilisez PDF ou EPUB.")
    
    # Create uploads directory if it doesn't exist
    uploads_dir = Path("uploads/books")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = uploads_dir / f"{book_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Update book with file path
    await db.books.update_one(
        {"id": book_id},
        {"$set": {"file_path": str(file_path)}}
    )
    
    return {"message": "Fichier uploadé avec succès", "file_path": str(file_path)}

# Book reservation endpoint (for physical books) - Now creates approval request
@api_router.post("/loans/request")
async def request_book_loan(
    request_data: dict,
    current_user: User = Depends(get_current_user)
):
    book_id = request_data.get("book_id")
    if not book_id:
        raise HTTPException(status_code=400, detail="book_id requis")
    
    # Check if book exists
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Livre introuvable")
    
    # Only for physical books
    if book["format"] not in [BookFormat.PHYSICAL, BookFormat.BOTH]:
        raise HTTPException(status_code=400, detail="Ce livre n'est pas disponible en format physique")
    
    # Check if user already has an active request/loan for this book
    existing_loan = await db.loans.find_one({
        "book_id": book_id,
        "user_id": current_user.id,
        "status": {"$in": [LoanStatus.PENDING_APPROVAL, LoanStatus.APPROVED, LoanStatus.RESERVED, LoanStatus.BORROWED]}
    })
    if existing_loan:
        raise HTTPException(status_code=400, detail="Vous avez déjà une demande ou un emprunt actif pour ce livre")
    
    # Check if there are available copies
    available_copies_count = await db.book_copies.count_documents({
        "book_id": book_id,
        "status": "available"
    })
    if available_copies_count == 0:
        raise HTTPException(status_code=400, detail="Aucun exemplaire disponible pour ce livre")
    
    # Create loan request with pending approval status
    due_date = datetime.now(timezone.utc) + timedelta(days=14)  # 14 days loan period
    loan = Loan(
        book_id=book_id,
        copy_id=None,  # Will be assigned when approved
        user_id=current_user.id,
        due_date=due_date,
        status=LoanStatus.PENDING_APPROVAL
    )
    
    # Insert loan request
    loan_mongo = prepare_for_mongo(loan.dict())
    await db.loans.insert_one(loan_mongo)
    
    return {
        "message": "Demande d'emprunt soumise avec succès. En attente de validation par un administrateur.",
        "loan_id": loan.id,
        "status": "pending_approval",
        "book_title": book["title"]
    }

# Book download endpoint (for digital books)
@api_router.post("/books/{book_id}/download")
async def download_book(book_id: str, current_user: User = Depends(get_current_user)):
    # Check if book exists
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Livre introuvable")
    
    # Only for digital books
    if book["format"] not in [BookFormat.DIGITAL, BookFormat.BOTH]:
        raise HTTPException(status_code=400, detail="Ce livre n'est pas disponible en format numérique")
    
    # Check if book has a file
    if not book.get("file_path"):
        raise HTTPException(status_code=404, detail="Fichier non disponible pour ce livre")
    
    # Check if file exists
    file_path = Path(book["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouvé sur le serveur")
    
    # Since books are free, we'll create a download record for tracking
    download_record = {
        "id": str(uuid.uuid4()),
        "book_id": book_id,
        "user_id": current_user.id,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "book_title": book["title"]
    }
    
    # Insert download record (optional, for analytics)
    try:
        await db.downloads.insert_one(download_record)
    except Exception:
        pass  # Don't fail download if logging fails
    
    # For now, return the file path (in production, you'd use signed URLs)
    return {
        "message": "Livre prêt pour téléchargement",
        "download_url": f"/api/books/{book_id}/file",
        "book_title": book["title"],
        "file_size": file_path.stat().st_size if file_path.exists() else 0
    }

# Serve book files
@api_router.get("/books/{book_id}/file")
async def serve_book_file(book_id: str, current_user: User = Depends(get_current_user)):
    # Check if book exists
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Livre introuvable")
    
    # Check if book has a file
    if not book.get("file_path"):
        raise HTTPException(status_code=404, detail="Fichier non disponible")
    
    file_path = Path(book["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    # Determine the media type
    media_type = "application/pdf" if file_path.suffix.lower() == ".pdf" else "application/epub+zip"
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=f"{book['title']}.{file_path.suffix.lower().lstrip('.')}",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{book['title']}.{file_path.suffix.lower().lstrip('.')}"}
    )

# Dashboard endpoints
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    stats = {}
    
    if current_user.role == UserRole.SUPER_ADMIN:
        stats["total_schools"] = await db.schools.count_documents({})
        stats["pending_schools"] = await db.schools.count_documents({"status": SchoolStatus.PENDING})
        stats["total_users"] = await db.users.count_documents({})
        stats["total_books"] = await db.books.count_documents({})
        stats["total_loans"] = await db.loans.count_documents({})
    
    elif current_user.role in [UserRole.SCHOOL_ADMIN, UserRole.LIBRARIAN]:
        stats["school_books"] = await db.books.count_documents({"school_id": current_user.school_id})
        stats["active_loans"] = await db.loans.count_documents({
            "status": {"$in": [LoanStatus.BORROWED, LoanStatus.RESERVED]},
            "$or": [
                {"book_id": {"$in": [book["id"] for book in await db.books.find({"school_id": current_user.school_id}).to_list(None)]}},
            ]
        })
        stats["total_copies"] = await db.book_copies.count_documents({
            "book_id": {"$in": [book["id"] for book in await db.books.find({"school_id": current_user.school_id}).to_list(None)]}
        })
    
    else:
        stats["my_loans"] = await db.loans.count_documents({"user_id": current_user.id})
        stats["active_loans"] = await db.loans.count_documents({
            "user_id": current_user.id,
            "status": {"$in": [LoanStatus.BORROWED, LoanStatus.RESERVED]}
        })
    
    return stats

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()