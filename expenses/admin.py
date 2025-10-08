"""I wire up the Ledgerly admin so it feels cohesive inside Django admin."""

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html

from .models import Category, Transaction, UserSettings
from .currencies import CURRENCY_CHOICES


class LedgerlyAdminSite(AdminSite):
    """I tidy the admin index so auth users sit under an Accounts app."""

    site_header = "Ledgerly Admin"
    site_title = "Ledgerly Admin"
    index_title = "Ledgerly administration"

    def get_app_list(self, request):
        """I group proxy account users into a custom Accounts section."""

        app_list = super().get_app_list(request)
        accounts_models = []
        filtered_apps = []

        for app in app_list:
            remaining_models = []
            for model in app["models"]:
                # I pull the proxy AccountUser out of the django.contrib app.
                if model["object_name"] == "AccountUser":
                    accounts_models.append(model)
                else:
                    remaining_models.append(model)

            if remaining_models:
                app["models"] = remaining_models
                filtered_apps.append(app)

        if accounts_models:
            # I mimic an "Accounts" app so admin users can find people fast.
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
    """I expose a proxy model to customise how Users appear in admin."""

    class Meta:
        proxy = True
        verbose_name = "User"
        verbose_name_plural = "Users"


class AccountUserAdmin(DjangoUserAdmin):
    """I reuse Django's built-in user admin tooling without changes."""


class CategoryAdmin(admin.ModelAdmin):
    """I display category details with active status and usage counts."""
    
    list_display = ('name', 'is_active', 'transaction_count', 'created_info')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('name',)
    
    def transaction_count(self, obj):
        """Show how many transactions use this category."""
        count = obj.transaction_set.count()
        return f"{count} transaction{'s' if count != 1 else ''}"
    
    def created_info(self, obj):
        """Show when category was created."""
        # Categories don't have created_at, so we'll show transaction info
        first_transaction = obj.transaction_set.order_by('created_at').first()
        if first_transaction:
            date_str = first_transaction.created_at.strftime('%Y-%m-%d')
            return f"First used: {date_str}"
        return "Never used"


class TransactionAdmin(admin.ModelAdmin):
    """I display comprehensive transaction details with filtering."""
    
    list_display = (
        'name', 'user', 'type', 'formatted_amount',
        'category', 'occurred_on', 'created_at'
    )
    list_filter = ('type', 'category', 'occurred_on', 'created_at', 'user')
    search_fields = ('name', 'note', 'user__username', 'user__email')
    date_hierarchy = 'occurred_on'
    ordering = ('-occurred_on', '-created_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('user', 'name', 'type', 'amount_in_cents', 'category')
        }),
        ('Dates', {
            'fields': ('occurred_on',)
        }),
        ('Additional Info', {
            'fields': ('note',),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def formatted_amount(self, obj):
        """Display amount in currency format."""
        # Simple formatting - you might want to use your currency helpers
        amount = obj.amount_in_cents / 100
        # Check user settings for currency
        has_settings = hasattr(obj.user, 'settings')
        is_gbp = has_settings and obj.user.settings.currency_code == 'GBP'
        symbol = "£" if is_gbp else "$"
        # Red for expenses, green for income
        color = "#dc3545" if obj.type == 'OUTGO' else "#28a745"
        amount_str = f"{symbol}{amount:.2f}"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, amount_str
        )


class UserSettingsAdmin(admin.ModelAdmin):
    """I display user settings including cycle dates and currency."""
    
    list_display = (
        'user', 'currency_code', 'cycle_start_date',
        'user_email', 'user_date_joined', 'total_transactions'
    )
    list_filter = ('currency_code', 'cycle_start_date')
    search_fields = (
        'user__username', 'user__email',
        'user__first_name', 'user__last_name'
    )
    ordering = ('user__username',)
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Preferences', {
            'fields': ('currency_code', 'cycle_start_date')
        }),
    )
    
    def user_email(self, obj):
        """Show user's email address."""
        return obj.user.email or "No email set"
    
    def currency_display(self, obj):
        """Show currency with full name."""
        currency_dict = dict(CURRENCY_CHOICES)
        return currency_dict.get(obj.currency_code, obj.currency_code)
    
    def user_date_joined(self, obj):
        """Show when user joined."""
        return obj.user.date_joined.strftime('%Y-%m-%d %H:%M')
    
    def total_transactions(self, obj):
        """Show total number of transactions for this user."""
        count = obj.user.transactions.count()
        return f"{count} transaction{'s' if count != 1 else ''}"


ledgerly_admin_site.register(AccountUser, AccountUserAdmin)
ledgerly_admin_site.register(Category, CategoryAdmin)
ledgerly_admin_site.register(Transaction, TransactionAdmin)
ledgerly_admin_site.register(UserSettings, UserSettingsAdmin)
