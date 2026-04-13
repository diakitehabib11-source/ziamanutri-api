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