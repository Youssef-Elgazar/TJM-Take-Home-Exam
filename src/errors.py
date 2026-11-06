"""Shared exceptions."""


class ManualReviewRequired(RuntimeError):
    """Raised when the run must stop and a human must decide."""

    def __init__(self, reasons):
        if isinstance(reasons, str):
            reasons = [reasons]
        self.reasons = list(reasons)
        super().__init__("; ".join(self.reasons))
