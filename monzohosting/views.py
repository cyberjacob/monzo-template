#!/usr/bin/env python
# coding=utf-8
import os

import pymonzo
from django.conf import settings
from django.views.generic import FormView, TemplateView, RedirectView

from monzohosting import models, forms


# Create your views here.
class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        try:
            monzo = models.Setting.get_monzo()
        except models.Setting.DoesNotExist:
            return {'error': True, 'message': "No Monzo configuration available."}
        return {'error': False, 'message': monzo.whoami()}


class WebhookView(TemplateView):
    template_name = "webhook_setup.html"

    def get_context_data(self, **kwargs):
        c = {'webhooks': {}}
        for item in os.listdir(settings.APPS_DIR):
            if item[0] != "_" and os.path.isdir(os.path.join(settings.APPS_DIR, item)):
                try:
                    c["webhooks"][item] = models.webhookReceivers.objects.get(
                        moduleName=item,
                        webhookType="transaction.created"
                    )
                except models.webhookReceivers.DoesNotExist:
                    c["webhooks"][item] = False
        return c


class SetupView(FormView):
    template_name = "setup.html"
    form_class = forms.SetupForm

    def form_valid(self, form):
        models.Setting.set_value("client_id", form.cleaned_data["client_id"])
        models.Setting.set_value("client_secret", form.cleaned_data["client_secret"])
        models.Setting.set_value("instance_domain", form.cleaned_data["instance_domain"])
        SetupView.success_url = "https://auth.monzo.com/?response_type=code&redirect_uri=" + \
                                models.Setting.get_redirect_uri() + "&client_id=" + form.cleaned_data["client_id"]
        return super().form_valid(form)


class AuthView(RedirectView):
    pattern_name = 'index'
    def get(self, request, *args, **kwargs):
        pymonzo.MonzoAPI(
            client_id=models.Setting.get_value("client_id"),
            client_secret=models.Setting.get_value("client_secret"),
            auth_code=request.GET["code"],
            redirect_url="https://" + models.Setting.get_value("instance_domain") + "/auth",
            token_save_function=models.Setting.save_token_data
        ).whoami()

        return super().get(request, *args, **kwargs)


def webhook(request):
    return "OK"
