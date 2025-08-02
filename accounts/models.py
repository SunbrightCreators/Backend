from string import ascii_lowercase, digits
from django.contrib.auth.models import AbstractUser
from django.db import models
from django_nanoid.models import NANOIDField
from .managers import CustomUserManager

class CustomUser(AbstractUser):
    # AbstractUser 모델 오버라이딩
    username = NANOIDField(
        editable=False,
        secure_generated=True,
        alphabetically=ascii_lowercase+digits,
        size=21,
    )
    first_name = None
    last_name = None
    email = models.EmailField(
        unique=True,
        error_messages={'unique': '이미 존재하는 이메일입니다.',},
    )
    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # 커스텀 필드

    def __str__(self):
        return self.email
