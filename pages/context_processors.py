from django.conf import settings


def additional_settings_options(request):
    return {'metric_system_code': settings.METRIC_SYSTEM_CODE}
