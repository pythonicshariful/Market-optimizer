# File: utils.py


from sklearn.metrics import mean_absolute_error


def explain_model(model, data):
    """Return SHAP values if available, otherwise a placeholder explanation.

    This function performs lazy import of `shap` to avoid importing heavy
    dependencies at module import time (which can block server startup).
    """
    try:
        import shap
    except Exception:
        return {"explanation": "SHAP not available in this environment."}
    try:
        explainer = shap.Explainer(model, data)
        shap_values = explainer(data)
        return shap_values
    except Exception:
        return {"explanation": "SHAP failed to run on the provided model/data."}


def check_bias(y_true, y_pred, sensitive_features):
    """Compute group-wise MAE using fairlearn when available; otherwise overall MAE.

    Lazy-imports `fairlearn.metrics.MetricFrame` to avoid heavy imports on module
    load.
    """
    try:
        from fairlearn.metrics import MetricFrame
    except Exception:
        MetricFrame = None

    if MetricFrame is not None:
        try:
            mf = MetricFrame(metrics={'mae': mean_absolute_error}, y_true=y_true, y_pred=y_pred, sensitive_features=sensitive_features)
            return mf.by_group
        except Exception:
            pass
    # Fallback: compute overall MAE only
    return {"overall_mae": mean_absolute_error(y_true, y_pred)}