from fastapi import APIRouter, HTTPException
from app.models.user import User, UserCreate
from app.db_mock import db_users, user_id_counter

router = APIRouter()

@router.post("/", response_model=User, status_code=201)
def create_user(user: UserCreate):
    """
    Crea un nuevo usuario.
    """
    global user_id_counter
    user_id_counter += 1
    
    # Simula la creación del usuario en la "base de datos"
    new_user = User(
        id=user_id_counter,
        email=user.email,
        full_name=user.full_name,
        is_active=True
    )
    
    db_users[new_user.id] = new_user
    
    return new_user

@router.get("/{user_id}", response_model=User)
def read_user(user_id: int):
    """
    Obtiene un usuario por su ID.
    """
    user = db_users.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user