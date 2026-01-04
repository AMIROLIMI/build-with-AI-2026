from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
# Try to load from backend directory first, then from project root
env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
print(f"🔍 Looking for .env file at: {env_path}")
print(f"   .env file exists: {env_path.exists()}")
if env_path.exists():
    print(f"   ✅ .env file found, loading variables...")
else:
    print(f"   ⚠️ .env file not found, using system environment variables")

app = FastAPI(title="Real Estate Dashboard API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
MODEL_PATH = Path(r"C:\Users\oamir\Desktop\Build with AI 2026\artifacts\catboost_rmse128_r877.pkl")
CSV_PATH = BASE_DIR / "Notebooks" / "somon_ml_clear_amir3.csv"
GRAPHS_PATH = Path(r"C:\Users\oamir\Desktop\Build with AI 2026\Notebooks\graphs")

# OpenAI API - load from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
print(f"🔑 OpenAI API Key loaded: {'Yes' if OPENAI_API_KEY else 'No'} (length: {len(OPENAI_API_KEY) if OPENAI_API_KEY else 0})")
if OPENAI_API_KEY:
    print(f"   Key starts with: {OPENAI_API_KEY[:10]}...")
try:
    if OPENAI_API_KEY:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI client initialized successfully")
    else:
        openai_client = None
        print("⚠️ OpenAI API key not provided")
        print(f"   Current working directory: {os.getcwd()}")
        print(f"   .env file should be at: {Path(__file__).parent / '.env'}")
        print(f"   .env file exists: {(Path(__file__).parent / '.env').exists()}")
except Exception as e:
    openai_client = None
    print(f"❌ Failed to initialize OpenAI client: {e}")
    import traceback
    traceback.print_exc()

# Feature importance (from model analysis - exact values)
FEATURE_IMPORTANCE = {
    "area_m2": 30.173527,
    "renovation": 18.376194,
    "heating": 13.209384,
    "district": 12.669100,
    "floor": 10.571874,
    "rooms": 4.431513,
    "condition": 3.891500,
    "techpassport": 3.405732,
    "build_type": 1.635607,
    "bathroom": 1.635568
}

# Load model
model = None
df_cache = None

def load_models():
    global model
    try:
        if MODEL_PATH.exists():
            model = joblib.load(MODEL_PATH)
            print(f"✅ Model loaded: {type(model).__name__}")
            print(f"   Model path: {MODEL_PATH}")
        else:
            print(f"❌ Model not found at {MODEL_PATH}")
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        import traceback
        traceback.print_exc()
        raise

def load_dataframe():
    """Load and cache CSV dataframe"""
    global df_cache
    try:
        if CSV_PATH.exists():
            df_cache = pd.read_csv(CSV_PATH)
            print(f"✅ CSV loaded: {len(df_cache)} records")
        else:
            print(f"⚠️ CSV not found at {CSV_PATH}")
            df_cache = None
    except Exception as e:
        print(f"⚠️ Error loading CSV: {e}")
        df_cache = None

load_models()
load_dataframe()

# Request models
class PredictionRequest(BaseModel):
    rooms: int
    area_m2: float
    floor: int
    district: str
    build_type: str
    renovation: str
    bathroom: str
    heating: str
    condition: str
    techpassport: str
    price: float | None = None  # Optional for sale prediction

# Districts mapping
DISTRICTS = ["Сино", "Фирдавси", "Шохмансур", "И. Сомони", "Другое"]

def prepare_features(data: dict):
    """Prepare features for model prediction"""
    try:
        # Create DataFrame with all features in correct order
        # CatBoost handles categorical features directly
        df = pd.DataFrame([{
            'rooms': int(data['rooms']),
            'area_m2': float(data['area_m2']),
            'floor': int(data['floor']),
            'district': str(data['district']),
            'build_type': str(data['build_type']),
            'renovation': str(data['renovation']),
            'bathroom': str(data['bathroom']),
            'heating': str(data['heating']),
            'condition': str(data['condition']),
            'techpassport': str(data['techpassport'])
        }])
        
        # Ensure column order matches training
        expected_cols = ['rooms', 'area_m2', 'floor', 'district', 'build_type', 
                       'renovation', 'bathroom', 'heating', 'condition', 'techpassport']
        df = df[expected_cols]
        return df
    except Exception as e:
        print(f"Error in prepare_features: {e}")
        import traceback
        traceback.print_exc()
        raise

async def generate_explanation(input_data: dict, predicted_price: float, user_price: float = None, status: str = None, diff_percent: float = None):
    """Generate explanation and recommendations using OpenAI"""
    print(f"🤖 generate_explanation called with: price={predicted_price}, user_price={user_price}, status={status}, diff_percent={diff_percent}")
    print(f"   Input data keys: {list(input_data.keys())}")
    
    if not openai_client:
        print("⚠️ OpenAI client not initialized - using fallback explanation")
        # Generate basic explanation based on features
        area = input_data.get('area_m2', 'N/A')
        renovation = input_data.get('renovation', 'N/A')
        district = input_data.get('district', 'N/A')
        
        fallback_explanation = f"Модель предсказала цену {predicted_price:,.0f} сомони на основе характеристик квартиры. "
        fallback_explanation += f"Площадь {area} м² является самым важным фактором (30.17%), "
        fallback_explanation += f"затем ремонт '{renovation}' (18.38%) и район '{district}' (12.67%)."
        
        fallback_recommendation = "Для повышения цены улучшите площадь, качество ремонта и убедитесь в наличии отопления."
        
        return {
            "explanation": fallback_explanation,
            "recommendation": fallback_recommendation
        }
    
    print(f"🤖 Generating explanation for price: {predicted_price}, user_price: {user_price}")
    
    try:
        # Prepare feature analysis
        feature_analysis = []
        for feature, importance in sorted(FEATURE_IMPORTANCE.items(), key=lambda x: x[1], reverse=True):
            value = input_data.get(feature, 'N/A')
            feature_analysis.append(f"- {feature}: {value} (важность: {importance:.1f}%)")
        
        feature_text = "\n".join(feature_analysis[:5])  # Top 5 features
        
        # Calculate price difference if user_price is provided
        price_context = ""
        recommendation_instruction = ""
        
        if user_price:
            diff = user_price - predicted_price
            diff_percent = (diff / predicted_price) * 100
            
            if diff_percent <= -5:
                price_context = f"Цена пользователя: {user_price:,.0f} сомони (на {abs(diff_percent):.1f}% НИЖЕ рыночной {predicted_price:,.0f} сомони)"
                recommendation_instruction = f"Скажи что это ОТЛИЧНО! Квартира продастся очень быстро, возможно даже в течение недели. Если не спешите, можно немного поднять цену до {int(predicted_price * 0.95):,} сомони и все равно продать быстро."
            elif diff_percent <= 0:
                price_context = f"Цена пользователя: {user_price:,.0f} сомони (на {abs(diff_percent):.1f}% ниже или равна рыночной {predicted_price:,.0f} сомони)"
                recommendation_instruction = f"Скажи что это ХОРОШАЯ цена для быстрой продажи. Квартира продастся в течение 2-4 недель. Можно оставить такую цену."
            else:
                price_context = f"Цена пользователя: {user_price:,.0f} сомони (на {diff_percent:.1f}% ВЫШЕ рыночной {predicted_price:,.0f} сомони)"
                recommendation_instruction = f"Скажи что для БЫСТРОЙ продажи (в течение месяца) лучше снизить цену до {int(predicted_price):,} сомони или даже до {int(predicted_price * 0.95):,} сомони. Иначе продажа может затянуться на 2-3 месяца или больше."
        else:
            price_context = "Цена пользователя не указана"
            recommendation_instruction = "Дай общую рекомендацию что можно улучшить для повышения цены или скорости продажи (улучшить ремонт, добавить отопление и т.д.)."
        
        # Build prompt
        prompt = f"""Ты - эксперт по недвижимости в Таджикистане. Проанализируй прогноз цены квартиры и дай объяснение.

Характеристики квартиры:
{feature_text}

Прогнозируемая рыночная цена: {predicted_price:,.0f} сомони
{price_context if price_context else 'Цена пользователя не указана'}

Важность признаков модели (feature importance):
- Площадь (area_m2): 30.17% - самый важный фактор
- Ремонт (renovation): 18.38%
- Отопление (heating): 13.21%
- Район (district): 12.67%
- Этаж (floor): 10.57%
- Количество комнат (rooms): 4.43%
- Состояние (condition): 3.89%
- Техпаспорт (techpassport): 3.41%
- Тип застройки (build_type): 1.64%
- Санузел (bathroom): 1.64%

ЗАДАНИЕ:
1. ОБЪЯСНЕНИЕ (2-3 предложения): Объясни почему модель дала именно такую цену ({predicted_price:,.0f} сомони), а не выше или ниже. Укажи какие конкретные характеристики квартиры повлияли на цену (учитывая важность признаков). Например: "Цена получилась такой потому что площадь X м² (самый важный фактор 30%), ремонт Y (18%), район Z (12%)..."

2. РЕКОМЕНДАЦИЯ (1-2 предложения), но по площади не давай рекомендации, если нет отопления то нужно рекоментовать чтобы установить или если нет ремонта то пусть отремонтируют: {recommendation_instruction}

Ответ на русском языке, формат:
ОБЪЯСНЕНИЕ: [объяснение]
РЕКОМЕНДАЦИЯ: [рекомендация]"""

        print(f"📤 Sending request to OpenAI...")
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по недвижимости в Таджикистане. Дай четкие и полезные объяснения."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        result_text = response.choices[0].message.content
        print(f"📥 Received response from OpenAI: {result_text[:200]}...")
        
        # Parse response - try multiple formats
        explanation = ""
        recommendation = ""
        
        # Try to find ОБЪЯСНЕНИЕ: and РЕКОМЕНДАЦИЯ: markers
        if "ОБЪЯСНЕНИЕ:" in result_text.upper() or "объяснение:" in result_text:
            # Case insensitive search
            text_upper = result_text.upper()
            expl_idx = text_upper.find("ОБЪЯСНЕНИЕ:")
            rec_idx = text_upper.find("РЕКОМЕНДАЦИЯ:")
            
            if expl_idx != -1:
                # Extract explanation
                expl_start = expl_idx + len("ОБЪЯСНЕНИЕ:")
                if rec_idx != -1:
                    explanation = result_text[expl_start:rec_idx].strip()
                else:
                    explanation = result_text[expl_start:].strip()
            
            if rec_idx != -1:
                # Extract recommendation
                rec_start = rec_idx + len("РЕКОМЕНДАЦИЯ:")
                recommendation = result_text[rec_start:].strip()
        else:
            # Fallback: try to split by paragraphs or lines
            paragraphs = result_text.split('\n\n')
            if len(paragraphs) >= 2:
                explanation = paragraphs[0].strip()
                recommendation = paragraphs[1].strip()
            else:
                # Last resort: use first 150 chars as explanation
                lines = result_text.split('\n')
                explanation = lines[0].strip() if lines else result_text[:200].strip()
                if len(lines) > 1:
                    recommendation = '\n'.join(lines[1:]).strip()[:200]
        
        # Ensure we have something
        if not explanation:
            explanation = result_text[:200].strip()
        if not recommendation:
            recommendation = "Улучшите площадь, ремонт и отопление для повышения цены."
        
        result = {
            "explanation": explanation,
            "recommendation": recommendation
        }
        print(f"✅ Generated explanation: {result['explanation'][:50]}...")
        print(f"   Full explanation: {result['explanation']}")
        print(f"   Full recommendation: {result['recommendation']}")
        return result
    except Exception as e:
        print(f"❌ Error generating explanation: {e}")
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        
        # Generate fallback explanation even on error
        area = input_data.get('area_m2', 'N/A')
        renovation = input_data.get('renovation', 'N/A')
        district = input_data.get('district', 'N/A')
        
        fallback_explanation = f"Модель предсказала цену {predicted_price:,.0f} сомони. "
        fallback_explanation += f"Основные факторы: площадь {area} м² (30.17%), ремонт '{renovation}' (18.38%), район '{district}' (12.67%)."
        
        fallback_recommendation = "Для повышения цены улучшите площадь, качество ремонта и убедитесь в наличии отопления."
        
        print(f"⚠️ Using fallback explanation due to error")
        return {
            "explanation": fallback_explanation,
            "recommendation": fallback_recommendation
        }


@app.post("/api/predict/sale")
async def predict_sale(request: PredictionRequest):
    """Predict if apartment will sell quickly at given price"""
    try:
        if model is None:
            raise HTTPException(status_code=500, detail="Model not loaded")
        
        features = prepare_features(request.dict())
        
        # Predict (CatBoost always returns DataFrame)
        try:
            raw_predicted_price = float(model.predict(features)[0])
            # Always multiply by 0.9
            predicted_price = raw_predicted_price * 0.9
        except Exception as pred_error:
            print(f"Prediction error: {pred_error}")
            print(f"Features type: {type(features)}")
            print(f"DataFrame columns: {features.columns.tolist()}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Prediction failed: {str(pred_error)}")
        
        user_price = request.price
        
        if user_price is None:
            # Generate explanation even without user price
            print(f"🔄 Starting explanation generation (no user price)...")
            explanation_text = ""
            recommendation_text = ""
            
            try:
                explanation_data = await generate_explanation(
                    request.dict(),
                    predicted_price,
                    None,
                    None
                )
                print(f"📋 Explanation data received: {explanation_data}")
                print(f"📋 Explanation data type: {type(explanation_data)}")
                
                # Ensure explanation_data is not None
                if explanation_data and isinstance(explanation_data, dict):
                    explanation_text = explanation_data.get("explanation", "")
                    recommendation_text = explanation_data.get("recommendation", "")
                else:
                    print("⚠️ WARNING: explanation_data is not a dict or is None!")
            except Exception as expl_error:
                print(f"❌ Error in generate_explanation: {expl_error}")
                import traceback
                traceback.print_exc()
            
            # Ensure we have non-empty strings - use fallback if needed
            if not explanation_text or not explanation_text.strip():
                print("⚠️ WARNING: explanation is empty, using fallback")
                area = request.dict().get('area_m2', 'N/A')
                renovation = request.dict().get('renovation', 'N/A')
                district = request.dict().get('district', 'N/A')
                explanation_text = f"Модель предсказала цену {predicted_price:,.0f} сомони на основе характеристик квартиры. Площадь {area} м² является самым важным фактором (30.17%), затем ремонт '{renovation}' (18.38%) и район '{district}' (12.67%)."
            
            if not recommendation_text or not recommendation_text.strip():
                print("⚠️ WARNING: recommendation is empty, using fallback")
                recommendation_text = "Введите цену для получения рекомендаций по продаже."
            
            response_data = {
                "predicted_price": float(predicted_price),
                "message": "Введите цену для анализа",
                "explanation": str(explanation_text) if explanation_text else "",
                "recommendation": str(recommendation_text) if recommendation_text else ""
            }
            
            print(f"📤 Sending response with explanation: {bool(response_data.get('explanation'))}")
            print(f"   Explanation: {response_data.get('explanation', '')[:100]}...")
            print(f"   Explanation length: {len(response_data.get('explanation', ''))}")
            print(f"   Recommendation: {response_data.get('recommendation', '')[:100]}...")
            print(f"   Recommendation length: {len(response_data.get('recommendation', ''))}")
            print(f"✅ Final response_data keys: {list(response_data.keys())}")
            print(f"✅ Full response_data: {response_data}")
            
            return response_data
        
        # Calculate difference
        diff = user_price - predicted_price
        diff_percent = (diff / predicted_price) * 100
        
        if diff_percent <= -5:  # Price is 5%+ lower than predicted
            message = "Отлично! Вашу квартиру точно быстро купят"
            status = "success"
        elif diff_percent <= 0:  # Price is lower or equal
            message = "Хорошая цена! Квартира продастся быстро"
            status = "good"
        else:  # Price is higher
            message = f"Лучше продать по цене {int(predicted_price):,} сомони, если хотите быстро продать"
            status = "warning"
        
        # Generate AI explanation and recommendation
        print(f"🔄 Starting explanation generation...")
        explanation_text = ""
        recommendation_text = ""
        
        try:
            explanation_data = await generate_explanation(
                request.dict(),
                predicted_price,
                user_price,
                status
            )
            print(f"📋 Explanation data received: {explanation_data}")
            print(f"📋 Explanation data type: {type(explanation_data)}")
            
            # Ensure explanation_data is not None
            if explanation_data and isinstance(explanation_data, dict):
                explanation_text = explanation_data.get("explanation", "")
                recommendation_text = explanation_data.get("recommendation", "")
            else:
                print("⚠️ WARNING: explanation_data is not a dict or is None!")
        except Exception as expl_error:
            print(f"❌ Error in generate_explanation: {expl_error}")
            import traceback
            traceback.print_exc()
        
        # Ensure we have non-empty strings - use fallback if needed
        if not explanation_text or not explanation_text.strip():
            print("⚠️ WARNING: explanation is empty, using fallback")
            area = request.dict().get('area_m2', 'N/A')
            renovation = request.dict().get('renovation', 'N/A')
            district = request.dict().get('district', 'N/A')
            explanation_text = f"Модель предсказала цену {predicted_price:,.0f} сомони на основе характеристик квартиры. Площадь {area} м² является самым важным фактором (30.17%), затем ремонт '{renovation}' (18.38%) и район '{district}' (12.67%)."
        
        if not recommendation_text or not recommendation_text.strip():
            print("⚠️ WARNING: recommendation is empty, using fallback")
            recommendation_text = "Для повышения цены улучшите площадь, качество ремонта и убедитесь в наличии отопления."
        
        # Build response with all fields explicitly
        response_data = {
            "predicted_price": float(predicted_price),
            "user_price": float(user_price) if user_price else None,
            "difference": float(diff),
            "difference_percent": round(diff_percent, 2),
            "message": str(message),
            "status": str(status),
            "explanation": str(explanation_text) if explanation_text else "",
            "recommendation": str(recommendation_text) if recommendation_text else ""
        }
        
        # Verify all fields are present
        required_fields = ["predicted_price", "user_price", "difference", "difference_percent", "message", "status", "explanation", "recommendation"]
        missing_fields = [field for field in required_fields if field not in response_data]
        if missing_fields:
            print(f"⚠️ WARNING: Missing fields in response: {missing_fields}")
        
        print(f"📤 Sending response with explanation: {bool(response_data.get('explanation'))}")
        print(f"   Explanation: {response_data.get('explanation', '')[:100]}...")
        print(f"   Explanation length: {len(response_data.get('explanation', ''))}")
        print(f"   Recommendation: {response_data.get('recommendation', '')[:100]}...")
        print(f"   Recommendation length: {len(response_data.get('recommendation', ''))}")
        print(f"✅ Final response_data keys: {list(response_data.keys())}")
        print(f"✅ Full response_data: {response_data}")
        
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in predict_sale: {e}")
        import traceback
        traceback.print_exc()
        # Even on error, try to return basic response with fallback explanation
        try:
            fallback_response = {
                "predicted_price": predicted_price if 'predicted_price' in locals() else 0,
                "user_price": user_price if 'user_price' in locals() else None,
                "difference": diff if 'diff' in locals() else 0,
                "difference_percent": round(diff_percent, 2) if 'diff_percent' in locals() else 0,
                "message": message if 'message' in locals() else "Ошибка при прогнозировании",
                "status": status if 'status' in locals() else "error",
                "explanation": f"Произошла ошибка при генерации объяснения: {str(e)[:100]}",
                "recommendation": "Попробуйте обновить страницу и повторить запрос."
            }
            print(f"⚠️ Returning fallback response due to error")
            return fallback_response
        except:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/districts")
def get_districts():
    """Get list of available districts"""
    return {"districts": DISTRICTS}

@app.get("/api/health")
def health():
    return {
        "status": "ok", 
        "model_loaded": model is not None,
        "model_type": type(model).__name__ if model is not None else None,
        "model_path": str(MODEL_PATH),
        "model_exists": MODEL_PATH.exists()
    }

@app.get("/api/graphs/list")
def get_graphs_list():
    """Get list of available graphs"""
    graphs_path = GRAPHS_PATH
    
    if not graphs_path.exists():
        print(f"⚠️ Graphs path does not exist: {graphs_path}")
        return {"graphs": {"категориальные": [], "числовые": [], "связи": [], "корреляции": []}}
    
    graphs = {
        "категориальные": [],
        "числовые": [],
        "связи": [],
        "корреляции": []
    }
    
    png_files = list(graphs_path.glob("*.png"))
    print(f"📊 Found {len(png_files)} PNG files in {graphs_path}")
    
    for file in png_files:
        filename = file.name
        print(f"  Processing: {filename}")
        
        if filename.startswith("категориальный_"):
            # Remove prefix and extension, clean up title
            title = filename.replace("категориальный_", "").replace("_распределение.png", "").replace(".png", "")
            # Convert to readable format
            if "_" in title:
                title = title.replace("_", " ").title()
            else:
                title = title.title()
            title = f"Распределение: {title}"
            graphs["категориальные"].append({
                "name": filename,
                "path": f"/api/graphs/{filename}",
                "title": title
            })
            print(f"    → Added to категориальные: {title}")
        elif filename.startswith("числовой_"):
            # Handle both _распределение.png and _boxplot.png
            base_name = filename.replace("числовой_", "").replace(".png", "")
            if "_распределение" in base_name:
                title = base_name.replace("_распределение", "").replace("_", " ").title()
                title = f"Распределение: {title}"
            elif "_boxplot" in base_name:
                title = base_name.replace("_boxplot", "").replace("_", " ").title()
                title = f"Boxplot: {title}"
            else:
                title = base_name.replace("_", " ").title()
            graphs["числовые"].append({
                "name": filename,
                "path": f"/api/graphs/{filename}",
                "title": title
            })
            print(f"    → Added to числовые: {title}")
        elif filename.startswith("связи_"):
            # Handle various связи_ patterns
            title = filename.replace("связи_", "").replace(".png", "")
            # Special handling for price_vs patterns
            if "price_vs_" in title:
                title = title.replace("price_vs_", "Цена vs ").replace("_", " ").title()
            elif "средняя_цена_по_" in title:
                title = title.replace("средняя_цена_по_", "Средняя цена по ").replace("_", " ").title()
            else:
                title = title.replace("_", " ").title()
            graphs["связи"].append({
                "name": filename,
                "path": f"/api/graphs/{filename}",
                "title": title
            })
            print(f"    → Added to связи: {title}")
        elif filename.startswith("корреляция_"):
            title = filename.replace("корреляция_", "").replace(".png", "")
            if "heatmap" in title:
                title = title.replace("_", " ").title()
                title = f"Heatmap: {title}"
            else:
                title = title.replace("_", " ").title()
            graphs["корреляции"].append({
                "name": filename,
                "path": f"/api/graphs/{filename}",
                "title": title
            })
            print(f"    → Added to корреляции: {title}")
        else:
            print(f"    ⚠️ Skipped (unknown prefix): {filename}")
    
    print(f"✅ Returning {sum(len(g) for g in graphs.values())} graphs")
    return {"graphs": graphs}

@app.get("/api/graphs/{filename}")
def get_graph(filename: str):
    """Serve graph image"""
    from urllib.parse import unquote
    # Decode URL-encoded filename
    filename = unquote(filename)
    graph_file = GRAPHS_PATH / filename
    print(f"🔍 Looking for graph: {graph_file}")
    print(f"   Exists: {graph_file.exists()}")
    if graph_file.exists():
        return FileResponse(graph_file, media_type="image/png")
    print(f"❌ Graph not found: {graph_file}")
    raise HTTPException(status_code=404, detail=f"Graph not found: {filename}")

@app.get("/api/statistics")
def get_statistics():
    """Get statistics from CSV file"""
    try:
        if df_cache is None:
            raise HTTPException(status_code=404, detail="CSV file not loaded")
        
        df = df_cache.copy()
        
        # Separate numerical and categorical columns
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        # Remove price from numerical for separate handling
        if 'price' in numerical_cols:
            numerical_cols.remove('price')
        
        stats = {
            "total_records": len(df),
            "numerical": {},
            "categorical": {},
            "price_stats": {}
        }
        
        # Price statistics (target variable)
        if 'price' in df.columns:
            price_data = df['price'].dropna()
            stats["price_stats"] = {
                "min": float(price_data.min()),
                "max": float(price_data.max()),
                "mean": float(price_data.mean()),
                "median": float(price_data.median()),
                "std": float(price_data.std()),
                "q25": float(price_data.quantile(0.25)),
                "q75": float(price_data.quantile(0.75)),
                "distribution": price_data.tolist()[:1000]  # Limit for performance
            }
        
        # Numerical columns statistics
        for col in numerical_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                stats["numerical"][col] = {
                    "min": float(col_data.min()),
                    "max": float(col_data.max()),
                    "mean": float(col_data.mean()),
                    "median": float(col_data.median()),
                    "std": float(col_data.std()),
                    "q25": float(col_data.quantile(0.25)),
                    "q75": float(col_data.quantile(0.75)),
                    "distribution": col_data.tolist()[:1000]  # Limit for performance
                }
        
        # Categorical columns statistics
        for col in categorical_cols:
            if col in df.columns:
                value_counts = df[col].value_counts().to_dict()
                # Convert to string keys for JSON serialization
                value_counts_str = {str(k): int(v) for k, v in value_counts.items()}
                stats["categorical"][col] = {
                    "value_counts": value_counts_str,
                    "unique_count": int(df[col].nunique()),
                    "null_count": int(df[col].isnull().sum())
                }
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve frontend static files
FRONTEND_DIR = BASE_DIR / "dashboard" / "frontend"
LOGO_DIR = BASE_DIR / "logo"
if FRONTEND_DIR.exists():
    # Mount static files (CSS, JS, images)
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
    # Mount logo directory
    if LOGO_DIR.exists():
        app.mount("/logo", StaticFiles(directory=str(LOGO_DIR)), name="logo")
    
    @app.get("/")
    async def read_root():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
    
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        # Skip API routes
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        
        file_path = FRONTEND_DIR / path
        if file_path.exists() and file_path.is_file() and file_path.suffix in ['.html', '.css', '.js', '.png', '.jpg', '.svg']:
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIR / "index.html"))

