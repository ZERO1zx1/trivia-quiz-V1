-- TriviaVerse migration 0001: economy integrity columns & constraints
-- FIX-005..FIX-010 / FIX-022
-- Safe to run repeatedly: each statement is wrapped in an idempotent helper.
-- Run against PostgreSQL with:
--   psql "$DATABASE_URL" -f migrations/0001_economy_integrity.sql
-- or via the app (development convenience):
--   RUN_DB_MIGRATIONS=1 flask run

-- ---------- 0001: unique auction bidder constraint ----------
-- Prevents the same user from holding more than one unredeemed bid per auction
-- (exactly-once escrow refund semantics rely on auction_id+bidder_id being unique).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_auction_bidder'
    ) THEN
        ALTER TABLE auction_bids
            ADD CONSTRAINT uq_auction_bidder UNIQUE (auction_id, bidder_id);
    END IF;
END $$;

-- ---------- 0002: marketplace transactions ledger columns ----------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'marketplace_transactions' AND column_name = 'net_seller_amount'
    ) THEN
        ALTER TABLE marketplace_transactions ADD COLUMN net_seller_amount INTEGER NOT NULL DEFAULT 0;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'marketplace_transactions' AND column_name = 'tax'
    ) THEN
        ALTER TABLE marketplace_transactions ADD COLUMN tax INTEGER NOT NULL DEFAULT 0;
    END IF;
END $$;

-- ---------- 0003: listing buyer reference (set on purchase) ----------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'marketplace_listings' AND column_name = 'buyer_id'
    ) THEN
        ALTER TABLE marketplace_listings ADD COLUMN buyer_id INTEGER;
    END IF;
END $$;

-- ---------- 0004: 2FA canonical fields on two_factor_auth ----------
-- The model now uses secret_key / updated_at as canonical names; legacy rows
-- that were created under the old (broken) column naming keep working because
-- create_all only creates the table when missing. If the table already exists
-- but is missing these columns, add them here.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'two_factor_auth' AND column_name = 'secret_key'
    ) THEN
        ALTER TABLE two_factor_auth ADD COLUMN secret_key VARCHAR(100);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'two_factor_auth' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE two_factor_auth ADD COLUMN updated_at TIMESTAMP;
    END IF;
END $$;
