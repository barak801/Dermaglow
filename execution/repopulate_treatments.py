import os
import sys

# Add the project directory to sys.path to import app and models
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_dir)

from app import app, db
from models import Treatment

def repopulate():
    with app.app_context():
        # 1. Ensure the body_parts column exists (Manual Migration for SQLite)
        try:
            db.session.execute(db.text("ALTER TABLE treatments ADD COLUMN body_parts TEXT"))
            db.session.commit()
            print("Added body_parts column to treatments table.")
        except Exception as e:
            # Column likely already exists
            db.session.rollback()
            print(f"Note: Column body_parts might already exist or error occurred: {e}")

        # 2. Clear existing treatments (as per user request to 'recover' from deletion, 
        # but safely we'll just delete all and re-insert to ensure latest info)
        Treatment.query.delete()
        print("Cleared existing treatments.")

        # 3. Define optimized treatment data
        treatments = [
            {
                "name": "Endolifting Facial",
                "category": "Mínimamente Invasivo / Estética Facial",
                "description": "Procedimiento avanzado que utiliza tecnología láser interna para retraer la piel, eliminar grasa localizada y estimular la producción de colágeno desde el interior.",
                "benefits": "Rejuvenecimiento sin cirugía\nReducción de papada y flacidez\nRedefinición del óvalo facial\nResultados naturales y duraderos",
                "duration": "45-60 min",
                "recovery_time": "2-3 días",
                "preparation": "Venir con el rostro limpio, sin maquillaje. Evitar exposición solar intensa 48h antes.",
                "body_parts": "Rostro completo\nPapada\nCuello\nLínea mandibular",
                "price_info": "Valor de evaluación: $30 (Abonables al tratamiento)"
            },
            {
                "name": "Endolifting Corporal",
                "category": "Mínimamente Invasivo / Estética Corporal",
                "description": "Aplicación de láser subdérmico para tensado cutáneo y reducción de tejido adiposo en zonas rebeldes del cuerpo.",
                "benefits": "Combate la flacidez corporal\nMejora la textura de la piel\nReduce medidas en zonas específicas\nSin cicatrices visibles",
                "duration": "60-90 min",
                "recovery_time": "3-5 días",
                "preparation": "Usar ropa cómoda. Hidratación adecuada los días previos.",
                "body_parts": "Abdomen y flancos\nBrazos (cara interna)\nMuslos y entrepierna\nRodillas",
                "price_info": "Valor de evaluación: $30 (Abonables al tratamiento)"
            },
            {
                "name": "Mela minilipo",
                "category": "Mínimamente Invasivo / Modelado Corporal",
                "description": "Mini Extracción Lipídica Ambulatoria. Técnica de succión de grasa localizada realizada bajo anestesia local, ideal para modelado sin hospitalización.",
                "benefits": "Procedimiento ambulatorio (salida inmediata)\nRecuperación ultrarrápida\nResultados visibles en pocos días\nAnestesia local únicamente",
                "duration": "1-2 horas",
                "recovery_time": "24-48 horas",
                "preparation": "Ayuno ligero de 4-6 horas. Exámenes básicos de sangre si se requiere.",
                "body_parts": "Abdomen alto y bajo\nCintura (flancos)\nEspalda (rollito del sostén)\nBrazos",
                "price_info": "Valor de evaluación: $30 (Abonables al tratamiento)"
            },
            {
                "name": "Liposucción con MicroAire",
                "category": "Quirúrgico / Alta Definición",
                "description": "Liposucción asistida por potencia (PAL) que utiliza cánulas vibratorias para una extracción de grasa más suave, precisa y con menor trauma tisular.",
                "benefits": "Mayor definición muscular (High Def)\nMenos moretones e inflamación\nExtracción de mayor volumen de grasa\nRecuperación más cómoda que lipo tradicional",
                "duration": "2-4 horas",
                "recovery_time": "7-10 días",
                "preparation": "Ayuno completo (8h). Valoración anestesiológica previa. Exámenes preoperatorios completos.",
                "body_parts": "Zonas múltiples\nAbdomen HD\nEspalda completa\nPiernas y glúteos",
                "price_info": "Valor de evaluación: $30 (Abonables al tratamiento)"
            },
            {
                "name": "Implantes Mamarios",
                "category": "Quirúrgico / Estética Mamaria",
                "description": "Cirugía de aumento de busto mediante la colocación de prótesis de alta calidad para mejorar el volumen, la forma y la proyección de los senos.",
                "benefits": "Mejora la armonía corporal\nPrótesis de marcas líderes garantizadas\nRecuperación supervisada\nAumento de la confianza personal",
                "duration": "1-2 horas",
                "recovery_time": "3-5 semanas (actividad total)",
                "preparation": "Ayuno de 8 horas. No fumar 2 semanas antes. Exámenes preoperatorios y ecografía mamaria.",
                "body_parts": "Senos / Mamas",
                "price_info": "Valor de evaluación: $30 (Abonables al tratamiento)"
            }
        ]

        # 4. Insert data
        for t_data in treatments:
            t = Treatment(**t_data)
            db.session.add(t)
        
        db.session.commit()
        print("Success: 5 treatments repopulated successfully.")

if __name__ == "__main__":
    repopulate()
