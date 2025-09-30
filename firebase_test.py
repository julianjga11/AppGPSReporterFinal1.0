import firebase_admin
from firebase_admin import credentials, firestore

# 1️⃣ Cargar credenciales desde el archivo JSON
cred = credentials.Certificate(r"C:\Users\julia\Downloads\ReportApp1-main\ReportApp1-main\firebase_key.json")
firebase_admin.initialize_app(cred)

# 2️⃣ Conectarse a Firestore
db = firestore.client()

# 3️⃣ Escribir un documento de prueba
doc_ref = db.collection("test").document("prueba1")
doc_ref.set({
    "mensaje": "Hola desde mi servidor 🚀",
    "estado": "conectado"
})

print("✅ Conexión a Firebase exitosa y documento creado en Firestore.")
