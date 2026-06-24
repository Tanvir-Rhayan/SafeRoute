import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb
import joblib
import os

def train_safety_model():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "dataset.csv")
    df = pd.read_csv(data_path)

    features = ["hour", "crime_rate", "lighting_score", "crowd_score",
                "hospital_nearby", "police_nearby", "open_shops"]
    target = "safety_score"

    X = df[features]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    xgb_model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        verbosity=0
    )
    xgb_model.fit(X_train, y_train)

    rf_model = RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        random_state=42
    )
    rf_model.fit(X_train, y_train)

    xgb_pred = xgb_model.predict(X_test)
    rf_pred = rf_model.predict(X_test)

    xgb_r2 = r2_score(y_test, xgb_pred)
    rf_r2 = r2_score(y_test, rf_pred)

    xgb_rmse = np.sqrt(mean_squared_error(y_test, xgb_pred))
    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))

    print(f"XGBoost - R2: {xgb_r2:.4f}, RMSE: {xgb_rmse:.4f}")
    print(f"Random Forest - R2: {rf_r2:.4f}, RMSE: {rf_rmse:.4f}")

    best_model = xgb_model if xgb_r2 >= rf_r2 else rf_model
    best_name = "XGBoost" if xgb_r2 >= rf_r2 else "Random Forest"
    print(f"Best model: {best_name}")

    model_path = os.path.join(base_dir, "model", "safety_model.pkl")
    joblib.dump(best_model, model_path)
    print(f"Model saved to {model_path}")

    import json
    metrics = {
        "model_name": best_name,
        "r2_score": round(xgb_r2 if xgb_r2 >= rf_r2 else rf_r2, 4),
        "rmse": round(xgb_rmse if xgb_r2 >= rf_r2 else rf_rmse, 4),
        "features": features,
        "feature_importance": dict(zip(features, best_model.feature_importances_.tolist()))
    }

    metrics_path = os.path.join(base_dir, "model", "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved to {metrics_path}")

    return best_model, metrics

if __name__ == "__main__":
    train_safety_model()