from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDING = "REFUNDING"
    REFUNDED = "REFUNDED"
