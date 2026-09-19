from django.conf import settings


def org(request):
    return {"ORG_NAME": settings.ORG_NAME}
