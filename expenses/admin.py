from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from .models import Category, Transaction


class LedgerlyAdminSite(AdminSite):
    site_header = "Ledgerly Admin"
    site_title = "Ledgerly Admin"
    index_title = "Ledgerly administration"

    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        accounts_models = []
        filtered_apps = []

        for app in app_list:
            remaining_models = []
            for model in app["models"]:
                if model["object_name"] == "AccountUser":
                    accounts_models.append(model)
                else:
                    remaining_models.append(model)

            if remaining_models:
                app["models"] = remaining_models
                filtered_apps.append(app)

        if accounts_models:
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
    class Meta:
        proxy = True
        verbose_name = "User"
        verbose_name_plural = "Users"


class AccountUserAdmin(DjangoUserAdmin):
    pass


class CategoryAdmin(admin.ModelAdmin):
    pass


class TransactionAdmin(admin.ModelAdmin):
    pass


ledgerly_admin_site.register(AccountUser, AccountUserAdmin)
ledgerly_admin_site.register(Category, CategoryAdmin)
ledgerly_admin_site.register(Transaction, TransactionAdmin)
