import os
from decimal import Decimal

import pandas as pd
from catboost import CatBoostRegressor, Pool
from django.conf import settings

from .models import HistoricalTaskData


def ensure_model_dir():
    os.makedirs(settings.ML_MODELS_DIR, exist_ok=True)


def get_training_dataframe():
    items = HistoricalTaskData.objects.exclude(
        actual_time_spent__isnull=True
    ).values(
        'task_title',
        'task_type',
        'assignee_name',
        'actual_time_spent'
    )

    data = list(items)

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    df['task_title'] = df['task_title'].fillna('')
    df['task_type'] = df['task_type'].fillna('')
    df['assignee_name'] = df['assignee_name'].fillna('')
    df['actual_time_spent'] = pd.to_numeric(df['actual_time_spent'], errors='coerce')

    df = df.dropna(subset=['actual_time_spent'])

    return df


def train_model():
    ensure_model_dir()

    df = get_training_dataframe()

    if len(df) < settings.MIN_TASKS_FOR_TRAINING:
        return False

    X = df[['task_title', 'assignee_name', 'task_type']]
    y = df['actual_time_spent']

    train_pool = Pool(
        data=X,
        label=y,
        cat_features=['assignee_name', 'task_type'],
        text_features=['task_title']
    )

    model = CatBoostRegressor(
        iterations=500,
        depth=6,
        learning_rate=0.1,
        loss_function='RMSE',
        verbose=False
    )

    model.fit(train_pool)
    model.save_model(str(settings.CATBOOST_MODEL_PATH))

    return True


def model_exists():
    return os.path.exists(settings.CATBOOST_MODEL_PATH)


def load_model():
    if not model_exists():
        return None

    model = CatBoostRegressor()
    model.load_model(str(settings.CATBOOST_MODEL_PATH))
    return model


def can_predict():
    df = get_training_dataframe()

    if len(df) < settings.MIN_TASKS_FOR_TRAINING:
        return False

    if not model_exists():
        return False

    return True


def predict_task_time(task):
    if not can_predict():
        return {
            'prediction_time': None,
            'prediction_text': 'Недостаточно данных для прогнозирования'
        }

    model = load_model()

    assignee_name = ''
    if task.assignee:
        assignee_name = task.assignee.full_name

    X = pd.DataFrame([{
        'task_title': task.title,
        'assignee_name': assignee_name,
        'task_type': task.task_type,
    }])

    pool = Pool(
        data=X,
        cat_features=['assignee_name', 'task_type'],
        text_features=['task_title']
    )

    prediction = model.predict(pool)[0]

    if prediction < 0:
        prediction = 0

    prediction_value = Decimal(str(round(float(prediction), 2)))

    return {
        'prediction_time': prediction_value,
        'prediction_text': None
    }


def create_or_update_prediction(task):
    from tasks.models import Prediction

    prediction_result = predict_task_time(task)

    Prediction.objects.create(
        task=task,
        prediction_time=prediction_result['prediction_time'],
        prediction_text=prediction_result['prediction_text'],
    )

    if prediction_result['prediction_time'] is not None:
        task.time_estimate = prediction_result['prediction_time']
    else:
        task.time_estimate = None

    task.save(update_fields=['time_estimate'])

    return prediction_result


def save_historical_data(task):
    HistoricalTaskData.objects.update_or_create(
        task=task,
        defaults={
            'task_title': task.title,
            'task_type': task.task_type,
            'assignee_name': task.assignee.full_name if task.assignee else '',
            'actual_time_spent': task.actual_time_spent,
        }
    )


def retrain_model_if_possible():
    df = get_training_dataframe()

    if len(df) < settings.MIN_TASKS_FOR_TRAINING:
        return False

    return train_model()