from enum import Enum

class PrivacyLevel(str, Enum):
    public = "PUBLIC"
    followers = "FOLLOWERS"
    private = "PRIVATE"

class Gender(str, Enum):
    male = "MALE"
    female = "FEMALE"
    unknown = "UNKNOWN"