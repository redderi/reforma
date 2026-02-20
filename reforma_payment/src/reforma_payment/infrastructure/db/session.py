import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from reforma_payment.infrastructure.config.db_config import (
    DATABASE_URL,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
)
from reforma_common.logger import log_info, log_error
from reforma_payment.infrastructure.config.stripe_config import (
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
)
from sqlalchemy.orm import sessionmaker
from reforma_payment.infrastructure.db.base import Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


def create_database():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (DB_NAME,))
        exists = cur.fetchone()

        if not exists:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
            log_info(
                "Database created successfully",
                service="payment-service",
                context={"database_name": DB_NAME, "host": DB_HOST, "port": DB_PORT},
            )
        else:
            log_info(
                "Database already exists",
                service="payment-service",
                context={"database_name": DB_NAME},
            )

        cur.close()
        conn.close()

    except Exception as e:
        log_error(
            "Failed to create or check database",
            service="payment-service",
            context={
                "database_name": DB_NAME,
                "host": DB_HOST,
                "port": DB_PORT,
                "error_detail": str(e),
            },
        )
        raise


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_models():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        log_info(
            "Database tables created or verified",
            service="payment-service",
            context={"engine_url": DATABASE_URL},
        )

        async with SessionLocal() as session:
            from reforma_payment.infrastructure.repositories.payment_provider_repository_impl import (
                PaymentProviderRepositoryImpl,
            )
            from reforma_payment.domain.entities.payment_provider import PaymentProvider

            repo = PaymentProviderRepositoryImpl(session)
            stripe_provider = await repo.get_active_by_type("stripe")

            if not stripe_provider:
                provider = PaymentProvider(
                    name="Stripe",
                    provider_type="stripe",
                    credentials={
                        "secret_key": STRIPE_SECRET_KEY,
                        "webhook_secret": STRIPE_WEBHOOK_SECRET,
                    },
                    is_active=True,
                )
                await repo.add(provider)

                log_info(
                    "Initial Stripe payment provider created",
                    service="payment-service",
                    context={
                        "provider_id": str(provider.id),
                        "provider_type": provider.provider_type,
                    },
                )
            else:
                log_info(
                    "Stripe payment provider already exists",
                    service="payment-service",
                    context={
                        "provider_id": str(stripe_provider.id),
                        "provider_type": stripe_provider.provider_type,
                    },
                )

    except Exception as e:
        log_error(
            "Unexpected error during database initialization",
            service="payment-service",
            context={"error_detail": str(e)},
        )
        raise
