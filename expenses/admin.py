"""Custom admin site wiring so Ledgerly feels cohesive in Django admin."""

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from .models import Category, Transaction


class LedgerlyAdminSite(AdminSite):
    """Housekeep the admin index so auth users appear under an Accounts app."""

    site_header = "Ledgerly Admin"
    site_title = "Ledgerly Admin"
    index_title = "Ledgerly administration"

    def get_app_list(self, request):
        """Group proxy account users into a custom Accounts section."""

        app_list = super().get_app_list(request)
        accounts_models = []
        filtered_apps = []

        for app in app_list:
            remaining_models = []
            for model in app["models"]:
                # Pull the proxy AccountUser out of the django.contrib app.
                if model["object_name"] == "AccountUser":
                    accounts_models.append(model)
                else:
                    remaining_models.append(model)

            if remaining_models:
                app["models"] = remaining_models
                filtered_apps.append(app)

        if accounts_models:
            # Mimic a dedicated "Accounts" app so admin users can
            # find people fast.
            accounts_app = {
                "name": "Accounts",
                "app_label": "accounts",
                "app_url": accounts_models[0]["admin_url"],
                "has_module_perms": True,
                "models": accounts_models,
            }
            filtered_apps.insert(0, accounts_app)

        return filtered_apps


ledgerly_admin_site = LedgerlyAdminSite(name="ledgerly_admin")


class AccountUser(User):
    """Proxy model that lets us customise how Users appear in admin."""

    class Meta:
        proxy = True
        verbose_name = "User"
        verbose_name_plural = "Users"


class AccountUserAdmin(DjangoUserAdmin):
    """Leverage Django's built-in user admin tooling without alteration."""


class CategoryAdmin(admin.ModelAdmin):
    """Keep the option open for future list-display tweaks."""


class TransactionAdmin(admin.ModelAdmin):
    """Placeholder admin so transaction metadata can be refined later."""


ledgerly_admin_site.register(AccountUser, AccountUserAdmin)
ledgerly_admin_site.register(Category, CategoryAdmin)
ledgerly_admin_site.register(Transaction, TransactionAdmin)
