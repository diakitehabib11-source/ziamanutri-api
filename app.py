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
    prompt_effets = f"Tu es un expert médical. Décris les effets de la maladie {maladie} sur le corps humain."
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
    Génère un menu nutritionnel adapté avec des aliments locaux."""
    
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
        "menu_nutritionnel": menu_nutritionnel
    }