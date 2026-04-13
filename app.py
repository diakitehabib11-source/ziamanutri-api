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
    prompt_menu = f"""Tu es un expert en nutrition.
    Le patient souffre de {maladie}.
    Génère un menu nutritionnel adapté avec des aliments locaux en un seul paragraphe."""
    
    # Les aliments et fruits sités dans le menu nutritionnel
    # =========================
    # Extraction des aliments
    # =========================
    prompt_aliments = f"""
    À partir du texte suivant, liste uniquement les aliments (hors fruits) séparés par des virgules.

    Texte : {menu_nutritionnel}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt_aliments}]
        )
        aliments_text = response.choices[0].message.content.strip()

        # transformer en liste
        aliments = [a.strip() for a in aliments_text.split(",") if a.strip()]
    except Exception as e:
        aliments = []


    # =========================
    # Extraction des fruits
    # =========================
    prompt_fruits = f"""
    À partir du texte suivant, liste uniquement les fruits séparés par des virgules.

    Texte : {menu_nutritionnel}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt_fruits}]
        )
        fruits_text = response.choices[0].message.content.strip()

        # transformer en liste
        fruits = [f.strip() for f in fruits_text.split(",") if f.strip()]
    except Exception as e:
        fruits = []

    

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt_menu}]
        )
        menu_nutritionnel = response.choices[0].message.content.strip()
    except Exception as e:
        menu_nutritionnel = str(e)

    return {
        "maladie": maladie,
        "effets_maladie": effets_maladie,
        "menu_nutritionnel": menu_nutritionnel,
        "aliments": aliments,
        "fruits": fruits
    }