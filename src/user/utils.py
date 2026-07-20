def anonymized_profile_values() -> dict[str, None | str]:
    """Набор значений для затирания ПД при soft delete профиля"""
    return {
        "first_name": None,
        "last_name": None,
        "middle_name": None,
        "nickname": "deleted user",
        "avatar_url": None,
        "date_of_birth": None,
        "contacts": None,
        "messengers": None,
        "bio": None,
    }
