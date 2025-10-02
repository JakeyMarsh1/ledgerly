"""Regression tests for Ledgerly's transaction flows."""

from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Transaction, UserSettings


class TransactionFlowTests(TestCase):
    """Exercise dashboard search, detail editing, and deletion flows."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='super-secret',
        )
        self.category = Category.objects.create(name='Technology')

    def _login(self):
        logged_in = self.client.login(
            username='testuser',
            password='super-secret',
        )
        self.assertTrue(logged_in)

    def test_dashboard_search_matches_transaction_name(self):
        """Searching should match against the transaction name field."""

        Transaction.objects.create(
            user=self.user,
            name='Laptop Purchase',
            type=Transaction.OUTGO,
            amount_in_cents=150000,
            category=self.category,
            occurred_on=date(2025, 9, 1),
            note='Work device',
        )

        self._login()
        response = self.client.get(reverse('dashboard'), {'q': 'laptop'})

        self.assertContains(response, 'Laptop Purchase')

    def test_transaction_detail_allows_updates(self):
        """Users can update transaction fields via the detail view."""

        transaction = Transaction.objects.create(
            user=self.user,
            name='Original Name',
            type=Transaction.OUTGO,
            amount_in_cents=8000,
            category=self.category,
            occurred_on=date(2025, 9, 2),
            note='Initial note',
        )

        self._login()
        response = self.client.post(
            reverse('transaction_detail', args=[transaction.pk]),
            {
                'name': 'Updated Name',
                'type': Transaction.OUTGO,
                'amount_in_cents': '82.00',
                'category': self.category.pk,
                'occurred_on': '2025-09-03',
                'note': 'Updated note',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True})
        transaction.refresh_from_db()
        self.assertEqual(transaction.name, 'Updated Name')
        self.assertEqual(transaction.amount_in_cents, 8200)
        self.assertEqual(transaction.note, 'Updated note')

        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertContains(
            dashboard_response,
            'Transaction updated successfully.',
        )

    def test_transaction_detail_modal_get(self):
        """AJAX GET returns modal-friendly HTML content."""

        transaction = Transaction.objects.create(
            user=self.user,
            name='Inspect Me',
            type=Transaction.INCOME,
            amount_in_cents=12345,
            occurred_on=date(2025, 9, 5),
        )

        self._login()
        response = self.client.get(
            reverse('transaction_detail', args=[transaction.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('modal-header', response.content.decode())
        self.assertIn('Edit Transaction', response.content.decode())

    def test_transaction_delete_flow(self):
        """Posting to the delete view removes the transaction."""

        transaction = Transaction.objects.create(
            user=self.user,
            name='Disposable',
            type=Transaction.OUTGO,
            amount_in_cents=5000,
            category=self.category,
            occurred_on=date(2025, 9, 4),
        )

        self._login()
        response = self.client.post(
            reverse('transaction_delete', args=[transaction.pk]),
            follow=True,
        )

        self.assertContains(response, 'Transaction deleted successfully.')
        self.assertFalse(
            Transaction.objects.filter(
                pk=transaction.pk,
                user=self.user,
            ).exists()
        )

    def test_transaction_calendar_endpoint_returns_month_data(self):
        """Calendar endpoint returns grouped transactions for the month."""

        Transaction.objects.create(
            user=self.user,
            name='Calendar Test',
            type=Transaction.INCOME,
            amount_in_cents=12000,
            occurred_on=date(2025, 9, 5),
            note='Calendar note',
        )

        Transaction.objects.create(
            user=self.user,
            name='Same Day Expense',
            type=Transaction.OUTGO,
            amount_in_cents=3000,
            category=self.category,
            occurred_on=date(2025, 9, 5),
        )

        self._login()
        response = self.client.get(
            reverse('transaction_calendar_data'),
            {'year': '2025', 'month': '9'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['year'], 2025)
        self.assertEqual(data['month'], 9)

        days_by_date = {day['date']: day for day in data['days']}
        self.assertIn('2025-09-05', days_by_date)
        self.assertEqual(len(days_by_date['2025-09-05']['transactions']), 2)

    def test_transaction_calendar_requires_login(self):
        """Anonymous users should be redirected to log in."""

        response = self.client.get(reverse('transaction_calendar_data'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_clear_history_removes_user_transactions(self):
        """Clearing history deletes only the logged-in user's transactions."""

        Transaction.objects.create(
            user=self.user,
            name='Keep or not',
            type=Transaction.OUTGO,
            amount_in_cents=2000,
            category=self.category,
            occurred_on=date(2025, 9, 6),
        )
        other_user = User.objects.create_user(
            username='other',
            password='super-secret',
        )
        Transaction.objects.create(
            user=other_user,
            name='Other user transaction',
            type=Transaction.OUTGO,
            amount_in_cents=4000,
            occurred_on=date(2025, 9, 6),
        )

        self._login()
        response = self.client.post(
            reverse('account_clear_history'),
            follow=True,
        )

        self.assertContains(
            response,
            'Transaction history cleared. Enjoy the fresh start!',
        )
        self.assertFalse(
            Transaction.objects.filter(user=self.user).exists()
        )
        self.assertTrue(
            Transaction.objects.filter(user=other_user).exists()
        )

    def test_transaction_suggestions_endpoint(self):
        """Suggestions endpoint returns matching names and categories."""

        Transaction.objects.create(
            user=self.user,
            name='Asda Groceries',
            type=Transaction.OUTGO,
            amount_in_cents=3500,
            category=self.category,
            occurred_on=date(2025, 9, 7),
        )

        self.category.name = 'Asda Superstore'
        self.category.save(update_fields=['name'])

        self._login()
        response = self.client.get(
            reverse('transaction_suggestions'),
            {'q': 'asd'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('suggestions', data)
        self.assertTrue(
            any('Asda' in suggestion for suggestion in data['suggestions'])
        )

    def test_dashboard_accepts_large_amounts(self):
        """Submitting a large transaction remains within storage limits."""

        self._login()
        mega_amount = '5000000000000.00'  # $5 trillion
        response = self.client.post(
            reverse('dashboard'),
            {
                'action': 'add_transaction',
                'type': Transaction.INCOME,
                'name': 'Mega Funding',
                'amount_in_cents': mega_amount,
                'occurred_on': '2025-09-10',
                'note': 'Large test transaction',
            },
            follow=True,
        )

        self.assertContains(response, 'Income saved successfully.')
        txn = Transaction.objects.get(user=self.user, name='Mega Funding')
        self.assertEqual(txn.amount_in_cents, 500000000000000)

    def test_currency_settings_update_changes_symbol(self):
        """Users can change their preferred currency from the settings page."""

        self._login()
        settings, _ = UserSettings.objects.get_or_create(user=self.user)
        self.assertEqual(settings.currency_code, 'USD')

        response = self.client.post(
            reverse('account_currency_settings'),
            {
                'currency_code': 'GBP',
            },
            follow=True,
        )

        self.assertEqual(response.redirect_chain[-1][0], reverse('dashboard'))
        self.assertContains(
            response,
            'Currency updated to British Pound (£).'
        )
        settings.refresh_from_db()
        self.assertEqual(settings.currency_code, 'GBP')

    def test_transaction_detail_form_shows_decimal_amount(self):
        """Edit form should display amount formatted as decimal units."""

        transaction = Transaction.objects.create(
            user=self.user,
            name='Decimal Check',
            type=Transaction.INCOME,
            amount_in_cents=12345,
            occurred_on=date(2025, 9, 8),
        )

        self._login()
        response = self.client.get(
            reverse('transaction_detail', args=[transaction.pk])
        )

        self.assertContains(response, '123.45')

    def test_transaction_search_results_endpoint_returns_html(self):
        """Search results endpoint should render matching transactions."""

        Transaction.objects.create(
            user=self.user,
            name='Laptop Purchase',
            type=Transaction.OUTGO,
            amount_in_cents=150000,
            category=self.category,
            occurred_on=date(2025, 9, 1),
        )

        self._login()
        response = self.client.get(
            reverse('transaction_search_results'),
            {'q': 'laptop'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertIn('Laptop Purchase', data['html'])

    def test_transaction_search_results_endpoint_handles_empty_query(self):
        """Empty search queries should return no results."""

        self._login()
        response = self.client.get(
            reverse('transaction_search_results'),
            {'q': ''},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'html': '', 'count': 0})
