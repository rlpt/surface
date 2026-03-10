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
-- CRM
-- ============================================================

CREATE TABLE contacts (
  id VARCHAR(50) PRIMARY KEY,
  company VARCHAR(200) NOT NULL,
  name VARCHAR(200) NOT NULL,
  email VARCHAR(200),
  role VARCHAR(100),
  source VARCHAR(50),
  stage VARCHAR(20) NOT NULL DEFAULT 'lead'
    CHECK (stage IN ('lead', 'prospect', 'customer', 'churned', 'dormant')),
  notes TEXT,
  created_at DATE NOT NULL DEFAULT (CURRENT_DATE),
  last_contacted DATE,
  next_action_date DATE,
  next_action TEXT
);

CREATE TABLE interactions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  contact_id VARCHAR(50) NOT NULL,
  interaction_date DATE NOT NULL DEFAULT (CURRENT_DATE),
  channel VARCHAR(20) NOT NULL
    CHECK (channel IN ('email', 'call', 'meeting', 'demo', 'slack', 'event', 'other')),
  direction VARCHAR(10) NOT NULL DEFAULT 'outbound'
    CHECK (direction IN ('inbound', 'outbound')),
  summary TEXT NOT NULL,
  follow_up TEXT,
  FOREIGN KEY (contact_id) REFERENCES contacts(id),
  INDEX idx_interaction_date (interaction_date)
);

CREATE TABLE deals (
  id VARCHAR(50) PRIMARY KEY,
  contact_id VARCHAR(50) NOT NULL,
  title VARCHAR(200) NOT NULL,
  stage VARCHAR(20) NOT NULL DEFAULT 'qualifying'
    CHECK (stage IN ('qualifying', 'proposal', 'negotiation', 'closed-won', 'closed-lost')),
  value_gbp DECIMAL(10,2),
  recurring VARCHAR(10) CHECK (recurring IN ('monthly', 'annual', 'one-off')),
  opened_date DATE NOT NULL DEFAULT (CURRENT_DATE),
  closed_date DATE,
  lost_reason TEXT,
  notes TEXT,
  FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

CREATE TABLE tags (
  contact_id VARCHAR(50) NOT NULL,
  tag VARCHAR(50) NOT NULL,
  PRIMARY KEY (contact_id, tag),
  FOREIGN KEY (contact_id) REFERENCES contacts(id)
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

CREATE VIEW pipeline AS
SELECT
  d.stage,
  COUNT(*) AS deals,
  SUM(d.value_gbp) AS total_value,
  GROUP_CONCAT(c.company ORDER BY d.value_gbp DESC) AS companies
FROM deals d
JOIN contacts c ON c.id = d.contact_id
WHERE d.stage NOT IN ('closed-won', 'closed-lost')
GROUP BY d.stage
ORDER BY FIELD(d.stage, 'qualifying', 'proposal', 'negotiation');

CREATE VIEW stale_contacts AS
SELECT
  id, company, name, stage, last_contacted, next_action, next_action_date
FROM contacts
WHERE stage IN ('lead', 'prospect')
  AND (last_contacted IS NULL OR last_contacted < DATE_SUB(CURRENT_DATE, INTERVAL 14 DAY))
ORDER BY last_contacted ASC;
