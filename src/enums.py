from enum import StrEnum, auto


# fmt: off
class BasicRole(StrEnum):
    """Роль для главного экрана фронта"""

    tutor    = auto()
    student  = auto()


class AccountStatus(StrEnum):
    """Статус аккаунта человека в жизненном цикле гибридного ученика"""

    managed  = auto()
    """карточка без аккаунта, заведена репетитором"""
    invited  = auto()
    """приглашение отправлено"""
    active   = auto()
    """есть полноценный аккаунт"""
    blocked  = auto()
    """заблокирован"""
    deleted  = auto()
    """soft-delete"""
# fmt: on
