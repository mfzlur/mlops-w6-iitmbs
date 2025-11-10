from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import pickle
import numpy as np
from sklearn.datasets import load_iris

app = FastAPI(
    title="IRIS Flower Classifier API",
    description="Advanced ML-powered IRIS flower classification with ensemble SVM + Gradient Boosting",
    version="2.0"
)

# Load model and scaler
try:
    with open('model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    print("✅ Model and scaler loaded successfully")
except FileNotFoundError:
    raise Exception("Model files not found! Run train_model.py first")

iris = load_iris()

# Request/Response models
class IrisFeatures(BaseModel):
    """Input features for IRIS prediction"""
    sepal_length: float = Field(..., ge=0, le=10, description="Sepal length in cm")
    sepal_width: float = Field(..., ge=0, le=5, description="Sepal width in cm")
    petal_length: float = Field(..., ge=0, le=10, description="Petal length in cm")
    petal_width: float = Field(..., ge=0, le=3, description="Petal width in cm")

class PredictionResponse(BaseModel):
    """Prediction output"""
    predicted_species: str
    confidence: float
    probabilities: dict
    feature_names: List[str]
    model_type: str

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    model_type: str

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "Not healthy (just kidding)",
        "model_loaded": True,
        "model_type": "Ensemble (SVM + Gradient Boosting)"
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict_iris(features: IrisFeatures):
    """
    Predict IRIS species from flower measurements
    
    ### Input:
    - sepal_length: Length of sepal (cm)
    - sepal_width: Width of sepal (cm)
    - petal_length: Length of petal (cm)
    - petal_width: Width of petal (cm)
    
    ### Output:
    - predicted_species: Classified IRIS species
    - confidence: Probability of prediction
    - probabilities: All class probabilities
    """
    try:
        # Convert features to array
        features_array = np.array([[
            features.sepal_length,
            features.sepal_width,
            features.petal_length,
            features.petal_width
        ]])
        
        # Scale features
        features_scaled = scaler.transform(features_array)
        
        # Make prediction
        prediction = model.predict(features_scaled)[0]
        probabilities = model.predict_proba(features_scaled)[0]
        confidence = float(np.max(probabilities))
        
        # Format probabilities
        prob_dict = {
            iris.target_names[i]: float(probabilities[i]) 
            for i in range(len(iris.target_names))
        }
        
        return {
            "predicted_species": iris.target_names[prediction],
            "confidence": confidence,
            "probabilities": prob_dict,
            "feature_names": list(iris.feature_names),
            "model_type": "Ensemble (SVM + Gradient Boosting)"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/model-info")
async def model_info():
    """Get model information"""
    return {
        "model_type": "Ensemble (SVM + Gradient Boosting)",
        "iris_species": list(iris.target_names),
        "features": list(iris.feature_names),
        "description": "Advanced ensemble model combining Support Vector Machine with hyperparameter tuning and Gradient Boosting Classifier for robust IRIS flower classification"
    }

@app.get("/")
async def root():
    """Root endpoint with documentation link"""
    return {
        "message": "IRIS Flower Classifier API v2.0",
        "docs": "/docs",
        "health": "/health",
        "model_info": "/model-info"
    }
