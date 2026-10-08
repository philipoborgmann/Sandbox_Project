"""Asset catalogue use cases."""

from .domain import Asset
from .repositories import AssetRepository


def list_assets(repository: AssetRepository) -> tuple[Asset, ...]:
    return repository.list_assets()
