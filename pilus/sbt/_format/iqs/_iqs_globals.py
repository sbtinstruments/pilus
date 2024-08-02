from enum import Enum, unique


@unique
class IqsVersion(Enum):
    """Version of the IQS specification."""

    V1_0_0 = "v1.0.0"
    V2_0_0 = "v2.0.0"
