from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import Trader, UserTraderCopy, UserCopyTraderHistory


@api_view(["GET"])
@permission_classes([AllowAny])
def list_traders(request):
    """List all active traders with optional search and category filter"""
    search = request.GET.get("search", "").strip()
    category = request.GET.get("category", "").strip().lower()

    traders = Trader.objects.filter(is_active=True)

    if search:
        traders = traders.filter(
            Q(name__icontains=search) | Q(username__icontains=search)
        )

    if category and category != "all":
        traders = traders.filter(category=category)

    traders_list = []
    for t in traders:
        avatar_url = None
        try:
            if t.avatar:
                avatar_url = t.avatar.url
        except Exception:
            pass

        traders_list.append({
            "id": t.id,
            "name": t.name,
            "username": t.username,
            "avatar_url": avatar_url,
            "badge": t.badge,
            "country": t.country,
            "gain": str(t.gain),
            "risk": t.risk,
            "trades": t.trades,
            "capital": t.capital,
            "copiers": t.copiers,
            "trend_direction": t.trend_direction,
            "category": t.category,
            "is_active": t.is_active,
        })

    return Response(traders_list)


@api_view(["GET"])
@permission_classes([AllowAny])
def trader_detail(request, trader_id):
    """Get detailed trader profile"""
    try:
        t = Trader.objects.get(id=trader_id)
    except Trader.DoesNotExist:
        return Response({"error": "Trader not found"}, status=status.HTTP_404_NOT_FOUND)

    avatar_url = None
    try:
        if t.avatar:
            avatar_url = t.avatar.url
    except Exception:
        pass

    # Get frequently traded assets from UserCopyTraderHistory (actual trade history)
    from django.db.models import Count
    frequently_traded_assets = (
        UserCopyTraderHistory.objects
        .filter(trader=t)
        .values('market')
        .annotate(count=Count('market'))
        .order_by('-count')[:10]  # Top 10 most traded assets
    )
    frequently_traded = [item['market'] for item in frequently_traded_assets]

    data = {
        "id": t.id,
        "name": t.name,
        "username": t.username,
        "avatar_url": avatar_url,
        "badge": t.badge,
        "country": t.country,
        "gain": str(t.gain),
        "risk": t.risk,
        "trades": t.trades,
        "capital": t.capital,
        "copiers": t.copiers,
        "avg_trade_time": t.avg_trade_time,
        "subscribers": t.subscribers,
        "current_positions": t.current_positions,
        "min_account_threshold": str(t.min_account_threshold),
        "expert_rating": str(t.expert_rating),
        "return_ytd": str(t.return_ytd),
        "return_2y": str(t.return_2y),
        "avg_score_7d": str(t.avg_score_7d),
        "profitable_weeks": str(t.profitable_weeks),
        "total_trades_12m": t.total_trades_12m,
        "avg_profit_percent": str(t.avg_profit_percent),
        "avg_loss_percent": str(t.avg_loss_percent),
        "total_wins": t.total_wins,
        "total_losses": t.total_losses,
        "win_rate": t.win_rate,
        "performance_data": t.performance_data,
        "monthly_performance": t.monthly_performance,
        "frequently_traded": frequently_traded,
        "bio": t.bio,
        "followers": t.followers,
        "trading_days": t.trading_days,
        "trend_direction": t.trend_direction,
        "tags": t.tags,
        "category": t.category,
        "max_drawdown": str(t.max_drawdown),
        "cumulative_earnings_copiers": str(t.cumulative_earnings_copiers),
        "cumulative_copiers": t.cumulative_copiers,
        "portfolio_breakdown": t.portfolio_breakdown,
        "top_traded": t.top_traded,
        "is_active": t.is_active,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }

    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def copy_trader_action(request):
    """Copy or cancel copying a trader"""
    import json
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, Exception):
        body = request.data

    trader_id = body.get("trader_id")
    action = body.get("action")

    if not trader_id or action not in ("copy", "cancel"):
        return Response(
            {"success": False, "error": "trader_id and action (copy/cancel) required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        trader = Trader.objects.get(id=trader_id)
    except Trader.DoesNotExist:
        return Response(
            {"success": False, "error": "Trader not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    user = request.user

    if action == "copy":
        from decimal import Decimal

        if user.balance < trader.min_account_threshold:
            return Response({
                "success": False,
                "error": f"Insufficient balance. You need at least ${trader.min_account_threshold} to copy {trader.name}. Your balance: ${user.balance}",
            }, status=status.HTTP_400_BAD_REQUEST)

        copy_record, created = UserTraderCopy.objects.get_or_create(
            user=user,
            trader=trader,
            defaults={
                "is_actively_copying": True,
                "initial_investment_amount": user.balance,
                "minimum_threshold_at_start": trader.min_account_threshold,
            },
        )

        if not created:
            if copy_record.is_actively_copying:
                return Response({
                    "success": False,
                    "error": f"You are already copying {trader.name}",
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                copy_record.is_actively_copying = True
                copy_record.initial_investment_amount = user.balance
                copy_record.minimum_threshold_at_start = trader.min_account_threshold
                copy_record.save()

        trader.copiers += 1
        trader.save()

        return Response({
            "success": True,
            "message": f"You are now copying {trader.name}",
        })

    elif action == "cancel":
        try:
            copy_record = UserTraderCopy.objects.get(
                user=user, trader=trader, is_actively_copying=True
            )
        except UserTraderCopy.DoesNotExist:
            return Response({
                "success": False,
                "error": f"You are not copying {trader.name}",
            }, status=status.HTTP_400_BAD_REQUEST)

        copy_record.is_actively_copying = False
        copy_record.save()

        if trader.copiers > 0:
            trader.copiers -= 1
            trader.save()

        return Response({
            "success": True,
            "message": f"You have stopped copying {trader.name}",
        })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def copy_trader_status(request, trader_id):
    """Check if user is copying a specific trader"""
    is_copying = UserTraderCopy.objects.filter(
        user=request.user,
        trader_id=trader_id,
        is_actively_copying=True,
    ).exists()

    return Response({"success": True, "is_copying": is_copying})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_copied_trades(request):
    """Get all trades from traders the user is copying"""
    copies = UserTraderCopy.objects.filter(
        user=request.user,
        is_actively_copying=True,
    ).select_related("trader")

    trades_list = []
    for copy in copies:
        trade_history = UserCopyTraderHistory.objects.filter(
            trader=copy.trader
        ).order_by("-opened_at")

        for trade in trade_history:
            user_pl = trade.calculate_user_profit_loss(copy.initial_investment_amount)
            trades_list.append({
                "id": trade.id,
                "market": trade.market,
                "market_name": trade.market_name,
                "market_logo_url": trade.market_logo_url,
                "direction": trade.direction,
                "duration": trade.duration,
                "amount": str(trade.amount),
                "entry_price": str(trade.entry_price),
                "exit_price": str(trade.exit_price) if trade.exit_price else None,
                "profit_loss_percent": str(trade.profit_loss_percent),
                "user_profit_loss": str(user_pl),
                "status": trade.status,
                "status_display": trade.get_status_display(),
                "direction_display": trade.get_direction_display(),
                "time_ago": trade.time_ago,
                "is_profit": trade.is_profit,
                "opened_at": trade.opened_at.isoformat() if trade.opened_at else None,
                "closed_at": trade.closed_at.isoformat() if trade.closed_at else None,
                "reference": trade.reference,
                "trader_name": copy.trader.name,
                "trader_id": copy.trader.id,
            })

    # Sort all trades by opened_at descending
    trades_list.sort(key=lambda x: x["opened_at"] or "", reverse=True)

    return Response({"success": True, "trades": trades_list})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_following_traders(request):
    """Get all traders the user is currently copying"""
    copies = UserTraderCopy.objects.filter(
        user=request.user,
        is_actively_copying=True,
    ).select_related("trader")

    traders_list = []
    for copy in copies:
        t = copy.trader
        avatar_url = None
        try:
            if t.avatar:
                avatar_url = t.avatar.url
        except Exception:
            pass

        traders_list.append({
            "id": copy.id,  # UserTraderCopy ID
            "trader_id": t.id,  # Trader ID for navigation
            "trader_name": t.name,
            "trader_username": t.username,
            "trader_avatar_url": avatar_url,
            "initial_investment": str(copy.initial_investment_amount),
            "started_copying_at": copy.started_copying_at.isoformat() if copy.started_copying_at else None,
        })

    return Response({"success": True, "traders": traders_list})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_trade_history(request):
    """
    Get comprehensive trade history for user - all trades from all traders they are/were copying.
    Supports filtering by status, trader, and pagination.
    """
    # Get filter parameters
    status_filter = request.GET.get("status", "").strip()  # open, closed, or empty for all
    trader_id = request.GET.get("trader_id", "").strip()
    limit = request.GET.get("limit", "50")
    offset = request.GET.get("offset", "0")

    try:
        limit = int(limit)
        offset = int(offset)
    except ValueError:
        limit = 50
        offset = 0

    # Get all traders the user is or was copying
    copies = UserTraderCopy.objects.filter(
        user=request.user,
    ).select_related("trader")

    # Build queryset for trades
    trader_ids = [copy.trader.id for copy in copies]
    trades_query = UserCopyTraderHistory.objects.filter(
        trader_id__in=trader_ids
    ).select_related("trader")

    # Apply filters
    if status_filter:
        trades_query = trades_query.filter(status=status_filter)

    if trader_id:
        try:
            trader_id_int = int(trader_id)
            trades_query = trades_query.filter(trader_id=trader_id_int)
        except ValueError:
            pass

    # Order by most recent first
    trades_query = trades_query.order_by("-opened_at")

    # Get total count before pagination
    total_count = trades_query.count()

    # Apply pagination
    trades = trades_query[offset:offset + limit]

    # Build response
    trades_list = []
    for trade in trades:
        # Find the user's copy record for this trader to get investment amount
        user_investment = None
        for copy in copies:
            if copy.trader.id == trade.trader.id:
                user_investment = copy.initial_investment_amount
                break

        user_pl = trade.calculate_user_profit_loss(user_investment) if user_investment else 0

        trader_avatar_url = None
        try:
            if trade.trader.avatar:
                trader_avatar_url = trade.trader.avatar.url
        except Exception:
            pass

        trades_list.append({
            "id": trade.id,
            "trader_id": trade.trader.id,
            "trader_name": trade.trader.name,
            "trader_username": trade.trader.username,
            "trader_avatar_url": trader_avatar_url,
            "market": trade.market,
            "market_name": trade.market_name,
            "market_logo_url": trade.market_logo_url,
            "direction": trade.direction,
            "direction_display": trade.get_direction_display(),
            "duration": trade.duration,
            "amount": str(trade.amount),
            "entry_price": str(trade.entry_price),
            "exit_price": str(trade.exit_price) if trade.exit_price else None,
            "profit_loss_percent": str(trade.profit_loss_percent),
            "user_profit_loss": str(user_pl),
            "status": trade.status,
            "status_display": trade.get_status_display(),
            "time_ago": trade.time_ago,
            "is_profit": trade.is_profit,
            "opened_at": trade.opened_at.isoformat() if trade.opened_at else None,
            "closed_at": trade.closed_at.isoformat() if trade.closed_at else None,
            "reference": trade.reference,
        })

    return Response({
        "success": True,
        "trades": trades_list,
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
    })
