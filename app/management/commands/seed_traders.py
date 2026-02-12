from django.core.management.base import BaseCommand
from app.models import Trader
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed 5 professional traders for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing traders before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted_count = Trader.objects.all().delete()[0]
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted_count} existing traders')
            )

        traders_data = [
            {
                "name": "Kristijan Novak",
                "username": "@kristijan",
                "country": "Germany",
                "badge": "gold",
                "gain": Decimal("126799.00"),
                "risk": 4,
                "capital": "250000",
                "copiers": 287,
                "avg_trade_time": "2 weeks",
                "trades": 1326,
                "subscribers": 194,
                "current_positions": 8,
                "min_account_threshold": Decimal("50000.00"),
                "expert_rating": Decimal("4.90"),
                "return_ytd": Decimal("2187.00"),
                "return_2y": Decimal("8450.00"),
                "avg_score_7d": Decimal("9.30"),
                "profitable_weeks": Decimal("92.00"),
                "total_trades_12m": 485,
                "avg_profit_percent": Decimal("86.00"),
                "avg_loss_percent": Decimal("8.00"),
                "total_wins": 1166,
                "total_losses": 160,
                "performance_data": [
                    {"month": "Jan", "value": 12.5},
                    {"month": "Feb", "value": 8.3},
                    {"month": "Mar", "value": 15.1},
                    {"month": "Apr", "value": -2.4},
                    {"month": "May", "value": 18.7},
                    {"month": "Jun", "value": 9.8},
                ],
                "frequently_traded": ["BTC/USD", "ETH/USD", "AAPL", "TSLA"],
                "is_active": True,
            },
            {
                "name": "Sarah Chen",
                "username": "@sarachen",
                "country": "Singapore",
                "badge": "gold",
                "gain": Decimal("84320.50"),
                "risk": 3,
                "capital": "500000",
                "copiers": 215,
                "avg_trade_time": "1 week",
                "trades": 982,
                "subscribers": 158,
                "current_positions": 5,
                "min_account_threshold": Decimal("25000.00"),
                "expert_rating": Decimal("4.80"),
                "return_ytd": Decimal("1540.00"),
                "return_2y": Decimal("5320.00"),
                "avg_score_7d": Decimal("9.10"),
                "profitable_weeks": Decimal("88.50"),
                "total_trades_12m": 362,
                "avg_profit_percent": Decimal("72.00"),
                "avg_loss_percent": Decimal("12.00"),
                "total_wins": 810,
                "total_losses": 172,
                "performance_data": [
                    {"month": "Jan", "value": 9.2},
                    {"month": "Feb", "value": 14.6},
                    {"month": "Mar", "value": 7.8},
                    {"month": "Apr", "value": 11.3},
                    {"month": "May", "value": -1.5},
                    {"month": "Jun", "value": 16.4},
                ],
                "frequently_traded": ["GOOGL", "AMZN", "SOL/USD", "NVDA"],
                "is_active": True,
            },
            {
                "name": "Marcus Williams",
                "username": "@marcusw",
                "country": "United States",
                "badge": "silver",
                "gain": Decimal("45210.75"),
                "risk": 6,
                "capital": "100000",
                "copiers": 143,
                "avg_trade_time": "3 days",
                "trades": 2150,
                "subscribers": 89,
                "current_positions": 12,
                "min_account_threshold": Decimal("10000.00"),
                "expert_rating": Decimal("4.60"),
                "return_ytd": Decimal("890.00"),
                "return_2y": Decimal("3120.00"),
                "avg_score_7d": Decimal("8.50"),
                "profitable_weeks": Decimal("78.00"),
                "total_trades_12m": 720,
                "avg_profit_percent": Decimal("55.00"),
                "avg_loss_percent": Decimal("15.00"),
                "total_wins": 1580,
                "total_losses": 570,
                "performance_data": [
                    {"month": "Jan", "value": 5.4},
                    {"month": "Feb", "value": -3.2},
                    {"month": "Mar", "value": 22.1},
                    {"month": "Apr", "value": 8.9},
                    {"month": "May", "value": 12.6},
                    {"month": "Jun", "value": -1.8},
                ],
                "frequently_traded": ["EUR/USD", "GBP/USD", "XAU/USD", "BTC/USD"],
                "is_active": True,
            },
            {
                "name": "Elena Petrova",
                "username": "@elenap",
                "country": "Switzerland",
                "badge": "gold",
                "gain": Decimal("97450.30"),
                "risk": 2,
                "capital": "1000000",
                "copiers": 312,
                "avg_trade_time": "1 month",
                "trades": 654,
                "subscribers": 245,
                "current_positions": 3,
                "min_account_threshold": Decimal("75000.00"),
                "expert_rating": Decimal("5.00"),
                "return_ytd": Decimal("1820.00"),
                "return_2y": Decimal("6780.00"),
                "avg_score_7d": Decimal("9.70"),
                "profitable_weeks": Decimal("95.00"),
                "total_trades_12m": 198,
                "avg_profit_percent": Decimal("90.00"),
                "avg_loss_percent": Decimal("5.00"),
                "total_wins": 612,
                "total_losses": 42,
                "performance_data": [
                    {"month": "Jan", "value": 18.2},
                    {"month": "Feb", "value": 12.4},
                    {"month": "Mar", "value": 9.7},
                    {"month": "Apr", "value": 14.1},
                    {"month": "May", "value": 8.9},
                    {"month": "Jun", "value": 20.3},
                ],
                "frequently_traded": ["AAPL", "MSFT", "NVDA", "META"],
                "is_active": True,
            },
            {
                "name": "Takeshi Yamamoto",
                "username": "@takeshi",
                "country": "Japan",
                "badge": "silver",
                "gain": Decimal("32180.60"),
                "risk": 7,
                "capital": "75000",
                "copiers": 98,
                "avg_trade_time": "1 day",
                "trades": 3420,
                "subscribers": 67,
                "current_positions": 15,
                "min_account_threshold": Decimal("5000.00"),
                "expert_rating": Decimal("4.50"),
                "return_ytd": Decimal("620.00"),
                "return_2y": Decimal("2450.00"),
                "avg_score_7d": Decimal("7.80"),
                "profitable_weeks": Decimal("72.00"),
                "total_trades_12m": 1280,
                "avg_profit_percent": Decimal("48.00"),
                "avg_loss_percent": Decimal("20.00"),
                "total_wins": 2394,
                "total_losses": 1026,
                "performance_data": [
                    {"month": "Jan", "value": -4.1},
                    {"month": "Feb", "value": 28.5},
                    {"month": "Mar", "value": 6.3},
                    {"month": "Apr", "value": -7.2},
                    {"month": "May", "value": 35.8},
                    {"month": "Jun", "value": 11.4},
                ],
                "frequently_traded": ["BTC/USD", "ETH/USD", "SOL/USD", "DOGE/USD"],
                "is_active": True,
            },
        ]

        created_count = 0
        updated_count = 0

        for trader_data in traders_data:
            trader, created = Trader.objects.update_or_create(
                username=trader_data["username"],
                defaults=trader_data
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created trader: {trader.name} ({trader.username})')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'⟳ Updated trader: {trader.name} ({trader.username})')
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(f'Traders created: {created_count}'))
        self.stdout.write(self.style.WARNING(f'Traders updated: {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total traders in database: {Trader.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
