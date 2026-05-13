import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/api/nutrition")
async def get_nutrition(request: Request):
    
    try:
        data = await request.json()
    except:
        return JSONResponse(
            content={"error": "Content-Type doit être application/json"},
            status_code=415
        )

    maladie = data.get("maladie")

    if not maladie:
        return JSONResponse(
            content={"error": "Veuillez fournir une maladie"},
            status_code=400
        )
    


    # Effets de la maladie
    prompt_effets = f"Tu es un expert médical. Décris les effets de la maladie {maladie} sur le corps humain en 3 phrases."
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt_effets}]
        )
        effets_maladie = response.choices[0].message.content.strip()
    except Exception as e:
        effets_maladie = str(e)

    # Menu nutritionnel
    try:
        res_menu = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Tu es un expert en nutrition. Le patient souffre de {maladie}. Génère un menu nutritionnel adapté avec des aliments locaux en un seul paragraphe."}]
        )
        menu_nutritionnel = res_menu.choices[0].message.content.strip()
    except Exception as e:
        menu_nutritionnel = "Erreur lors de la génération du menu."
        
    # 3. EXTRACTION (Maintenant que menu_nutritionnel n'est plus vide !)
    try:
        prompt_extraction = f"""Analyse le texte suivant et extrait tous les aliments et fruits mentionnés.
        Réponds UNIQUEMENT en JSON sous ce format : {{"aliments_fruits": ["item1", "item2"]}}
        Texte : {menu_nutritionnel}"""

        res_extraire = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_extraction}],
            response_format={ "type": "json_object" } # Force la sortie JSON
        )
        
        result_json = json.loads(res_extraire.choices[0].message.content)
        aliments_fruits = result_json.get("aliments_fruits", [])
    except Exception:
        aliments_fruits = []

    

   

    return {
        "maladie": maladie,
        "effets_maladie": effets_maladie,
        "menu_nutritionnel": menu_nutritionnel,
        "aliments_fruits": aliments_fruits
    }
    
   
# Endepoint pour le chate Texte
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat/text")
async def chat_text(data: ChatRequest):

    user_message = data.message

    try:

        
        # 1. Détection maladie
    
        prompt_detection = f"""
        Le patient décrit ses symptômes :

        "{user_message}"

        Identifie uniquement la maladie probable.
        Réponds uniquement par le nom de la maladie.
        """

        res_detection = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": prompt_detection}
            ]
        )

        maladie = res_detection.choices[0].message.content.strip()


        
        # 2. Effets maladie
        
        prompt_effets = f"""
        Tu es un expert médical.
        Décris les effets de la maladie {maladie}
        sur le corps humain en 3 phrases.
        """

        res_effets = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": prompt_effets}
            ]
        )

        effets_maladie = res_effets.choices[0].message.content.strip()


        
        # 3. Menu nutritionnel
        
        prompt_menu = f"""
        Tu es un expert en nutrition.

        Le patient souffre de {maladie}.

        Génère un menu nutritionnel adapté
        avec des aliments locaux
        en un seul paragraphe.
        """

        res_menu = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": prompt_menu}
            ]
        )

        menu_nutritionnel = res_menu.choices[0].message.content.strip()


        
        # 4. Extraction aliments
        
        prompt_extraction = f"""
        Analyse le texte suivant et extrait
        tous les aliments et fruits mentionnés.

        Réponds UNIQUEMENT en JSON.

        Format :
        {{
            "aliments_fruits": ["item1", "item2"]
        }}

        Texte :
        {menu_nutritionnel}
        """

        res_extract = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": prompt_extraction}
            ],
            response_format={"type": "json_object"}
        )

        result_json = json.loads(
            res_extract.choices[0].message.content
        )

        aliments_fruits = result_json.get(
            "aliments_fruits",
            []
        )

        # supprimer doublons
        aliments_fruits = list(
            set(
                [a.strip().lower() for a in aliments_fruits]
            )
        )


        
        # Réponse finale
        
        return {
            "maladie": maladie,
            "effets_maladie": effets_maladie,
            "menu_nutritionnel": menu_nutritionnel,
            "aliments_fruits": aliments_fruits
        }

    except Exception as e:

        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )
        
        
# Endpoint pour le chat vocal
from fastapi import UploadFile, File
import tempfile


@app.post("/api/chat/audio")
async def chat_audio(audio: UploadFile = File(...)):

    try:

        
        # 1. Sauvegarde temporaire
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:

            temp_audio.write(await audio.read())

            temp_audio_path = temp_audio.name


        
        # 2. Transcription Whisper
        
        with open(temp_audio_path, "rb") as audio_file:

            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        texte_patient = transcription.text


        
        # 3. Détection maladie
        
        prompt_detection = f"""
        Le patient décrit ses symptômes :

        "{texte_patient}"

        Identifie uniquement la maladie probable.

        Réponds uniquement par le nom de la maladie.
        """

        res_detection = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": prompt_detection}
            ]
        )

        maladie = res_detection.choices[0].message.content.strip()


        
        # 4. Effets maladie
        
        prompt_effets = f"""
        Tu es un expert médical.

        Décris les effets de la maladie
        {maladie}
        sur le corps humain en 3 phrases.
        """

        res_effets = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": prompt_effets}
            ]
        )

        effets_maladie = res_effets.choices[0].message.content.strip()


        
        # 5. Menu nutritionnel
        
        prompt_menu = f"""
        Tu es un expert en nutrition.

        Le patient souffre de {maladie}.

        Génère un menu nutritionnel adapté
        avec des aliments locaux
        en un seul paragraphe.
        """

        res_menu = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": prompt_menu}
            ]
        )

        menu_nutritionnel = res_menu.choices[0].message.content.strip()


        
        # 6. Extraction aliments
        
        prompt_extraction = f"""
        Analyse le texte suivant
        et extrait tous les aliments
        et fruits mentionnés.

        Réponds UNIQUEMENT en JSON.

        Format :
        {{
            "aliments_fruits": ["item1", "item2"]
        }}

        Texte :
        {menu_nutritionnel}
        """

        res_extract = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": prompt_extraction}
            ],
            response_format={"type": "json_object"}
        )

        result_json = json.loads(
            res_extract.choices[0].message.content
        )

        aliments_fruits = result_json.get(
            "aliments_fruits",
            []
        )

        # nettoyage
        aliments_fruits = list(
            set(
                [a.strip().lower() for a in aliments_fruits]
            )
        )


        
        # 7. Supprimer fichier temp
        
        os.remove(temp_audio_path)


        
        # 8. Réponse finale
        
        return {
            "transcription": texte_patient,
            "maladie": maladie,
            "effets_maladie": effets_maladie,
            "menu_nutritionnel": menu_nutritionnel,
            "aliments_fruits": aliments_fruits
        }

    except Exception as e:

        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )