from hashlib import blake2b

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


def get_hash(token: str):
    return blake2b(
        token.encode('utf-8'),
        digest_size=64,
        salt=settings.API_TOKEN_SALT.encode('utf-8'),
    ).hexdigest()


class ExternGoogleUser(models.Model):
    user = models.OneToOneField(User, null=False, on_delete=models.CASCADE, primary_key=True)
    extern_id = models.CharField(null=False, unique=True, max_length=128)
    is_username_changed = models.BooleanField(null=False, default=False)


class Token(models.Model):
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    app_name = models.CharField(verbose_name='Наименование приложения', max_length=20, null=False, blank=False)
    token = models.CharField(verbose_name='Токен для доступа к API сервера', max_length=128, null=False, blank=False, unique=True)
    expire_dt = models.DateTimeField(verbose_name='Время жизни токена', null=True)

    class Meta:
        db_table = 'app_custom_auth_token'
        verbose_name = 'Токен'
        verbose_name_plural = 'Токены'
