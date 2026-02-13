from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from decimal import Decimal

from app.models import (
    CustomUser, Transaction, Stock, AdminWallet,
    Portfolio, Notification, UserStockPosition,
    Trader, UserCopyTraderHistory, UserTraderCopy,
    WalletConnection,
)
from .forms import (
    AddTradeForm, AddEarningsForm, ApproveDepositForm,
    ApproveWithdrawalForm, ApproveKYCForm, AddCopyTradeForm,
    EditCopyTradeForm, AddTraderForm, EditTraderForm, EditDepositForm,
    AdminWalletForm,
)
from .decorators import admin_required


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _paginate(queryset_or_list, request, per_page=20):
    """Return a Page object and metadata dict."""
    paginator = Paginator(queryset_or_list, per_page)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj, paginator


def _resolve_range(exact, range_val, mapping, fallback=0):
    """Pick exact value, mapped range mid-point, or fallback."""
    if exact:
        return exact
    if range_val and range_val in mapping:
        return mapping[range_val]
    return fallback


_COPIERS_MAP = {'1-10': 5, '11-20': 15, '21-30': 25, '31-50': 40, '51-100': 75, '101-200': 150, '201-300': 250, '300+': 350}
_TRADES_MAP = {'1-50': 25, '51-100': 75, '101-200': 150, '201-300': 250, '301-500': 400, '500+': 600}
_SUBS_MAP = {'0': 0, '1-10': 5, '11-25': 18, '26-50': 38, '51-100': 75, '101-200': 150, '200+': 250}
_POS_MAP = {'0': 0, '1-5': 3, '6-10': 8, '11-20': 15, '20+': 25}


def _pick(custom, dropdown, fallback):
    """Return custom value if truthy, else dropdown, else fallback."""
    if custom:
        return custom
    if dropdown:
        return Decimal(dropdown) if isinstance(fallback, Decimal) else dropdown
    return fallback


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard:dashboard')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, f'Welcome back, {user.email}!')
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')
    return render(request, 'dashboard/login.html')


@admin_required
def admin_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('dashboard:login')


# ---------------------------------------------------------------------------
# Dashboard Overview
# ---------------------------------------------------------------------------

@admin_required
def dashboard(request):
    total_users = CustomUser.objects.filter(is_active=True).count()
    verified_users = CustomUser.objects.filter(is_verified=True).count()
    pending_kyc = CustomUser.objects.filter(has_submitted_kyc=True, is_verified=False).count()
    pending_deposits = Transaction.objects.filter(transaction_type='deposit', status='pending').count()
    pending_withdrawals = Transaction.objects.filter(transaction_type='withdrawal', status='pending').count()
    total_deposits = Transaction.objects.filter(transaction_type='deposit', status='completed').aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
    total_withdrawals = Transaction.objects.filter(transaction_type='withdrawal', status='completed').aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
    recent_transactions = Transaction.objects.select_related('user').order_by('-created_at')[:10]
    recent_users = CustomUser.objects.filter(is_active=True).order_by('-date_joined')[:5]

    return render(request, 'dashboard/dashboard.html', {
        'total_users': total_users,
        'verified_users': verified_users,
        'pending_kyc': pending_kyc,
        'pending_deposits': pending_deposits,
        'pending_withdrawals': pending_withdrawals,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'recent_transactions': recent_transactions,
        'recent_users': recent_users,
    })


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@admin_required
def users_list(request):
    search_query = request.GET.get('search', '')
    filter_status = request.GET.get('status', '')
    users = CustomUser.objects.all().order_by('-date_joined')

    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) | Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) | Q(account_id__icontains=search_query)
        )
    if filter_status == 'verified':
        users = users.filter(is_verified=True)
    elif filter_status == 'unverified':
        users = users.filter(is_verified=False)
    elif filter_status == 'kyc_pending':
        users = users.filter(has_submitted_kyc=True, is_verified=False)

    page_obj, paginator = _paginate(users, request, 20)
    return render(request, 'dashboard/users.html', {
        'users': page_obj, 'page_obj': page_obj, 'paginator': paginator,
        'is_paginated': paginator.num_pages > 1,
        'search_query': search_query, 'filter_status': filter_status,
    })


@admin_required
def user_detail(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'verify':
            user.is_verified = True
            user.save()
            messages.success(request, f'{user.email} has been verified.')
        elif action == 'unverify':
            user.is_verified = False
            user.save()
            messages.success(request, f'{user.email} verification removed.')
        elif action == 'activate':
            user.is_active = True
            user.save()
            messages.success(request, f'{user.email} has been activated.')
        elif action == 'deactivate':
            user.is_active = False
            user.save()
            messages.success(request, f'{user.email} has been deactivated.')
        elif action == 'update_balance':
            new_balance = request.POST.get('balance')
            if new_balance:
                user.balance = Decimal(new_balance)
                user.save()
                messages.success(request, f'Balance updated to ${user.balance}')
        elif action == 'update_profit':
            new_profit = request.POST.get('profit')
            if new_profit:
                user.profit = Decimal(new_profit)
                user.save()
                messages.success(request, f'Profit updated to ${user.profit}')
        elif action == 'toggle_transfer':
            user.can_transfer = not user.can_transfer
            user.save(update_fields=['can_transfer'])
            status = 'enabled' if user.can_transfer else 'disabled'
            messages.success(request, f'Transfer {status} for {user.email}')
        elif action == 'delete_portfolio':
            portfolio_id = request.POST.get('portfolio_id')
            if portfolio_id:
                Portfolio.objects.filter(id=portfolio_id, user=user).delete()
                messages.success(request, 'Portfolio entry deleted.')
        elif action == 'update_portfolio':
            portfolio_id = request.POST.get('portfolio_id')
            if portfolio_id:
                try:
                    p = Portfolio.objects.get(id=portfolio_id, user=user)
                    p.invested = Decimal(request.POST.get('invested', p.invested))
                    p.profit_loss = Decimal(request.POST.get('profit_loss', p.profit_loss))
                    p.value = p.invested + p.profit_loss
                    p.is_active = request.POST.get('is_active') == 'on'
                    p.save()
                    messages.success(request, 'Portfolio updated.')
                except Portfolio.DoesNotExist:
                    messages.error(request, 'Portfolio not found.')
        return redirect('dashboard:user_detail', user_id=user.id)

    transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:20]
    portfolios = Portfolio.objects.filter(user=user).order_by('-is_active', '-opened_at')

    return render(request, 'dashboard/user_detail.html', {
        'view_user': user, 'transactions': transactions, 'portfolios': portfolios,
    })


# ---------------------------------------------------------------------------
# KYC
# ---------------------------------------------------------------------------

@admin_required
def kyc_requests(request):
    status_filter = request.GET.get('status', 'pending')
    if status_filter == 'pending':
        users = CustomUser.objects.filter(has_submitted_kyc=True, is_verified=False)
    elif status_filter == 'approved':
        users = CustomUser.objects.filter(has_submitted_kyc=True, is_verified=True)
    else:
        users = CustomUser.objects.filter(has_submitted_kyc=True)
    users = users.order_by('-date_joined')

    page_obj, paginator = _paginate(users, request, 15)
    return render(request, 'dashboard/kyc_requests.html', {
        'kyc_requests': page_obj, 'page_obj': page_obj, 'paginator': paginator,
        'is_paginated': paginator.num_pages > 1, 'status_filter': status_filter,
    })


@admin_required
def kyc_detail(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, has_submitted_kyc=True)
    if request.method == 'POST':
        form = ApproveKYCForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            admin_notes = form.cleaned_data['admin_notes']
            if action == 'approve':
                user.is_verified = True
                user.save()
                Notification.objects.create(user=user, type='system', title='KYC Approved',
                    message='Your KYC verification has been approved!',
                    full_details='Your account is now fully verified. You can access all features.')
                messages.success(request, f'KYC approved for {user.email}')
            else:
                user.is_verified = False
                user.has_submitted_kyc = False
                user.save()
                Notification.objects.create(user=user, type='alert', title='KYC Rejected',
                    message='Your KYC verification was not approved.',
                    full_details=admin_notes or 'Please review your documents and submit again.')
                messages.warning(request, f'KYC rejected for {user.email}')
            return redirect('dashboard:kyc_requests')
    else:
        form = ApproveKYCForm()
    return render(request, 'dashboard/kyc_detail.html', {'view_user': user, 'form': form})


# ---------------------------------------------------------------------------
# Deposits
# ---------------------------------------------------------------------------

@admin_required
def deposits(request):
    status_filter = request.GET.get('status', 'pending')
    qs = Transaction.objects.filter(transaction_type='deposit').select_related('user').order_by('-created_at')
    if status_filter and status_filter != 'all':
        qs = qs.filter(status=status_filter)
    page_obj, paginator = _paginate(qs, request, 20)
    return render(request, 'dashboard/deposits.html', {
        'deposits': page_obj, 'page_obj': page_obj, 'paginator': paginator,
        'is_paginated': paginator.num_pages > 1, 'status_filter': status_filter,
    })


@admin_required
def deposit_detail(request, transaction_id):
    deposit = get_object_or_404(Transaction, id=transaction_id, transaction_type='deposit')
    if request.method == 'POST':
        form = ApproveDepositForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data['status']
            admin_notes = form.cleaned_data['admin_notes']
            deposit.status = status
            deposit.save()
            if status == 'completed':
                deposit.user.balance += deposit.amount
                deposit.user.save()
                Notification.objects.create(user=deposit.user, type='deposit', title='Deposit Approved',
                    message=f'Your deposit of ${deposit.amount} has been approved.',
                    full_details=f'Amount: ${deposit.amount}\nReference: {deposit.reference}')
                messages.success(request, f'Deposit approved — ${deposit.amount} credited to {deposit.user.email}')
            else:
                Notification.objects.create(user=deposit.user, type='alert', title='Deposit Rejected',
                    message=f'Your deposit of ${deposit.amount} was not approved.',
                    full_details=admin_notes or 'Please contact support.')
                messages.warning(request, f'Deposit rejected for {deposit.user.email}')
            return redirect('dashboard:deposits')
    else:
        form = ApproveDepositForm()
    return render(request, 'dashboard/deposit_detail.html', {'deposit': deposit, 'form': form})


@admin_required
def edit_deposit(request, transaction_id):
    deposit = get_object_or_404(Transaction, id=transaction_id, transaction_type='deposit')
    if request.method == 'POST':
        form = EditDepositForm(request.POST, request.FILES)
        if form.is_valid():
            old_amount, old_status = deposit.amount, deposit.status
            deposit.amount = form.cleaned_data['amount']
            deposit.currency = form.cleaned_data['currency']
            deposit.unit = form.cleaned_data['unit']
            deposit.status = form.cleaned_data['status']
            deposit.description = form.cleaned_data['description']
            deposit.reference = form.cleaned_data['reference']
            if form.cleaned_data.get('receipt'):
                deposit.receipt = form.cleaned_data['receipt']
            deposit.save()

            # Balance adjustments
            if old_status != deposit.status:
                if old_status == 'completed' and deposit.status != 'completed':
                    deposit.user.balance -= old_amount
                    deposit.user.save()
                    messages.warning(request, f'${old_amount} deducted from {deposit.user.email} balance.')
                elif old_status != 'completed' and deposit.status == 'completed':
                    deposit.user.balance += deposit.amount
                    deposit.user.save()
                    messages.success(request, f'${deposit.amount} credited to {deposit.user.email} balance.')
            elif deposit.status == 'completed' and old_amount != deposit.amount:
                diff = deposit.amount - old_amount
                deposit.user.balance += diff
                deposit.user.save()
                if diff > 0:
                    messages.success(request, f'Additional ${diff} credited.')
                else:
                    messages.warning(request, f'${abs(diff)} deducted.')

            Notification.objects.create(user=deposit.user, type='deposit', title='Deposit Updated',
                message='Your deposit has been updated by admin.',
                full_details=f'Amount: ${deposit.amount}\nCurrency: {deposit.currency}\nStatus: {deposit.status}\nRef: {deposit.reference}')
            messages.success(request, 'Deposit updated successfully!')
            return redirect('dashboard:deposit_detail', transaction_id=deposit.id)
    else:
        form = EditDepositForm(initial={
            'amount': deposit.amount, 'currency': deposit.currency, 'unit': deposit.unit,
            'status': deposit.status, 'description': deposit.description or '', 'reference': deposit.reference,
        })
    return render(request, 'dashboard/edit_deposit.html', {'form': form, 'deposit': deposit})


# ---------------------------------------------------------------------------
# Withdrawals
# ---------------------------------------------------------------------------

@admin_required
def withdrawals(request):
    status_filter = request.GET.get('status', 'pending')
    qs = Transaction.objects.filter(transaction_type='withdrawal').select_related('user').order_by('-created_at')
    if status_filter and status_filter != 'all':
        qs = qs.filter(status=status_filter)
    page_obj, paginator = _paginate(qs, request, 20)
    return render(request, 'dashboard/withdrawals.html', {
        'withdrawals': page_obj, 'page_obj': page_obj, 'paginator': paginator,
        'is_paginated': paginator.num_pages > 1, 'status_filter': status_filter,
    })


@admin_required
def withdrawal_detail(request, transaction_id):
    withdrawal = get_object_or_404(Transaction, id=transaction_id, transaction_type='withdrawal')
    if request.method == 'POST':
        form = ApproveWithdrawalForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data['status']
            admin_notes = form.cleaned_data['admin_notes']
            withdrawal.status = status
            withdrawal.save()
            if status == 'completed':
                Notification.objects.create(user=withdrawal.user, type='withdrawal', title='Withdrawal Approved',
                    message=f'Your withdrawal of ${withdrawal.amount} has been processed.',
                    full_details=f'Amount: ${withdrawal.amount}\nReference: {withdrawal.reference}')
                messages.success(request, f'Withdrawal approved for {withdrawal.user.email}')
            else:
                withdrawal.user.balance += withdrawal.amount
                withdrawal.user.save()
                Notification.objects.create(user=withdrawal.user, type='alert', title='Withdrawal Rejected',
                    message=f'Your withdrawal of ${withdrawal.amount} was not processed.',
                    full_details=admin_notes or 'Amount has been refunded to your balance.')
                messages.warning(request, f'Withdrawal rejected — amount refunded to {withdrawal.user.email}')
            return redirect('dashboard:withdrawals')
    else:
        form = ApproveWithdrawalForm()
    return render(request, 'dashboard/withdrawal_detail.html', {'withdrawal': withdrawal, 'form': form})


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

@admin_required
def transactions(request):
    tx_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    qs = Transaction.objects.select_related('user').order_by('-created_at')
    if tx_type:
        qs = qs.filter(transaction_type=tx_type)
    if status:
        qs = qs.filter(status=status)
    if search:
        qs = qs.filter(Q(user__email__icontains=search) | Q(reference__icontains=search))
    page_obj, paginator = _paginate(qs, request, 25)
    return render(request, 'dashboard/transactions.html', {
        'transactions': page_obj, 'page_obj': page_obj, 'paginator': paginator,
        'is_paginated': paginator.num_pages > 1,
        'transaction_type': tx_type, 'status': status, 'search': search,
    })


# ---------------------------------------------------------------------------
# Add Trade / Earnings
# ---------------------------------------------------------------------------

@admin_required
def add_trade(request):
    if request.method == 'POST':
        form = AddTradeForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user_email']
            entry = form.cleaned_data['entry']
            asset_type = form.cleaned_data['asset_type']
            asset = form.cleaned_data['asset']
            direction = form.cleaned_data['direction']
            profit = form.cleaned_data['profit'] or Decimal('0.00')

            Portfolio.objects.create(
                user=user, market=f"{asset} ({asset_type})", direction=direction.upper(),
                invested=entry, profit_loss=profit, value=entry + profit, is_active=True,
            )
            # Update user profit and balance when profit/loss is set
            if profit != Decimal('0.00'):
                user.profit = (user.profit or Decimal('0.00')) + profit
                user.balance = (user.balance or Decimal('0.00')) + profit
                user.save(update_fields=['profit', 'balance'])
            messages.success(request, f'Trade added for {user.email} (P/L: ${profit})')
            return redirect('dashboard:add_trade')
    else:
        form = AddTradeForm()
    return render(request, 'dashboard/add_trade.html', {'form': form})


@admin_required
def add_earnings(request):
    if request.method == 'POST':
        form = AddEarningsForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user_email']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data['description'] or 'Admin added earnings'
            user.balance += amount
            user.save()
            from django.utils.crypto import get_random_string
            Transaction.objects.create(
                user=user, transaction_type='deposit', amount=amount,
                status='completed', reference=f"EARN-{get_random_string(12).upper()}", description=description,
            )
            Notification.objects.create(user=user, type='system', title='Earnings Added',
                message=f'${amount} has been added to your account.', full_details=description)
            messages.success(request, f'${amount} added to {user.email}')
            return redirect('dashboard:add_earnings')
    else:
        form = AddEarningsForm()

    recent_earnings = Transaction.objects.filter(
        transaction_type='deposit', status='completed', description__icontains='admin'
    ).select_related('user').order_by('-created_at')[:10]
    return render(request, 'dashboard/add_earnings.html', {'form': form, 'recent_earnings': recent_earnings})


@admin_required
def get_assets_by_type(request):
    asset_type = request.GET.get('type', '')
    if asset_type == 'stock':
        assets = Stock.objects.filter(is_active=True).values('symbol', 'name')
        data = [{'value': s['symbol'], 'label': f"{s['symbol']} - {s['name']}"} for s in assets]
    elif asset_type == 'crypto':
        data = [
            {'value': 'BTC', 'label': 'Bitcoin (BTC)'}, {'value': 'ETH', 'label': 'Ethereum (ETH)'},
            {'value': 'BNB', 'label': 'Binance Coin (BNB)'}, {'value': 'SOL', 'label': 'Solana (SOL)'},
            {'value': 'XRP', 'label': 'Ripple (XRP)'}, {'value': 'ADA', 'label': 'Cardano (ADA)'},
            {'value': 'DOGE', 'label': 'Dogecoin (DOGE)'}, {'value': 'MATIC', 'label': 'Polygon (MATIC)'},
        ]
    elif asset_type == 'forex':
        data = [
            {'value': 'EURUSD', 'label': 'EUR/USD'}, {'value': 'GBPUSD', 'label': 'GBP/USD'},
            {'value': 'USDJPY', 'label': 'USD/JPY'}, {'value': 'USDCAD', 'label': 'USD/CAD'},
            {'value': 'AUDUSD', 'label': 'AUD/USD'}, {'value': 'NZDUSD', 'label': 'NZD/USD'},
        ]
    else:
        data = []
    return JsonResponse({'assets': data})


# ---------------------------------------------------------------------------
# Copy Trading
# ---------------------------------------------------------------------------

@admin_required
def copy_trades_list(request):
    trader_id = request.GET.get('trader')
    status = request.GET.get('status')
    search = request.GET.get('search')
    qs = UserCopyTraderHistory.objects.select_related('trader').all()
    if trader_id:
        qs = qs.filter(trader_id=trader_id)
    if status:
        qs = qs.filter(status=status)
    if search:
        qs = qs.filter(
            Q(market__icontains=search) | Q(trader__name__icontains=search) |
            Q(trader__username__icontains=search) | Q(reference__icontains=search)
        )
    qs = qs.order_by('-opened_at')
    page_obj = Paginator(qs, 20).get_page(request.GET.get('page'))

    for trade in page_obj:
        trade.copying_users_count = UserTraderCopy.objects.filter(trader=trade.trader, is_actively_copying=True).count()

    traders = Trader.objects.filter(is_active=True).order_by('name')
    return render(request, 'dashboard/copy_trades_list.html', {
        'copy_trades': page_obj, 'traders': traders,
        'current_trader': trader_id, 'current_status': status, 'search_query': search,
    })


@admin_required
def copy_trade_detail(request, trade_id):
    ct = get_object_or_404(UserCopyTraderHistory.objects.select_related('trader'), id=trade_id)
    copying_users = UserTraderCopy.objects.filter(trader=ct.trader, is_actively_copying=True).select_related('user')
    users_with_pl = []
    for rel in copying_users:
        pl = ct.calculate_user_profit_loss(rel.initial_investment_amount)
        users_with_pl.append({'copy_relation': rel, 'profit_loss': pl, 'is_profit': pl >= 0})
    return render(request, 'dashboard/copy_trade_detail.html', {
        'copy_trade': ct, 'users_with_pl': users_with_pl, 'affected_users_count': len(users_with_pl),
    })


@admin_required
def add_copy_trade(request):
    if request.method == 'POST':
        form = AddCopyTradeForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            ct = UserCopyTraderHistory.objects.create(
                trader=d['trader'], market=d['market'], direction=d['direction'],
                duration=d['duration'], amount=d['amount'], entry_price=d['entry_price'],
                exit_price=d.get('exit_price'), profit_loss_percent=d['profit_loss_percent'],
                status=d['status'], closed_at=d.get('closed_at'), notes=d.get('notes', ''),
            )
            copying = UserTraderCopy.objects.filter(trader=d['trader'], is_actively_copying=True)
            for rel in copying:
                user = rel.user
                user_pl = ct.calculate_user_profit_loss(rel.initial_investment_amount)
                if d['status'] == 'closed' and d['profit_loss_percent']:
                    user.profit = (user.profit or Decimal('0.00')) + user_pl
                    user.balance = (user.balance or Decimal('0.00')) + user_pl
                    user.save(update_fields=['profit', 'balance'])
                title = f'Trade Profit from {d["trader"].name}!' if user_pl >= 0 else f'Trade Update from {d["trader"].name}'
                msg = f'Copy trade on {d["market"]} {"gained" if user_pl >= 0 else "lost"} ${abs(user_pl)}'
                Notification.objects.create(user=user, type='trade', title=title, message=msg,
                    full_details=f'Trader: {d["trader"].name}\nMarket: {d["market"]}\nDirection: {d["direction"].upper()}\nYour Investment: ${rel.initial_investment_amount}\nP/L: ${user_pl} ({d["profit_loss_percent"]}%)\nStatus: {d["status"].capitalize()}')
            messages.success(request, f'Trade added for {d["trader"].name}! Notified {copying.count()} copying users.')
            return redirect('dashboard:copy_trades_list')
    else:
        form = AddCopyTradeForm()
    return render(request, 'dashboard/add_copy_trade.html', {'form': form})


@admin_required
def edit_copy_trade(request, trade_id):
    ct = get_object_or_404(UserCopyTraderHistory, id=trade_id)
    old_status = ct.status
    old_pnl = ct.profit_loss_percent

    if request.method == 'POST':
        form = EditCopyTradeForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            ct.trader = d['trader']
            ct.market = d['market']
            ct.direction = d['direction']
            ct.duration = d['duration']
            ct.amount = d['amount']
            ct.entry_price = d['entry_price']
            ct.exit_price = d.get('exit_price')
            ct.profit_loss_percent = d['profit_loss_percent']
            ct.status = d['status']
            ct.closed_at = d.get('closed_at')
            ct.notes = d.get('notes', '')
            ct.save()

            # If trade was just closed (status changed to closed), update copying users
            if d['status'] == 'closed' and old_status != 'closed':
                copying = UserTraderCopy.objects.filter(trader=ct.trader, is_actively_copying=True)
                for rel in copying:
                    user = rel.user
                    user_pl = ct.calculate_user_profit_loss(rel.initial_investment_amount)
                    user.profit = (user.profit or Decimal('0.00')) + user_pl
                    user.balance = (user.balance or Decimal('0.00')) + user_pl
                    user.save(update_fields=['profit', 'balance'])

            messages.success(request, f'Copy trade #{ct.id} updated.')
            return redirect('dashboard:copy_trade_detail', trade_id=ct.id)
    else:
        form = EditCopyTradeForm(initial={
            'trader': ct.trader, 'market': ct.market, 'direction': ct.direction,
            'duration': ct.duration, 'amount': ct.amount, 'entry_price': ct.entry_price,
            'exit_price': ct.exit_price, 'profit_loss_percent': ct.profit_loss_percent,
            'status': ct.status, 'closed_at': ct.closed_at, 'notes': ct.notes,
        })
    return render(request, 'dashboard/edit_copy_trade.html', {'form': form, 'copy_trade': ct})


@admin_required
def delete_copy_trade(request, trade_id):
    ct = get_object_or_404(UserCopyTraderHistory, id=trade_id)
    if request.method == 'POST':
        ct.delete()
        messages.success(request, f'Copy trade #{trade_id} deleted.')
        return redirect('dashboard:copy_trades_list')
    return render(request, 'dashboard/delete_copy_trade.html', {'copy_trade': ct})


# ---------------------------------------------------------------------------
# Traders
# ---------------------------------------------------------------------------

@admin_required
def traders_list(request):
    search = request.GET.get('search', '')
    badge_filter = request.GET.get('badge', '')
    active_filter = request.GET.get('active', '')
    qs = Trader.objects.all().order_by('-gain', '-copiers')
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(username__icontains=search) | Q(country__icontains=search))
    if badge_filter:
        qs = qs.filter(badge=badge_filter)
    if active_filter:
        qs = qs.filter(is_active=(active_filter == 'active'))
    page_obj, paginator = _paginate(qs, request, 20)
    return render(request, 'dashboard/traders_list.html', {
        'traders': page_obj, 'page_obj': page_obj, 'paginator': paginator,
        'is_paginated': paginator.num_pages > 1,
        'search': search, 'badge_filter': badge_filter, 'active_filter': active_filter,
    })


def _build_trader_data(form):
    """Extract cleaned trader field values from form, handling dropdown/custom logic."""
    d = form.cleaned_data
    capital = _pick(d.get('capital'), d.get('capital_dropdown'), '0')
    gain = _pick(d.get('gain'), d.get('gain_dropdown'), Decimal('0.00'))
    if isinstance(gain, str):
        gain = Decimal(gain)
    avg_profit = _pick(d.get('avg_profit_percent'), d.get('avg_profit_dropdown'), Decimal('0.00'))
    if isinstance(avg_profit, str):
        avg_profit = Decimal(avg_profit)
    avg_loss = _pick(d.get('avg_loss_percent'), d.get('avg_loss_dropdown'), Decimal('0.00'))
    if isinstance(avg_loss, str):
        avg_loss = Decimal(avg_loss)
    wins = _pick(d.get('total_wins'), d.get('total_wins_dropdown'), 0)
    if isinstance(wins, str):
        wins = int(wins)
    losses = _pick(d.get('total_losses'), d.get('total_losses_dropdown'), 0)
    if isinstance(losses, str):
        losses = int(losses)
    copiers = _resolve_range(d.get('copiers'), d.get('copiers_range'), _COPIERS_MAP)
    trades = _resolve_range(d.get('trades'), d.get('trades_range'), _TRADES_MAP)
    subscribers = _resolve_range(d.get('subscribers'), d.get('subscribers_range'), _SUBS_MAP)
    positions = _resolve_range(d.get('current_positions'), d.get('current_positions_range'), _POS_MAP)
    expert = Decimal(d['expert_rating']) if d.get('expert_rating') else Decimal('5.00')
    return {
        'name': d['name'], 'username': d['username'], 'country': d['country'], 'badge': d['badge'],
        'capital': capital, 'gain': gain, 'risk': int(d['risk']),
        'copiers': copiers, 'trades': trades, 'avg_trade_time': d['avg_trade_time'],
        'avg_profit_percent': avg_profit, 'avg_loss_percent': avg_loss,
        'total_wins': wins, 'total_losses': losses,
        'subscribers': subscribers, 'current_positions': positions, 'expert_rating': expert,
        'return_ytd': d.get('return_ytd') or Decimal('0.00'),
        'avg_score_7d': d.get('avg_score_7d') or Decimal('0.00'),
        'profitable_weeks': d.get('profitable_weeks') or Decimal('0.00'),
        'min_account_threshold': d.get('min_account_threshold') or Decimal('0.00'),
        'is_active': d.get('is_active', True),
        'total_trades_12m': trades,
    }


@admin_required
def add_trader(request):
    if request.method == 'POST':
        form = AddTraderForm(request.POST, request.FILES)
        if form.is_valid():
            data = _build_trader_data(form)
            data['avatar'] = form.cleaned_data.get('avatar')
            trader = Trader.objects.create(**data)
            messages.success(request, f'Trader "{trader.name}" added successfully!')
            return redirect('dashboard:traders_list')
    else:
        form = AddTraderForm()
    return render(request, 'dashboard/add_trader.html', {'form': form})


@admin_required
def trader_detail(request, trader_id):
    trader = get_object_or_404(Trader, id=trader_id)
    all_ct = UserCopyTraderHistory.objects.filter(trader=trader).select_related('trader').order_by('-opened_at')
    total_trades = all_ct.count()
    open_trades = all_ct.filter(status='open').count()
    closed_trades = all_ct.filter(status='closed').count()
    copy_trades = all_ct[:10]
    copying_users = UserTraderCopy.objects.filter(trader=trader, is_actively_copying=True).select_related('user')
    return render(request, 'dashboard/trader_detail.html', {
        'trader': trader, 'copy_trades': copy_trades, 'copying_users': copying_users,
        'total_copying_users': copying_users.count(),
        'total_trades': total_trades, 'open_trades': open_trades, 'closed_trades': closed_trades,
    })


@admin_required
def edit_trader(request, trader_id):
    trader = get_object_or_404(Trader, id=trader_id)
    if request.method == 'POST':
        form = EditTraderForm(request.POST, request.FILES)
        if form.is_valid():
            data = _build_trader_data(form)
            for key, val in data.items():
                setattr(trader, key, val)
            if form.cleaned_data.get('avatar'):
                trader.avatar = form.cleaned_data['avatar']
            trader.save()
            messages.success(request, f'Trader "{trader.name}" updated successfully!')
            return redirect('dashboard:trader_detail', trader_id=trader.id)
    else:
        form = EditTraderForm(initial={
            'name': trader.name, 'username': trader.username, 'country': trader.country,
            'badge': trader.badge, 'capital': trader.capital, 'gain': trader.gain,
            'risk': str(trader.risk), 'avg_trade_time': trader.avg_trade_time,
            'copiers': trader.copiers, 'trades': trader.trades,
            'avg_profit_percent': trader.avg_profit_percent, 'avg_loss_percent': trader.avg_loss_percent,
            'total_wins': trader.total_wins, 'total_losses': trader.total_losses,
            'subscribers': trader.subscribers, 'current_positions': trader.current_positions,
            'expert_rating': str(float(trader.expert_rating)),
            'return_ytd': trader.return_ytd, 'avg_score_7d': trader.avg_score_7d,
            'profitable_weeks': trader.profitable_weeks, 'min_account_threshold': trader.min_account_threshold,
            'is_active': trader.is_active,
        })
    return render(request, 'dashboard/edit_trader.html', {'form': form, 'trader': trader})


# ---------------------------------------------------------------------------
# Investors
# ---------------------------------------------------------------------------

@admin_required
def investors_list(request):
    search_query = request.GET.get('search', '')
    investor_ids = Transaction.objects.filter(transaction_type='deposit').values_list('user_id', flat=True).distinct()
    investors = CustomUser.objects.filter(id__in=investor_ids).order_by('-date_joined')
    if search_query:
        investors = investors.filter(
            Q(email__icontains=search_query) | Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) | Q(account_id__icontains=search_query)
        )
    investors_data = []
    for inv in investors:
        deps = Transaction.objects.filter(user=inv, transaction_type='deposit')
        investors_data.append({
            'user': inv,
            'total_deposits': deps.count(),
            'completed_deposits': deps.filter(status='completed').count(),
            'pending_deposits': deps.filter(status='pending').count(),
            'total_amount': deps.filter(status='completed').aggregate(t=Sum('amount'))['t'] or Decimal('0.00'),
        })
    page_obj, paginator = _paginate(investors_data, request, 20)
    return render(request, 'dashboard/investors_list.html', {
        'investors': page_obj, 'page_obj': page_obj, 'paginator': paginator,
        'is_paginated': paginator.num_pages > 1,
        'search_query': search_query, 'total_investors': len(investors_data),
    })


@admin_required
def investor_detail(request, user_id):
    investor = get_object_or_404(CustomUser, id=user_id)
    deps = Transaction.objects.filter(user=investor, transaction_type='deposit').order_by('-created_at')
    completed = deps.filter(status='completed')
    pending = deps.filter(status='pending')
    failed = deps.filter(status='failed')
    page_obj, paginator = _paginate(deps, request, 15)
    return render(request, 'dashboard/investor_detail.html', {
        'investor': investor, 'deposits': page_obj, 'page_obj': page_obj, 'paginator': paginator,
        'is_paginated': paginator.num_pages > 1,
        'total_deposits': deps.count(), 'completed_count': completed.count(),
        'pending_count': pending.count(), 'failed_count': failed.count(),
        'total_completed_amount': completed.aggregate(t=Sum('amount'))['t'] or Decimal('0.00'),
        'total_pending_amount': pending.aggregate(t=Sum('amount'))['t'] or Decimal('0.00'),
    })


# ---------------------------------------------------------------------------
# Admin Wallets
# ---------------------------------------------------------------------------

@admin_required
def wallets_list(request):
    wallets = AdminWallet.objects.all().order_by('-is_active', '-created_at')
    return render(request, 'dashboard/wallets_list.html', {'wallets': wallets})


@admin_required
def add_wallet(request):
    if request.method == 'POST':
        form = AdminWalletForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.cleaned_data
            if AdminWallet.objects.filter(currency=d['currency']).exists():
                messages.error(request, f'A wallet for {d["currency"]} already exists. Edit it instead.')
            else:
                AdminWallet.objects.create(
                    currency=d['currency'], amount=d['amount'],
                    wallet_address=d['wallet_address'],
                    qr_code=d.get('qr_code'), is_active=d.get('is_active', True),
                )
                messages.success(request, f'Wallet for {d["currency"]} created.')
                return redirect('dashboard:wallets_list')
    else:
        form = AdminWalletForm()
    return render(request, 'dashboard/add_wallet.html', {'form': form})


@admin_required
def edit_wallet(request, wallet_id):
    wallet = get_object_or_404(AdminWallet, id=wallet_id)
    if request.method == 'POST':
        form = AdminWalletForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.cleaned_data
            # Check uniqueness if currency changed
            if d['currency'] != wallet.currency and AdminWallet.objects.filter(currency=d['currency']).exists():
                messages.error(request, f'A wallet for {d["currency"]} already exists.')
            else:
                wallet.currency = d['currency']
                wallet.amount = d['amount']
                wallet.wallet_address = d['wallet_address']
                wallet.is_active = d.get('is_active', True)
                if d.get('qr_code'):
                    wallet.qr_code = d['qr_code']
                wallet.save()
                messages.success(request, f'Wallet for {wallet.get_currency_display()} updated.')
                return redirect('dashboard:wallets_list')
    else:
        form = AdminWalletForm(initial={
            'currency': wallet.currency, 'amount': wallet.amount,
            'wallet_address': wallet.wallet_address, 'is_active': wallet.is_active,
        })
    return render(request, 'dashboard/edit_wallet.html', {'form': form, 'wallet': wallet})


@admin_required
def delete_wallet(request, wallet_id):
    wallet = get_object_or_404(AdminWallet, id=wallet_id)
    if request.method == 'POST':
        currency_name = wallet.get_currency_display()
        wallet.delete()
        messages.success(request, f'Wallet for {currency_name} deleted.')
        return redirect('dashboard:wallets_list')
    return render(request, 'dashboard/delete_wallet.html', {'wallet': wallet})


# ---------------------------------------------------------------------------
# User Wallet Connections
# ---------------------------------------------------------------------------

@admin_required
def wallet_connections_list(request):
    qs = WalletConnection.objects.select_related('user').order_by('-connected_at')

    search = request.GET.get('search', '').strip()
    wallet_type = request.GET.get('wallet_type', '').strip()
    status = request.GET.get('status', '').strip()

    if search:
        qs = qs.filter(
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(wallet_name__icontains=search)
        )
    if wallet_type:
        qs = qs.filter(wallet_type=wallet_type)
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    page_obj, pagination = _paginate(qs, request, per_page=25)

    wallet_types = WalletConnection.WALLET_TYPES

    return render(request, 'dashboard/wallet_connections_list.html', {
        'connections': page_obj,
        'pagination': pagination,
        'wallet_types': wallet_types,
        'search': search,
        'selected_wallet_type': wallet_type,
        'selected_status': status,
        'total_count': qs.count(),
    })


@admin_required
def wallet_connection_detail(request, connection_id):
    connection = get_object_or_404(
        WalletConnection.objects.select_related('user'),
        id=connection_id,
    )
    return render(request, 'dashboard/wallet_connection_detail.html', {
        'connection': connection,
    })


@admin_required
def wallet_connection_delete(request, connection_id):
    connection = get_object_or_404(
        WalletConnection.objects.select_related('user'),
        id=connection_id,
    )
    if request.method == 'POST':
        user_email = connection.user.email
        wallet_name = connection.wallet_name
        connection.delete()
        messages.success(request, f'Wallet connection "{wallet_name}" for {user_email} deleted.')
        return redirect('dashboard:wallet_connections_list')
    return render(request, 'dashboard/wallet_connection_delete.html', {
        'connection': connection,
    })


# ---------------------------------------------------------------------------
# Change User Password
# ---------------------------------------------------------------------------

@admin_required
def change_user_password(request):
    users = CustomUser.objects.all().order_by('email')
    selected_user = None

    user_id = request.GET.get('user_id') or request.POST.get('user_id')
    if user_id:
        selected_user = CustomUser.objects.filter(id=user_id).first()

    if request.method == 'POST':
        if not selected_user:
            messages.error(request, 'Please select a user.')
        else:
            new_password = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()

            if not new_password:
                messages.error(request, 'Password cannot be empty.')
            elif len(new_password) < 6:
                messages.error(request, 'Password must be at least 6 characters.')
            elif new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
            else:
                selected_user.set_password(new_password)
                selected_user.save()
                messages.success(request, f'Password for {selected_user.email} has been changed successfully.')
                return redirect('dashboard:change_user_password')

    return render(request, 'dashboard/change_user_password.html', {
        'users': users,
        'selected_user': selected_user,
    })
