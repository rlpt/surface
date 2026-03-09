-- Surface database schema

-- ============================================================
-- Accounts (double-entry bookkeeping)
-- ============================================================

CREATE TABLE accounts (
  path VARCHAR(100) PRIMARY KEY,
  account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('assets', 'liabilities', 'expenses', 'revenue', 'equity'))
);

CREATE TABLE transactions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  txn_date DATE NOT NULL,
  payee VARCHAR(200) NOT NULL,
  description VARCHAR(500),
  INDEX idx_txn_date (txn_date)
);

CREATE TABLE postings (
  id INT PRIMARY KEY AUTO_INCREMENT,
  txn_id INT NOT NULL,
  account_path VARCHAR(100) NOT NULL,
  amount DECIMAL(15,2) NOT NULL,
  currency CHAR(3) NOT NULL DEFAULT 'GBP',
  FOREIGN KEY (txn_id) REFERENCES transactions(id),
  FOREIGN KEY (account_path) REFERENCES accounts(path)
);

-- ============================================================
-- Shares (cap table)
-- ============================================================

CREATE TABLE share_classes (
  name VARCHAR(50) PRIMARY KEY,
  nominal_value DECIMAL(10,4) NOT NULL,
  nominal_currency CHAR(3) NOT NULL DEFAULT 'GBP',
  authorised INT NOT NULL CHECK (authorised > 0)
);

CREATE TABLE holders (
  id VARCHAR(50) PRIMARY KEY,
  display_name VARCHAR(200) NOT NULL
);

CREATE TABLE share_events (
  id INT PRIMARY KEY AUTO_INCREMENT,
  event_date DATE NOT NULL,
  event_type VARCHAR(20) NOT NULL CHECK (event_type IN ('grant', 'transfer-in', 'transfer-out', 'cancel')),
  holder_id VARCHAR(50) NOT NULL,
  share_class VARCHAR(50) NOT NULL,
  quantity INT NOT NULL CHECK (quantity > 0),
  vesting_start DATE,
  vesting_months INT,
  vesting_cliff_months INT,
  FOREIGN KEY (holder_id) REFERENCES holders(id),
  FOREIGN KEY (share_class) REFERENCES share_classes(name),
  INDEX idx_event_date (event_date)
);

CREATE TABLE pools (
  name VARCHAR(50) PRIMARY KEY,
  share_class VARCHAR(50) NOT NULL,
  budget INT NOT NULL CHECK (budget > 0),
  FOREIGN KEY (share_class) REFERENCES share_classes(name)
);

CREATE TABLE pool_members (
  pool_name VARCHAR(50) NOT NULL,
  holder_id VARCHAR(50) NOT NULL,
  PRIMARY KEY (pool_name, holder_id),
  FOREIGN KEY (pool_name) REFERENCES pools(name),
  FOREIGN KEY (holder_id) REFERENCES holders(id)
);

-- ============================================================
-- Views
-- ============================================================

CREATE VIEW holdings AS
SELECT
  holder_id,
  share_class,
  SUM(CASE
    WHEN event_type IN ('grant', 'transfer-in') THEN quantity
    ELSE -quantity
  END) AS shares_held
FROM share_events
GROUP BY holder_id, share_class
HAVING shares_held > 0;

CREATE VIEW cap_table AS
SELECT
  h.display_name AS holder,
  ho.holder_id,
  ho.share_class AS class,
  ho.shares_held AS held,
  ROUND(ho.shares_held * 100.0 / (SELECT SUM(shares_held) FROM holdings), 1) AS pct
FROM holdings ho
JOIN holders h ON h.id = ho.holder_id
ORDER BY h.display_name;

CREATE VIEW account_balances AS
SELECT
  p.account_path,
  a.account_type,
  SUM(p.amount) AS balance,
  p.currency
FROM postings p
JOIN accounts a ON a.path = p.account_path
GROUP BY p.account_path, a.account_type, p.currency;

CREATE VIEW class_availability AS
SELECT
  sc.name AS class,
  sc.authorised,
  COALESCE(i.issued, 0) AS issued,
  sc.authorised - COALESCE(i.issued, 0) AS available
FROM share_classes sc
LEFT JOIN (
  SELECT share_class, SUM(shares_held) AS issued FROM holdings GROUP BY share_class
) i ON i.share_class = sc.name;
