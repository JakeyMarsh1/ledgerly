"""I wire up the Ledgerly admin so it feels cohesive inside Django admin."""

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django import forms

from .models import Category, Transaction, UserSettings
from .currencies import CURRENCY_CHOICES


class LedgerlyAdminSite(AdminSite):
    """I organize the admin around user-centric data containers."""

    site_header = "Ledgerly Admin - User Data Management"
    site_title = "Ledgerly Admin"
    index_title = "User Financial Data Administration"

    def get_app_list(self, request):
        """I group models into logical user-centric containers."""

        app_list = super().get_app_list(request)

        # Create custom app groupings for user data containers
        user_management_models = []
        financial_data_models = []
        system_models = []

        for app in app_list:
            for model in app["models"]:
                model_name = model["object_name"]

                # User Management Container
                if model_name in ["AccountUser"]:
                    user_management_models.append(model)

                # Financial Data Container (Categories only)
                # Transactions are managed via User inlines
                elif model_name in ["Category"]:
                    financial_data_models.append(model)

                # System/Other models
                else:
                    system_models.append(model)

        # Build the organized app list
        organized_apps = []

        if user_management_models:
            organized_apps.append({
                "name": "👥 Users",
                "app_label": "users",
                "app_url": user_management_models[0]["admin_url"],
                "has_module_perms": True,
                "models": user_management_models,
            })

        if financial_data_models:
            organized_apps.append({
                "name": "� Categories",
                "app_label": "categories",
                "app_url": financial_data_models[0]["admin_url"],
                "has_module_perms": True,
                "models": financial_data_models,
            })

        # Add any remaining system models
        for app in app_list:
            remaining_models = []
            for model in app["models"]:
                if model["object_name"] not in [
                    "AccountUser", "UserSettings", "Transaction", "Category"
                ]:
                    remaining_models.append(model)

            if remaining_models:
                app["models"] = remaining_models
                organized_apps.append(app)

        return organized_apps


ledgerly_admin_site = LedgerlyAdminSite(name="ledgerly_admin")


class AccountUser(User):
    """I expose a proxy model to customise how Users appear in admin."""

    class Meta:
        proxy = True
        verbose_name = "User"
        verbose_name_plural = "Users"


class UserSettingsInlineForm(forms.ModelForm):
    """Custom form for editing user settings inline."""

    class Meta:
        model = UserSettings
        fields = ['currency_code', 'cycle_start_date']
        widgets = {
            'cycle_start_date': forms.DateInput(attrs={'type': 'date'}),
        }


class UserSettingsInline(admin.StackedInline):
    """Inline admin for user settings."""

    model = UserSettings
    form = UserSettingsInlineForm
    can_delete = False
    verbose_name_plural = 'Financial Settings'
    extra = 0

    fieldsets = (
        (None, {
            'fields': ('currency_code', 'cycle_start_date'),
        }),
    )


class TransactionInlineForm(forms.ModelForm):
    """Custom form for editing transactions inline with formatted amounts."""

    formatted_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Amount"
    )

    class Meta:
        model = Transaction
        fields = [
            'name', 'type', 'formatted_amount', 'category', 'occurred_on'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert cents to decimal for display
        if self.instance and self.instance.amount_in_cents is not None:
            amount_decimal = self.instance.amount_in_cents / 100
            self.fields['formatted_amount'].initial = amount_decimal

    def save(self, commit=True):
        # Convert decimal back to cents before saving
        if 'formatted_amount' in self.cleaned_data:
            amount_decimal = self.cleaned_data['formatted_amount']
            self.instance.amount_in_cents = int(amount_decimal * 100)
        return super().save(commit)


class TransactionInline(admin.TabularInline):
    """Inline admin for viewing/editing user transactions."""

    model = Transaction
    form = TransactionInlineForm
    extra = 0
    max_num = 20  # Limit to most recent 20 for performance
    fields = (
        'name', 'type', 'formatted_amount', 'formatted_amount_display',
        'category', 'occurred_on'
    )
    readonly_fields = ('formatted_amount_display',)
    ordering = ('-occurred_on', '-created_at')

    @admin.display(description='Formatted Amount')
    def formatted_amount_display(self, obj):
        """Show formatted amount in inline."""
        if not obj or obj.amount_in_cents is None:
            return "No amount"

        try:
            amount = obj.amount_in_cents / 100
            currency_code = 'USD'  # Default currency

            # Try to get user currency preference
            if obj.user:
                try:
                    # Get or create user settings
                    from .models import UserSettings
                    settings, created = UserSettings.objects.get_or_create(
                        user=obj.user
                    )
                    currency_code = settings.currency_code or 'USD'
                except Exception:
                    currency_code = 'USD'

            symbol = "£" if currency_code == 'GBP' else "$"
            color = "#dc3545" if obj.type == 'OUTGO' else "#28a745"
            formatted_amount = f"{symbol}{amount:.2f}"
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color, formatted_amount
            )
        except Exception as e:
            return f"Error: {str(e)[:20]}"


class AccountUserAdmin(DjangoUserAdmin):
    """I provide a complete user data container with all financial info."""

    inlines = (UserSettingsInline, TransactionInline)

    # Enhanced list view showing key user metrics
    list_display = (
        'username', 'email', 'is_active', 'date_joined',
        'cycle_start_date', 'currency_display', 'transaction_count'
    )

    list_filter = (
        'is_active', 'date_joined',
        'settings__currency_code', 'settings__cycle_start_date'
    )

    search_fields = ('username', 'email', 'first_name', 'last_name')

    # Streamlined fieldsets focusing on user container
    fieldsets = (
        ('👤 User Identity', {
            'fields': ('username', 'email', 'first_name', 'last_name')
        }),
        ('🔐 Account Status', {
            'fields': ('is_active', 'date_joined', 'last_login'),
        }),
        ('⚙️ Administrative Access', {
            'fields': (
                'is_staff', 'is_superuser', 'groups', 'user_permissions'
            ),
            'classes': ('collapse',),
        }),
    )

    # Enhanced add form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    list_editable = ('is_active',)
    ordering = ('-date_joined',)

    def get_queryset(self, request):
        """Optimize queries for user data container."""
        queryset = super().get_queryset(request)
        return queryset.select_related('settings').prefetch_related(
            'transactions'
        )

    @admin.display(description='Cycle Start')
    def cycle_start_date(self, obj):
        """Show the user's billing cycle start."""
        if hasattr(obj, 'settings') and obj.settings:
            return obj.settings.cycle_start_date.strftime('%Y-%m-%d')
        return "Not set"

    @admin.display(description='Currency')
    def currency_display(self, obj):
        """Show user's preferred currency."""
        if hasattr(obj, 'settings') and obj.settings:
            currency_dict = dict(CURRENCY_CHOICES)
            code = obj.settings.currency_code
            return currency_dict.get(code, code)
        return "USD"

    @admin.display(description='Total Transactions')
    def transaction_count(self, obj):
        """Show total transactions for this user."""
        count = Transaction.objects.filter(user=obj).count()
        if count == 0:
            return "No transactions"
        return f"{count} transactions"


class CategoryAdmin(admin.ModelAdmin):
    """I manage expense categories with enhanced add/edit capabilities."""

    list_display = ('name', 'is_active', 'transaction_count', 'created_info')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('name',)
    list_editable = ('is_active',)

    # Enhanced fieldsets for adding/editing categories
    fieldsets = (
        ('Category Details', {
            'fields': ('name', 'is_active'),
            'description': 'Manage expense category name and status.',
        }),
    )

    # Simplified add form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name',),
            'description': (
                'Create a new expense category. '
                'Categories are active by default.'
            ),
        }),
    )

    @admin.display(description='Transaction Count')
    def transaction_count(self, obj):
        """Show how many transactions use this category."""
        count = obj.transaction_set.count()
        return f"{count} transaction{'s' if count != 1 else ''}"

    @admin.display(description='Usage Info')
    def created_info(self, obj):
        """Show when category was first used."""
        first_transaction = obj.transaction_set.order_by('created_at').first()
        if first_transaction:
            date_str = first_transaction.created_at.strftime('%Y-%m-%d')
            return f"First used: {date_str}"
        return "Never used"


class TransactionAdminForm(forms.ModelForm):
    """Custom form for editing transactions with formatted amounts."""

    formatted_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Amount"
    )

    class Meta:
        model = Transaction
        fields = [
            'user', 'name', 'type', 'formatted_amount',
            'category', 'occurred_on', 'note'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert cents to decimal for display
        if self.instance and self.instance.amount_in_cents is not None:
            amount_decimal = self.instance.amount_in_cents / 100
            self.fields['formatted_amount'].initial = amount_decimal

    def save(self, commit=True):
        # Convert decimal back to cents before saving
        if 'formatted_amount' in self.cleaned_data:
            amount_decimal = self.cleaned_data['formatted_amount']
            self.instance.amount_in_cents = int(amount_decimal * 100)
        return super().save(commit)


class TransactionAdmin(admin.ModelAdmin):
    """I organize transactions with user-centric grouping and filtering."""

    form = TransactionAdminForm
    list_display = (
        'name', 'user_workspace', 'type', 'formatted_amount',
        'category', 'occurred_on', 'created_at'
    )
    list_filter = (
        'type', 'category', 'occurred_on', 'created_at',
        'user', 'user__settings__currency_code'
    )
    search_fields = ('name', 'note', 'user__username', 'user__email')
    date_hierarchy = 'occurred_on'
    ordering = ('-occurred_on', '-created_at')
    readonly_fields = ('created_at', 'updated_at')

    # Enhanced fieldsets with user container focus
    fieldsets = (
        ('👤 User & Transaction Details', {
            'fields': ('user', 'name', 'type', 'formatted_amount', 'category')
        }),
        ('📅 When & Where', {
            'fields': ('occurred_on',)
        }),
        ('📝 Additional Info', {
            'fields': ('note',),
            'classes': ('collapse',)
        }),
        ('🔧 System Info', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Group by user for better organization
    list_per_page = 50

    @admin.display(description='User')
    def user_workspace(self, obj):
        """Show user with workspace info."""
        full_name = obj.user.get_full_name()
        email = obj.user.email
        user_detail = full_name or email or 'No details'
        return f"{obj.user.username} (User: {user_detail})"

    @admin.display(description='Amount')
    def formatted_amount(self, obj):
        """Display amount in user's preferred currency format."""
        if not obj or obj.amount_in_cents is None:
            return "No amount"

        try:
            amount = obj.amount_in_cents / 100
            currency_code = 'USD'  # Default currency

            # Try to get user currency preference
            if obj.user:
                try:
                    # Get or create user settings
                    from .models import UserSettings
                    settings, created = UserSettings.objects.get_or_create(
                        user=obj.user
                    )
                    currency_code = settings.currency_code or 'USD'
                except Exception:
                    currency_code = 'USD'

            symbol = "£" if currency_code == 'GBP' else "$"
            # Red for expenses, green for income
            color = "#dc3545" if obj.type == 'OUTGO' else "#28a745"
            amount_str = f"{symbol}{amount:.2f}"
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color, amount_str
            )
        except Exception as e:
            return f"Error: {str(e)[:20]}"

    def get_queryset(self, request):
        """Optimize queries for user data display."""
        return super().get_queryset(request).select_related(
            'user', 'user__settings', 'category'
        )


ledgerly_admin_site.register(AccountUser, AccountUserAdmin)
ledgerly_admin_site.register(Category, CategoryAdmin)
ledgerly_admin_site.register(Transaction, TransactionAdmin)
