import openai
import os
import json
import logging

# Configurar logging para debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cliente OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_sentiment(text):
    """
    Versión mejorada con mejor manejo de errores y logging
    """
    prompt = f"""
Analiza el siguiente texto y devuelve el resultado en formato JSON exacto.

Texto a analizar:
"""{text}"""

Responde SOLO con este formato JSON (sin texto adicional):
{{"sentiment": 0.8, "emotion": "alegría", "confidence": 0.9}}

Donde:
- sentiment: número entre -1 (muy negativo) y 1 (muy positivo)  
- emotion: alegría, tristeza, enojo, miedo, sorpresa, neutral
- confidence: número entre 0 y 1
"""
    
    try:
        logger.info(f"Analizando sentiment para texto de {len(text)} caracteres")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Modelo más confiable y barato
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Muy baja para consistencia
            max_tokens=100    # Suficiente para JSON simple
        )

        content = response.choices[0].message.content.strip()
        logger.info(f"Respuesta OpenAI: {content}")
        
        # Limpiar respuesta (remover markdown si existe)
        if content.startswith('```'):
            content = content.split('\n')[1:-1]
            content = '\n'.join(content)
        
        data = json.loads(content)
        
        sentiment = float(data.get("sentiment", 0))
        emotion = str(data.get("emotion", "neutral"))
        confidence = float(data.get("confidence", 0.5))
        
        logger.info(f"Resultado: sentiment={sentiment}, emotion={emotion}, confidence={confidence}")
        
        return sentiment, emotion, confidence

    except json.JSONDecodeError as e:
        logger.error(f"Error JSON: {e} | Respuesta: {content}")
        return 0.0, "neutral", 0.0
        
    except Exception as e:
        logger.error(f"Error OpenAI: {e}")
        return 0.0, "neutral", 0.0

if __name__ == "__main__":
    # Test del módulo
    test_texts = [
        "The Core School es excelente",
        "No me gusta nada esta escuela", 
        "Es una institución normal"
    ]
    
    for text in test_texts:
        result = analyze_sentiment(text)
        print(f"Texto: {text}")
        print(f"Resultado: {result}")
        print("-" * 30)
