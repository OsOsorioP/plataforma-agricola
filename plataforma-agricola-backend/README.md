# Agrosmi Backend

Este es el backend de **Agrosmi** 

### Tecnologías
- [FastAPI](https://fastapi.tiangolo.com/) → Framework backend (APIs rápidas y con docs automáticas).  
- [LangChain](https://www.langchain.com/) → Orquestación de agentes conversacionales.  
- [PostgreSQL](https://www.postgresql.org/) → Base de datos relacional.  
- [SQLAlchemy](https://www.sqlalchemy.org/) → ORM para gestión de la BD.  

### Estructura del proyecto

### Instalación y configuración

1. **Clonar el repositorio**
```bash
   git clone https://github.com/<tu-usuario>/plataforma-agricola.git
   cd plataforma-agricola-backend
```
2. **Crear entorno virtual**
```bash
    python -m venv venv
    source venv/bin/activate   # Linux/Mac
    venv\Scripts\activate      # Windows
```
3. **Instalar dependencias**
```bash
   pip install -r requirements.txt
```
4. **Configurar variables de entorno**
    DATABASE_URL=postgresql://usuario:password@localhost:5432/agriagent
    SECRET_KEY=tu_clave_secreta
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
5. **Ejecutar migraciones de BD**
```bash
    alembic upgrade head
```
6. **Iniciar servidor**
```bash
uvicorn app.main:app --reload
```
7. **Abrir documentación**
    endpoint: http://localhost:8000/docs

### Checklist
- [x] Modelos de usuario y parcela
- [x] Conexión a base de datos
- [X] Seguridad OAuth (autorización)
- [x] Arquitectura de Enrutamiento de Agentes
- [x] Sistema de multiagentes
- [x] Retrieval-Augmented Generation (RAG)
- [x] Agentes multimodal
- [ ] Fine-tuning
- [ ] Sistema de alertas
- [x] API's para los agentes
- [ ] Agroclimatico, imagenes saltelites
- [ ] Comunicación Inter-Agente
- [ ] Memoria a largo plazo y personalización
- [ ] Acciones en el mundo real (agentes activos)
