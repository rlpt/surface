-- Surface seed data — ported from plain-text ledgers

-- ============================================================
-- Accounts (chart of accounts)
-- ============================================================

INSERT INTO accounts (path, account_type) VALUES
  ('assets:bank:tide',           'assets'),
  ('assets:bank:savings',        'assets'),
  ('liabilities:cc:business',    'liabilities'),
  ('liabilities:tax:vat',        'liabilities'),
  ('liabilities:tax:corp',       'liabilities'),
  ('expenses:infra:hosting',     'expenses'),
  ('expenses:infra:cloud',       'expenses'),
  ('expenses:infra:domains',     'expenses'),
  ('expenses:tools:design',      'expenses'),
  ('expenses:tools:dev',         'expenses'),
  ('expenses:admin:compliance',  'expenses'),
  ('expenses:admin:insurance',   'expenses'),
  ('expenses:travel',            'expenses'),
  ('expenses:payroll:salary',    'expenses'),
  ('expenses:payroll:pension',   'expenses'),
  ('revenue:sales',              'revenue'),
  ('revenue:consulting',         'revenue'),
  ('equity:opening-balances',    'equity');

-- ============================================================
-- Share classes
-- ============================================================

INSERT INTO share_classes (name, nominal_value, nominal_currency, authorised) VALUES
  ('ordinary', 0.01, 'GBP', 10000);

-- ============================================================
-- Holders
-- ============================================================

INSERT INTO holders (id, display_name) VALUES
  ('richard', 'Richard Targett'),
  ('mark',    'Mark Holland'),
  ('emma',    'Emma Loxey');

-- ============================================================
-- Share events (chronological)
-- ============================================================

INSERT INTO share_events (event_date, event_type, holder_id, share_class, quantity) VALUES
  ('2024-06-01', 'grant',        'richard', 'ordinary', 1000),
  ('2026-02-13', 'transfer-out', 'richard', 'ordinary', 10),
  ('2026-02-13', 'transfer-in',  'mark',    'ordinary', 10),
  ('2026-02-13', 'transfer-out', 'richard', 'ordinary', 69),
  ('2026-02-13', 'transfer-in',  'emma',    'ordinary', 69),
  ('2026-02-13', 'grant',        'richard', 'ordinary', 7079);

-- ============================================================
-- Pools
-- ============================================================

INSERT INTO pools (name, share_class, budget) VALUES
  ('founder',        'ordinary', 8000),
  ('supporter',      'ordinary', 1000),
  ('early-supporter', 'ordinary', 81),
  ('investment',     'ordinary', 1000);

INSERT INTO pool_members (pool_name, holder_id) VALUES
  ('founder',   'richard'),
  ('supporter', 'mark'),
  ('supporter', 'emma');
