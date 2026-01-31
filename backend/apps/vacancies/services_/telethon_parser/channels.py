
TELEGRAM_JOB_CHANNELS = {
    'python': [
        'p_rabota',
        'back_rabota'

    ],

    # DevOps
    'devops': [
        'devops_rabota'
    ],

    # Frontend
    'frontend': [
        'js_rabota'
    ],
}


def get_all_channels() -> list:
    all_channels = []
    for category_channels in TELEGRAM_JOB_CHANNELS.values():
        all_channels.extend(category_channels)
    return list(set(all_channels))  # Убираем дубликаты


def get_channels_by_category(category: str) -> list:
    return TELEGRAM_JOB_CHANNELS.get(category, [])