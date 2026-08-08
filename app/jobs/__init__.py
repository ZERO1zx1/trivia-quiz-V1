"""Scheduled Jobs Registration

Central place to register all background jobs with APScheduler so the
factory only starts ONE scheduler and every job has one canonical
registration point (FIX-014).
"""
from app.jobs.premium_jobs import check_expired_premium
from app.jobs.streak_jobs import check_streak_protection
from app.economy.marketplace.service import expire_listings_job
from app.economy.auction.service import settle_auctions_job


def register_jobs(scheduler, app):
    """Register all periodic jobs.

    Jobs that take the app as an argument are wrapped in an app_context
    lambda only where needed; the service layer handles its own contexts
    so tests can call the service functions directly without an app.
    """
    scheduler.add_job(
        func=lambda: check_expired_premium(app),
        trigger='interval',
        hours=1,
        id='check_expired_premium',
        name='Check expired premium memberships',
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        func=lambda: check_streak_protection(app),
        trigger='interval',
        hours=4,
        id='check_streak_protection',
        name='Streak protection alerts',
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        func=lambda: expire_listings_job(app),
        trigger='interval',
        minutes=15,
        id='expire_marketplace_listings',
        name='Expire marketplace listings',
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        func=lambda: settle_auctions_job(app),
        trigger='interval',
        minutes=5,
        id='settle_auctions',
        name='Settle ended auctions',
        replace_existing=True,
        max_instances=1,
    )
