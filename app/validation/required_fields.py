from app.domain.address import Address


def missing_required_fields(address: Address) -> tuple[str, ...]:
    """Completeness only; house_flat may contain an explicit premise description."""
    return tuple(field for field in ('house_flat', 'area', 'city', 'pincode')
                 if getattr(address, field) is None)
