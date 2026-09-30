class DomainError(ValueError):
    """Stable error category without customer values or external error details."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)
