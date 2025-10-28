# src/domain/exceptions.py (Minimal definition)


class DomainError(Exception):
    """
    Base exception for all application business errors.
    All business rules violations (e.g., resource not found, invalid state)
    should inherit from this.
    """

    pass
