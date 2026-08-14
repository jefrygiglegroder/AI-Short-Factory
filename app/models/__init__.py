"""Models package initializer.

Import model modules to ensure they are registered with SQLAlchemy's Base.metadata
when the package is imported. This helps init_db() reliably see all models.
"""

# Import model modules so their classes register with Base.metadata
from . import account  # noqa: F401
from . import idea  # noqa: F401

__all__ = ["account", "idea"]
