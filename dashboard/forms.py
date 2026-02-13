from django import forms
from app.models import CustomUser, Stock, Transaction, Trader, UserCopyTraderHistory, AdminWallet
from decimal import Decimal

# ---------------------------------------------------------------------------
# Shared Tailwind widget classes
# ---------------------------------------------------------------------------
_input = 'w-full px-4 py-2.5 bg-gray-50 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition'
_select = _input
_textarea = _input
_checkbox = 'w-4 h-4 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500'
_file = 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'


# ===== Trade Forms =====

class AddTradeForm(forms.Form):
    user_email = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active=True).order_by('email'),
        label="Select User",
        widget=forms.Select(attrs={'class': _select}),
        to_field_name='email',
    )
    entry = forms.DecimalField(
        label="Entry Amount", max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '5255'}),
    )

    ASSET_TYPE_CHOICES = [('', 'Select Type'), ('stock', 'Stock'), ('crypto', 'Crypto'), ('forex', 'Forex')]
    asset_type = forms.ChoiceField(choices=ASSET_TYPE_CHOICES, label="Type", widget=forms.Select(attrs={'class': _select}))

    asset = forms.CharField(
        label="Asset",
        widget=forms.TextInput(attrs={'class': _input, 'placeholder': 'Select type first'}),
    )

    DIRECTION_CHOICES = [('', 'Select Direction'), ('buy', 'Buy'), ('sell', 'Sell'), ('futures', 'Futures')]
    direction = forms.ChoiceField(choices=DIRECTION_CHOICES, label="Direction", widget=forms.Select(attrs={'class': _select}))

    profit = forms.DecimalField(
        label="Profit / Loss", max_digits=12, decimal_places=2, required=False,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '0.00'}),
    )

    DURATION_CHOICES = [
        ('', 'Select Duration'),
        ('2 minutes', '2 minutes'), ('5 minutes', '5 minutes'), ('30 minutes', '30 minutes'),
        ('1 hour', '1 hour'), ('8 hours', '8 hours'), ('10 hours', '10 hours'), ('20 hours', '20 hours'),
        ('1 day', '1 day'), ('2 days', '2 days'), ('3 days', '3 days'),
        ('4 days', '4 days'), ('5 days', '5 days'), ('6 days', '6 days'),
        ('1 week', '1 week'), ('2 weeks', '2 weeks'),
    ]
    duration = forms.ChoiceField(choices=DURATION_CHOICES, label="Duration", widget=forms.Select(attrs={'class': _select}))

    rate = forms.DecimalField(
        label="Rate (Optional)", max_digits=12, decimal_places=2, required=False,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '251'}),
    )


class AddEarningsForm(forms.Form):
    user_email = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active=True).order_by('email'),
        label="Select User",
        widget=forms.Select(attrs={'class': _select}),
        to_field_name='email',
    )
    amount = forms.DecimalField(
        label="Earnings Amount", max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '100.00'}),
    )
    description = forms.CharField(
        label="Description", required=False,
        widget=forms.TextInput(attrs={'class': _input, 'placeholder': 'Bonus, Referral, Trade Profit, etc.'}),
    )


# ===== Approval Forms =====

class ApproveDepositForm(forms.Form):
    STATUS_CHOICES = [('completed', 'Approve'), ('failed', 'Reject')]
    status = forms.ChoiceField(choices=STATUS_CHOICES, label="Action", widget=forms.Select(attrs={'class': _select}))
    admin_notes = forms.CharField(
        label="Admin Notes (Optional)", required=False,
        widget=forms.Textarea(attrs={'class': _textarea, 'rows': 3, 'placeholder': 'Internal notes…'}),
    )


class ApproveWithdrawalForm(forms.Form):
    STATUS_CHOICES = [('completed', 'Approve'), ('failed', 'Reject')]
    status = forms.ChoiceField(choices=STATUS_CHOICES, label="Action", widget=forms.Select(attrs={'class': _select}))
    admin_notes = forms.CharField(
        label="Admin Notes (Optional)", required=False,
        widget=forms.Textarea(attrs={'class': _textarea, 'rows': 3, 'placeholder': 'Internal notes…'}),
    )


class ApproveKYCForm(forms.Form):
    ACTION_CHOICES = [('approve', 'Approve KYC'), ('reject', 'Reject KYC')]
    action = forms.ChoiceField(choices=ACTION_CHOICES, label="Action", widget=forms.Select(attrs={'class': _select}))
    admin_notes = forms.CharField(
        label="Admin Notes (Optional)", required=False,
        widget=forms.Textarea(attrs={'class': _textarea, 'rows': 3, 'placeholder': 'Reason for rejection…'}),
    )


# ===== Deposit Edit Form =====

class EditDepositForm(forms.Form):
    amount = forms.DecimalField(
        label="Deposit Amount", max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '1000.00', 'step': '0.01'}),
    )

    CURRENCY_CHOICES = [
        ('BTC', 'Bitcoin (BTC)'), ('ETH', 'Ethereum (ETH)'), ('SOL', 'Solana (SOL)'),
        ('USDT ERC20', 'USDT (ERC20)'), ('USDT TRC20', 'USDT (TRC20)'),
        ('BNB', 'Binance Coin (BNB)'), ('TRX', 'Tron (TRX)'), ('USDC', 'USDC (BASE)'),
    ]
    currency = forms.ChoiceField(choices=CURRENCY_CHOICES, label="Currency", widget=forms.Select(attrs={'class': _select}))

    unit = forms.DecimalField(
        label="Crypto Unit Amount", max_digits=12, decimal_places=8,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '0.01234567', 'step': '0.00000001'}),
    )

    STATUS_CHOICES = [('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled')]
    status = forms.ChoiceField(choices=STATUS_CHOICES, label="Status", widget=forms.Select(attrs={'class': _select}))

    description = forms.CharField(
        label="Description", required=False,
        widget=forms.Textarea(attrs={'class': _textarea, 'rows': 3, 'placeholder': 'Deposit description…'}),
    )
    reference = forms.CharField(
        label="Reference Number", max_length=100,
        widget=forms.TextInput(attrs={'class': _input, 'placeholder': 'DEP-XXXXXXXXXX'}),
    )
    receipt = forms.ImageField(
        label="Update Receipt (Optional)", required=False,
        widget=forms.FileInput(attrs={'class': _file, 'accept': 'image/*'}),
    )


# ===== Copy Trade Form =====

class AddCopyTradeForm(forms.Form):
    trader = forms.ModelChoiceField(
        queryset=Trader.objects.filter(is_active=True).order_by('name'),
        label="Select Trader",
        widget=forms.Select(attrs={'class': _select}),
        empty_label="Select Trader",
    )
    market = forms.ChoiceField(
        choices=[('', 'Select Market')] + list(UserCopyTraderHistory.MARKET_CHOICES),
        label="Market / Asset", widget=forms.Select(attrs={'class': _select}),
    )
    direction = forms.ChoiceField(
        choices=[('', 'Select Direction')] + list(UserCopyTraderHistory.DIRECTION_CHOICES),
        label="Trade Direction", widget=forms.Select(attrs={'class': _select}),
    )

    DURATION_CHOICES = [
        ('', 'Select Duration'),
        ('2 minutes', '2 Minutes'), ('5 minutes', '5 Minutes'), ('10 minutes', '10 Minutes'),
        ('15 minutes', '15 Minutes'), ('30 minutes', '30 Minutes'),
        ('1 hour', '1 Hour'), ('2 hours', '2 Hours'), ('4 hours', '4 Hours'), ('12 hours', '12 Hours'),
        ('1 day', '1 Day'), ('2 days', '2 Days'),
        ('1 week', '1 Week'), ('2 weeks', '2 Weeks'), ('1 month', '1 Month'),
    ]
    duration = forms.ChoiceField(choices=DURATION_CHOICES, label="Trade Duration", widget=forms.Select(attrs={'class': _select}))

    amount = forms.DecimalField(
        label="Investment Amount", max_digits=20, decimal_places=8,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '1000.00', 'step': '0.00000001'}),
    )
    entry_price = forms.DecimalField(
        label="Entry Price", max_digits=20, decimal_places=8,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '50000.00', 'step': '0.00000001'}),
    )
    exit_price = forms.DecimalField(
        label="Exit Price (Optional)", max_digits=20, decimal_places=8, required=False,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '51000.00', 'step': '0.00000001'}),
    )
    profit_loss_percent = forms.DecimalField(
        label="Profit / Loss %", max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '15.50', 'step': '0.01'}),
        help_text="Positive for profit, negative for loss",
    )
    status = forms.ChoiceField(
        choices=[('', 'Select Status')] + list(UserCopyTraderHistory.STATUS_CHOICES),
        label="Trade Status", widget=forms.Select(attrs={'class': _select}),
    )
    closed_at = forms.DateTimeField(
        label="Close Date & Time (Optional)", required=False,
        widget=forms.DateTimeInput(attrs={'class': _input, 'type': 'datetime-local'}),
    )
    notes = forms.CharField(
        label="Notes (Optional)", required=False,
        widget=forms.Textarea(attrs={'class': _textarea, 'rows': 3, 'placeholder': 'Additional notes…'}),
    )


# ===== Trader Forms =====

class AddTraderForm(forms.Form):
    # --- Basic Info ---
    name = forms.CharField(label="Trader Name", max_length=150, widget=forms.TextInput(attrs={'class': _input, 'placeholder': 'Kristijan'}))
    username = forms.CharField(label="Username", max_length=100, widget=forms.TextInput(attrs={'class': _input, 'placeholder': '@kristijan'}), help_text="Must be unique")
    avatar = forms.ImageField(label="Avatar", required=False, widget=forms.FileInput(attrs={'class': _file, 'accept': 'image/*'}))

    COUNTRY_CHOICES = [
        ('', 'Select Country'),
        ('United States', 'United States'), ('United Kingdom', 'United Kingdom'),
        ('Germany', 'Germany'), ('France', 'France'), ('Canada', 'Canada'),
        ('Australia', 'Australia'), ('Singapore', 'Singapore'), ('Hong Kong', 'Hong Kong'),
        ('Japan', 'Japan'), ('South Korea', 'South Korea'), ('India', 'India'),
        ('Brazil', 'Brazil'), ('Mexico', 'Mexico'), ('Netherlands', 'Netherlands'),
        ('Switzerland', 'Switzerland'), ('Sweden', 'Sweden'), ('Norway', 'Norway'),
        ('Denmark', 'Denmark'), ('Spain', 'Spain'), ('Italy', 'Italy'), ('Other', 'Other'),
    ]
    country = forms.ChoiceField(choices=COUNTRY_CHOICES, label="Country", widget=forms.Select(attrs={'class': _select}))

    badge = forms.ChoiceField(
        choices=[('', 'Select Badge'), ('bronze', 'Bronze'), ('silver', 'Silver'), ('gold', 'Gold')],
        label="Badge Level", widget=forms.Select(attrs={'class': _select}),
    )

    # --- Capital & Gain ---
    CAPITAL_CHOICES = [
        ('', 'Select Starting Capital'),
        ('1000', '$1,000'), ('5000', '$5,000'), ('10000', '$10,000'), ('25000', '$25,000'),
        ('50000', '$50,000'), ('75000', '$75,000'), ('100000', '$100,000'),
        ('250000', '$250,000'), ('500000', '$500,000'), ('1000000', '$1,000,000'),
    ]
    capital_dropdown = forms.ChoiceField(choices=CAPITAL_CHOICES, label="Starting Capital (Dropdown)", required=False, widget=forms.Select(attrs={'class': _select}))
    capital = forms.CharField(label="OR Custom Amount", max_length=50, required=False, widget=forms.TextInput(attrs={'class': _input, 'placeholder': '50000'}))

    GAIN_CHOICES = [
        ('', 'Select Total Gain %'),
        ('50', '50%'), ('100', '100%'), ('500', '500%'), ('1000', '1,000%'),
        ('5000', '5,000%'), ('10000', '10,000%'), ('50000', '50,000%'),
        ('100000', '100,000%'), ('126799', '126,799%'),
    ]
    gain_dropdown = forms.ChoiceField(choices=GAIN_CHOICES, label="Total Gain % (Dropdown)", required=False, widget=forms.Select(attrs={'class': _select}))
    gain = forms.DecimalField(label="OR Exact Gain %", max_digits=10, decimal_places=2, required=False, widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '126799.00', 'step': '0.01'}))

    # --- Risk & Time ---
    RISK_CHOICES = [(i, str(i)) for i in range(1, 11)]
    risk = forms.ChoiceField(choices=[('', 'Select Risk Level')] + RISK_CHOICES, label="Risk Level (1-10)", widget=forms.Select(attrs={'class': _select}))

    AVG_TRADE_TIME_CHOICES = [
        ('', 'Select Avg Trade Time'),
        ('1 day', '1 Day'), ('3 days', '3 Days'), ('1 week', '1 Week'), ('2 weeks', '2 Weeks'),
        ('3 weeks', '3 Weeks'), ('1 month', '1 Month'), ('2 months', '2 Months'),
        ('3 months', '3 Months'), ('6 months', '6 Months'),
    ]
    avg_trade_time = forms.ChoiceField(choices=AVG_TRADE_TIME_CHOICES, label="Avg Trade Time", widget=forms.Select(attrs={'class': _select}))

    # --- Copiers & Trades ---
    COPIERS_CHOICES = [
        ('', 'Select Copiers Range'),
        ('1-10', '1-10'), ('11-20', '11-20'), ('21-30', '21-30'), ('31-50', '31-50'),
        ('51-100', '51-100'), ('101-200', '101-200'), ('201-300', '201-300'), ('300+', '300+'),
    ]
    copiers_range = forms.ChoiceField(choices=COPIERS_CHOICES, label="Copiers Range", widget=forms.Select(attrs={'class': _select}))
    copiers = forms.IntegerField(label="Exact Copiers (Optional)", required=False, widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '40', 'min': '0'}))

    TRADES_CHOICES = [
        ('', 'Select Trades Range'),
        ('1-50', '1-50'), ('51-100', '51-100'), ('101-200', '101-200'),
        ('201-300', '201-300'), ('301-500', '301-500'), ('500+', '500+'),
    ]
    trades_range = forms.ChoiceField(choices=TRADES_CHOICES, label="Trades Range", widget=forms.Select(attrs={'class': _select}))
    trades = forms.IntegerField(label="Exact Trades (Optional)", required=False, widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '251', 'min': '0'}))

    # --- Performance ---
    AVG_PROFIT_CHOICES = [('', 'Select'), ('10', '10%'), ('20', '20%'), ('30', '30%'), ('40', '40%'), ('50', '50%'), ('60', '60%'), ('70', '70%'), ('80', '80%'), ('86', '86%'), ('90', '90%'), ('95', '95%')]
    avg_profit_dropdown = forms.ChoiceField(choices=AVG_PROFIT_CHOICES, label="Avg Profit % (Dropdown)", required=False, widget=forms.Select(attrs={'class': _select}))
    avg_profit_percent = forms.DecimalField(label="OR Exact %", max_digits=10, decimal_places=2, required=False, widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '86.00', 'step': '0.01'}))

    AVG_LOSS_CHOICES = [('', 'Select'), ('5', '5%'), ('8', '8%'), ('10', '10%'), ('12', '12%'), ('15', '15%'), ('20', '20%'), ('25', '25%'), ('30', '30%')]
    avg_loss_dropdown = forms.ChoiceField(choices=AVG_LOSS_CHOICES, label="Avg Loss % (Dropdown)", required=False, widget=forms.Select(attrs={'class': _select}))
    avg_loss_percent = forms.DecimalField(label="OR Exact %", max_digits=10, decimal_places=2, required=False, widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '8.00', 'step': '0.01'}))

    WINS_CHOICES = [('', 'Select'), ('50', '50'), ('100', '100'), ('250', '250'), ('500', '500'), ('1000', '1,000'), ('1166', '1,166'), ('1500', '1,500'), ('2000', '2,000')]
    total_wins_dropdown = forms.ChoiceField(choices=WINS_CHOICES, label="Total Wins (Dropdown)", required=False, widget=forms.Select(attrs={'class': _select}))
    total_wins = forms.IntegerField(label="OR Exact", required=False, widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '1166', 'min': '0'}))

    LOSSES_CHOICES = [('', 'Select'), ('10', '10'), ('50', '50'), ('100', '100'), ('160', '160'), ('200', '200'), ('300', '300'), ('500', '500')]
    total_losses_dropdown = forms.ChoiceField(choices=LOSSES_CHOICES, label="Total Losses (Dropdown)", required=False, widget=forms.Select(attrs={'class': _select}))
    total_losses = forms.IntegerField(label="OR Exact", required=False, widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '160', 'min': '0'}))

    # --- Optional Stats ---
    SUBSCRIBERS_CHOICES = [('', 'Select'), ('0', '0'), ('1-10', '1-10'), ('11-25', '11-25'), ('26-50', '26-50'), ('51-100', '51-100'), ('101-200', '101-200'), ('200+', '200+')]
    subscribers_range = forms.ChoiceField(choices=SUBSCRIBERS_CHOICES, label="Subscribers Range", required=False, widget=forms.Select(attrs={'class': _select}))
    subscribers = forms.IntegerField(label="Exact Subscribers", required=False, initial=0, widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '49', 'min': '0'}))

    POSITIONS_CHOICES = [('', 'Select'), ('0', 'None'), ('1-5', '1-5'), ('6-10', '6-10'), ('11-20', '11-20'), ('20+', '20+')]
    current_positions_range = forms.ChoiceField(choices=POSITIONS_CHOICES, label="Current Positions", required=False, widget=forms.Select(attrs={'class': _select}))
    current_positions = forms.IntegerField(label="Exact Positions", required=False, initial=0, widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '3', 'min': '0'}))

    EXPERT_RATING_CHOICES = [('', 'Select'), ('5.00', '5.00'), ('4.90', '4.90'), ('4.80', '4.80'), ('4.70', '4.70'), ('4.60', '4.60'), ('4.50', '4.50'), ('4.00', '4.00'), ('3.50', '3.50'), ('3.00', '3.00')]
    expert_rating = forms.ChoiceField(choices=EXPERT_RATING_CHOICES, label="Expert Rating", required=False, widget=forms.Select(attrs={'class': _select}))

    return_ytd = forms.DecimalField(label="Return YTD %", max_digits=10, decimal_places=2, required=False, initial=0.00, widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '2187.00', 'step': '0.01'}))
    avg_score_7d = forms.DecimalField(label="Avg Score (7d)", max_digits=10, decimal_places=2, required=False, initial=0.00, widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '9.30', 'step': '0.01'}))
    profitable_weeks = forms.DecimalField(label="Profitable Weeks %", max_digits=5, decimal_places=2, required=False, initial=0.00, widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '92.00', 'step': '0.01'}))
    min_account_threshold = forms.DecimalField(label="Min Account Balance", max_digits=12, decimal_places=2, required=False, initial=0.00, widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '50000.00', 'step': '0.01'}))
    is_active = forms.BooleanField(label="Active (Available for Copying)", required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': _checkbox}))


class EditCopyTradeForm(AddCopyTradeForm):
    """Same fields as AddCopyTradeForm but used for editing existing copy trades."""
    pass


class EditTraderForm(AddTraderForm):
    pass


# ===== Admin Wallet Form =====

class AdminWalletForm(forms.Form):
    currency = forms.ChoiceField(
        choices=[('', 'Select Currency')] + list(AdminWallet.CURRENCY_CHOICES),
        label="Currency", widget=forms.Select(attrs={'class': _select}),
    )
    amount = forms.DecimalField(
        label="Rate (USD per unit)", max_digits=20, decimal_places=6,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '97250.00', 'step': '0.000001'}),
    )
    wallet_address = forms.CharField(
        label="Wallet Address", max_length=255,
        widget=forms.TextInput(attrs={'class': _input, 'placeholder': 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh'}),
    )
    qr_code = forms.ImageField(
        label="QR Code (Optional)", required=False,
        widget=forms.FileInput(attrs={'class': _file, 'accept': 'image/*'}),
    )
    is_active = forms.BooleanField(
        label="Active (Visible to Users)", required=False, initial=True,
        widget=forms.CheckboxInput(attrs={'class': _checkbox}),
    )
