import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models import AccessEvent, CorePage, Site, VisitorEnrichmentCache, VisitorIdentityRule  # noqa: F401
from models.base import Base
from models.session import engine


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized.")


if __name__ == "__main__":
    main()
