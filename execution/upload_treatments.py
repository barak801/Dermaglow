import os
import sys
import time
import google.generativeai as genai
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import KnowledgeFile, Treatment

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

TREATMENTS_DATA = [
    {
        "id": 1,
        "name": "Endolifting Facial (Papada y Cuello)",
        "description": "Procedimiento avanzado con Láser CO2 Fraccionado para tensado de piel y rejuvenecimiento facial sin cirugía.",
        "benefits": "Reafirmación inmediata\nEstimulación de colágeno\nSin incisiones visibles\nResultados naturales",
        "duration": "60-90 min",
        "recovery_time": "3-5 días",
        "price_info": "Desde $350",
        "body_parts": "Facial, Papada, Cuello",
        "kb_file": "endolifting.md"
    },
    {
        "id": 2,
        "name": "Endolifting Corporal",
        "description": "Remodelación corporal y tensado cutáneo mediante tecnología láser subdérmica y Láser CO2. Combina BodyTite para resultados superiores.",
        "benefits": "Reducción de grasa localizada\nTensado de la piel\nMejora de la celulitis\nRecuperación rápida",
        "duration": "90-120 min",
        "recovery_time": "4-7 días",
        "price_info": "Desde $350 por zona",
        "body_parts": "Abdomen, Brazos, Piernas, Espalda",
        "kb_file": "endolifting.md"
    },
    {
        "id": 3,
        "name": "Mela minilipo",
        "description": "Mini Extracción Lipídica Ambulatoria. Técnica suave bajo anestesia local ideal para modelado sin hospitalización.",
        "benefits": "Anestesia local únicamente\nRegreso a casa inmediato\nSin quirógrafo mayor\nMínimo dolor",
        "duration": "60 min",
        "recovery_time": "24-48 horas",
        "price_info": "Desde $500",
        "body_parts": "Abdomen bajo, Flancos, Rodillas, Papada",
        "kb_file": "mela_minilipo.md"
    },
    {
        "id": 4,
        "name": "Liposucción con MicroAire",
        "description": "Liposucción de Alta Definición (PAL + RFAL). Utilizamos MicroAire para precisión y BodyTite para máxima retracción de la piel.",
        "benefits": "Alta definición muscular\nMenos moretones y trauma\nPiel firme y tensa\nExtracción de grasa de alta calidad",
        "duration": "2-3 horas",
        "recovery_time": "5-7 días",
        "price_info": "Desde $1800",
        "body_parts": "Abdomen, Cintura, Espalda, Muslos",
        "kb_file": "liposuccion_microaire_bodytite.md"
    },
    {
        "id": 5,
        "name": "Implantes Mamarios",
        "description": "Aumento de busto con implantes de silicona de grado médico de alta cohesividad para un resultado natural y seguro.",
        "benefits": "Prótesis garantizadas de por vida\nHarmonía corporal mejorada\nCicatrices imperceptibles\nAsesoría en volumen personalizado",
        "duration": "90-120 min",
        "recovery_time": "7-10 días",
        "price_info": "Desde $2000",
        "body_parts": "Busto / Senos",
        "kb_file": "implantes_mamarios.md"
    },
    {
        "name": "Quantum RF",
        "description": "Radiofrecuencia Quantum RF para tensado cutáneo no invasivo. Estimula colágeno sin tiempo de recuperación.",
        "benefits": "Cero tiempo de recuperación\nTratamiento indoloro\nEfecto lifting inmediato\nTodo tipo de piel",
        "duration": "45 min",
        "recovery_time": "Inmediata",
        "price_info": "Desde $80 por sesión",
        "body_parts": "Rostro, Abdomen, Glúteos",
        "kb_file": "quantum_rf.md"
    }
]

def upload_to_gemini(file_path):
    print(f"Uploading {file_path} to Gemini...")
    sample_file = genai.upload_file(path=file_path, display_name=os.path.basename(file_path))
    print(f"Uploaded file '{sample_file.display_name}' as: {sample_file.uri}")
    return sample_file

def sync():
    with app.app_context():
        # 1. Update Treatments
        for data in TREATMENTS_DATA:
            t = Treatment.query.filter_by(name=data['name']).first()
            if not t:
                print(f"Creating new treatment: {data['name']}")
                t = Treatment(name=data['name'])
                db.session.add(t)
            
            t.description = data['description']
            t.benefits = data.get('benefits')
            t.duration = data['duration']
            t.recovery_time = data['recovery_time']
            t.price_info = data['price_info']
            t.body_parts = data['body_parts']
            print(f"Updated treatment: {t.name}")
        
        db.session.commit()

        # 2. Upload KB Files and link to KnowledgeFile table
        kb_dir = "directives/treatments"
        kb_files = [f for f in os.listdir(kb_dir) if f.endswith('.md')]
        
        # Clear existing KB references (already done in previous step but being safe)
        KnowledgeFile.query.delete()
        
        for kb_f in kb_files:
            file_path = os.path.join(kb_dir, kb_f)
            gemini_file = upload_to_gemini(file_path)
            
            new_kf = KnowledgeFile(
                filename=f"directives/treatments/{kb_f}",
                gemini_uri=gemini_file.uri,
                gemini_name=gemini_file.name
            )
            db.session.add(new_kf)
            print(f"Saved KB reference: {kb_f} -> {gemini_file.name}")
        
        db.session.commit()
        print("Sync complete!")

if __name__ == "__main__":
    sync()
