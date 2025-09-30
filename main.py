from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import base64
from PIL import Image
from io import BytesIO

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, firestore

# 📌 Ruta absoluta al archivo firebase_key.json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cred_path = os.path.join(BASE_DIR, "firebase_key.json")

# Inicializar Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Crear la aplicación FastAPI
app = FastAPI(
    title="Reportes GPS API",
    description="API para recibir y servir reportes con coordenadas GPS y fotos (Firestore)",
    version="2.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos
class ReporteCreate(BaseModel):
    latitud: float
    longitud: float
    timestamp: Optional[str] = None
    foto_base64: Optional[str] = None
    descripcion: Optional[str] = None
    tipo_reporte: Optional[str] = "general"

class ReporteResponse(BaseModel):
    id: str
    latitud: float
    longitud: float
    timestamp: str
    foto_base64: str
    descripcion: Optional[str]
    tipo_reporte: str

# Carpeta para imágenes
IMAGES_FOLDER = os.path.join(BASE_DIR, "imagenes_reportes")
os.makedirs(IMAGES_FOLDER, exist_ok=True)

# Montar carpeta de imágenes como estáticos
app.mount("/imagenes_reportes", StaticFiles(directory=IMAGES_FOLDER), name="imagenes_reportes")

# Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head><title>Reportes GPS API</title></head>
        <body>
            <h1>🗺️ API de Reportes GPS</h1>
            <p>Bienvenido a la API con Firestore 🚀</p>
            <ul>
                <li><a href="/docs">📚 Documentación Swagger</a></li>
                <li><a href="/mapa">🗺️ Ver Mapa de Reportes</a></li>
                <li><a href="/reportes">📊 Ver Reportes (JSON)</a></li>
            </ul>
        </body>
    </html>
    """

@app.get("/mapa", response_class=HTMLResponse)
async def mapa():
    try:
        with open(os.path.join(BASE_DIR, "mapa.html"), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error: archivo mapa.html no encontrado</h1>"

@app.post("/reportes/", response_model=ReporteResponse)
async def crear_reporte(reporte: ReporteCreate):
    try:
        current_time = datetime.now()
        if not reporte.timestamp:
            reporte.timestamp = current_time.isoformat()
        else:
            try:
                current_time = datetime.fromisoformat(reporte.timestamp)
            except ValueError:
                current_time = datetime.now()

        # Guardar imagen
        ruta_imagen = ""
        if reporte.foto_base64:
            try:
                image_data = base64.b64decode(reporte.foto_base64)
                image = Image.open(BytesIO(image_data))
                image_filename = f"{int(datetime.timestamp(current_time))}.jpg"
                image_path = os.path.join(IMAGES_FOLDER, image_filename)
                image.save(image_path, format="JPEG")
                ruta_imagen = f"imagenes_reportes/{image_filename}"
            except Exception as img_err:
                raise HTTPException(status_code=400, detail=f"Error al procesar la imagen: {img_err}")

        # Guardar en Firestore
        doc_ref = db.collection("reportes").document()
        doc_ref.set({
            "latitud": reporte.latitud,
            "longitud": reporte.longitud,
            "timestamp": current_time.isoformat(),
            "foto_base64": ruta_imagen,
            "descripcion": reporte.descripcion,
            "tipo_reporte": reporte.tipo_reporte,
            "created_at": datetime.now().isoformat()
        })

        return ReporteResponse(
            id=doc_ref.id,
            latitud=reporte.latitud,
            longitud=reporte.longitud,
            timestamp=current_time.isoformat(),
            foto_base64=ruta_imagen,
            descripcion=reporte.descripcion,
            tipo_reporte=reporte.tipo_reporte or "general"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/reportes/", response_model=List[ReporteResponse])
async def obtener_reportes():
    try:
        docs = db.collection("reportes").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
        reportes = []
        for doc in docs:
            data = doc.to_dict()
            reportes.append(ReporteResponse(
                id=doc.id,
                latitud=data.get("latitud", 0.0),
                longitud=data.get("longitud", 0.0),
                timestamp=data.get("timestamp", ""),
                foto_base64=data.get("foto_base64", ""),
                descripcion=data.get("descripcion", ""),
                tipo_reporte=data.get("tipo_reporte", "general")
            ))
        return reportes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/stats")
async def estadisticas():
    try:
        total = len(list(db.collection("reportes").stream()))
        ultimo_doc = db.collection("reportes").order_by("created_at", direction=firestore.Query.DESCENDING).limit(1).stream()
        ultimo = None
        for doc in ultimo_doc:
            ultimo = doc.to_dict().get("timestamp", None)
        return {
            "total_reportes": total,
            "ultimo_reporte": ultimo
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
import os

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
