import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report,
)

from src.config import (
    REFERENCE_DATA_PATH,
    MODEL_PATH,
    METADATA_PATH,
    EVALUATION_METRICS_PATH,
    REPORTS_DIR,
    RANDOM_SEED,
)
from src.data_pipeline import prepare_data, build_preprocessor, get_feature_lists


def train_and_evaluate():
    print("=" * 60)
    print("TASK 1 & 2: LOADING DATASET & TRAINING FRAUD DETECTION MODELS")
    print("=" * 60)

    # 1. Prepare Data
    X, y, df_prepared = prepare_data(REFERENCE_DATA_PATH)
    print(f"Dataset shape: {X.shape}")
    print(f"Target distribution:\n{y.value_counts()}")
    fraud_rate = (y == 1).mean() * 100
    print(f"Fraud Rate: {fraud_rate:.2f}%")

    num_features, cat_features = get_feature_lists()
    all_features = num_features + cat_features

    # 2. Stratified Train-Test Split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_SEED, stratify=y
    )
    print(f"Training samples: {len(X_train)} (Fraud: {y_train.sum()})")
    print(f"Testing samples:  {len(X_test)} (Fraud: {y_test.sum()})")

    # Ratio for class weighting
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos = neg_count / max(pos_count, 1)

    # 3. Model Candidates
    preprocessor = build_preprocessor()

    models = {
        "LogisticRegression": Pipeline(
            steps=[
                ("preprocessor", build_preprocessor()),
                (
                    "classifier",
                    LogisticRegression(
                        class_weight="balanced",
                        max_iter=1000,
                        random_state=RANDOM_SEED,
                    ),
                ),
            ]
        ),
        "RandomForest": Pipeline(
            steps=[
                ("preprocessor", build_preprocessor()),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=150,
                        max_depth=8,
                        class_weight="balanced",
                        random_state=RANDOM_SEED,
                    ),
                ),
            ]
        ),
        "XGBoost": Pipeline(
            steps=[
                ("preprocessor", build_preprocessor()),
                (
                    "classifier",
                    XGBClassifier(
                        n_estimators=100,
                        max_depth=5,
                        learning_rate=0.05,
                        scale_pos_weight=scale_pos,
                        random_state=RANDOM_SEED,
                        eval_metric="logloss",
                    ),
                ),
            ]
        ),
    }

    # 4. Cross-Validation and Test Evaluation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    results = {}
    best_model_name = None
    best_roc_auc = -1.0

    print("\n--- Model Benchmark & Cross-Validation ---")
    for name, pipe in models.items():
        # 5-fold CV ROC-AUC
        cv_scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="roc_auc")
        mean_cv_auc = float(np.mean(cv_scores))
        std_cv_auc = float(np.std(cv_scores))

        # Fit on entire training set
        pipe.fit(X_train, y_train)

        # Predict probabilities and classes on test set
        y_pred = pipe.predict(X_test)
        y_prob = pipe.predict_proba(X_test)[:, 1]

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        macro_f1 = float(f1_score(y_test, y_pred, average="macro"))
        roc_auc = float(roc_auc_score(y_test, y_prob))
        pr_auc = float(average_precision_score(y_test, y_prob))
        cm = confusion_matrix(y_test, y_pred).tolist()

        results[name] = {
            "cv_roc_auc_mean": mean_cv_auc,
            "cv_roc_auc_std": std_cv_auc,
            "test_accuracy": acc,
            "test_precision": prec,
            "test_recall": rec,
            "test_f1": f1,
            "test_macro_f1": macro_f1,
            "test_roc_auc": roc_auc,
            "test_pr_auc": pr_auc,
            "confusion_matrix": cm,
        }

        print(
            f"[{name}] CV ROC-AUC: {mean_cv_auc:.4f} (+/- {std_cv_auc:.4f}) | "
            f"Test ROC-AUC: {roc_auc:.4f} | PR-AUC: {pr_auc:.4f} | F1: {f1:.4f} | Recall: {rec:.4f}"
        )

        if roc_auc > best_roc_auc:
            best_roc_auc = roc_auc
            best_model_name = name

    print(f"\n>>> Selected Best Model: {best_model_name} (ROC-AUC: {best_roc_auc:.4f}) <<<")
    best_pipeline = models[best_model_name]

    # 5. Save Artifacts
    joblib.dump(best_pipeline, MODEL_PATH)
    print(f"Saved trained model pipeline to {MODEL_PATH}")

    # Generate Confusion Matrix Plot
    plt.figure(figsize=(6, 5))
    cm_arr = np.array(results[best_model_name]["confusion_matrix"])
    sns.heatmap(
        cm_arr,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["Legitimate", "Fraudulent"],
        yticklabels=["Legitimate", "Fraudulent"],
    )
    plt.title(f"Confusion Matrix: {best_model_name}")
    plt.xlabel("Predicted Label")
    plt.ylabel("Actual Label")
    plt.tight_layout()
    cm_plot_path = REPORTS_DIR / "confusion_matrix.png"
    plt.savefig(cm_plot_path, dpi=200)
    plt.close()
    print(f"Saved confusion matrix plot to {cm_plot_path}")

    # Metadata
    metadata = {
        "model_name": best_model_name,
        "features": {
            "numerical": num_features,
            "categorical": cat_features,
            "all": all_features,
        },
        "metrics": results[best_model_name],
        "all_model_results": results,
        "target_mapping": {"0": "Legitimate", "1": "Fraudulent"},
        "threshold": 0.5,
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata to {METADATA_PATH}")

    with open(EVALUATION_METRICS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved evaluation metrics to {EVALUATION_METRICS_PATH}")

    return best_model_name, results


if __name__ == "__main__":
    train_and_evaluate()
