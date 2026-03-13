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
-- CRM (customer contract management)
-- ============================================================

CREATE TABLE customers (
  id VARCHAR(50) PRIMARY KEY,
  company VARCHAR(200) NOT NULL,
  company_number VARCHAR(50),
  address TEXT,
  notes TEXT,
  created_at DATE NOT NULL DEFAULT (CURRENT_DATE)
);

CREATE TABLE contacts (
  id VARCHAR(50) PRIMARY KEY,
  customer_id VARCHAR(50) NOT NULL,
  name VARCHAR(200) NOT NULL,
  email VARCHAR(200),
  role VARCHAR(100),
  notes TEXT,
  created_at DATE NOT NULL DEFAULT (CURRENT_DATE),
  FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE contracts (
  id VARCHAR(50) PRIMARY KEY,
  customer_id VARCHAR(50) NOT NULL,
  title VARCHAR(200) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'active', 'expired', 'terminated')),
  effective_date DATE,
  term_months INT,
  auto_renew BOOLEAN DEFAULT FALSE,
  payment_terms VARCHAR(50) DEFAULT 'net-30',
  currency CHAR(3) NOT NULL DEFAULT 'GBP',
  governing_law VARCHAR(100) DEFAULT 'England and Wales',
  jurisdiction VARCHAR(100) DEFAULT 'Courts of England and Wales',
  notice_period_days INT DEFAULT 30,
  notes TEXT,
  created_at DATE NOT NULL DEFAULT (CURRENT_DATE),
  FOREIGN KEY (customer_id) REFERENCES customers(id),
  INDEX idx_contract_status (status)
);

CREATE TABLE contract_lines (
  contract_id VARCHAR(50) NOT NULL,
  seq INT NOT NULL,
  description VARCHAR(500) NOT NULL,
  quantity DECIMAL(10,2) NOT NULL DEFAULT 1,
  unit_price DECIMAL(10,2) NOT NULL,
  frequency VARCHAR(20) NOT NULL DEFAULT 'monthly'
    CHECK (frequency IN ('monthly', 'quarterly', 'annual', 'one-off')),
  PRIMARY KEY (contract_id, seq),
  FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE TABLE contract_clauses (
  contract_id VARCHAR(50) NOT NULL,
  seq INT NOT NULL,
  heading VARCHAR(200) NOT NULL,
  body TEXT NOT NULL,
  PRIMARY KEY (contract_id, seq),
  FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

-- ============================================================
-- Board (meetings, minutes, resolutions)
-- ============================================================

CREATE TABLE board_meetings (
  id VARCHAR(50) PRIMARY KEY,
  meeting_date DATE NOT NULL,
  title VARCHAR(200) NOT NULL,
  location VARCHAR(200),
  status VARCHAR(20) NOT NULL DEFAULT 'scheduled'
    CHECK (status IN ('scheduled', 'in-progress', 'completed', 'cancelled')),
  called_by VARCHAR(200),
  created_at DATE NOT NULL DEFAULT (CURRENT_DATE),
  INDEX idx_meeting_date (meeting_date)
);

CREATE TABLE board_attendees (
  meeting_id VARCHAR(50) NOT NULL,
  person_name VARCHAR(200) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'director'
    CHECK (role IN ('chair', 'secretary', 'director', 'observer')),
  PRIMARY KEY (meeting_id, person_name),
  FOREIGN KEY (meeting_id) REFERENCES board_meetings(id)
);

CREATE TABLE board_minutes (
  meeting_id VARCHAR(50) NOT NULL,
  seq INT NOT NULL,
  item_text TEXT NOT NULL,
  PRIMARY KEY (meeting_id, seq),
  FOREIGN KEY (meeting_id) REFERENCES board_meetings(id)
);

CREATE TABLE board_resolutions (
  id VARCHAR(50) PRIMARY KEY,
  meeting_id VARCHAR(50) NOT NULL,
  resolution_text TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'passed', 'failed', 'withdrawn')),
  proposed_by VARCHAR(200),
  voted_date DATE,
  FOREIGN KEY (meeting_id) REFERENCES board_meetings(id),
  INDEX idx_resolution_status (status)
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

CREATE VIEW contract_summary AS
SELECT
  ct.id,
  cu.company,
  ct.title,
  ct.status,
  ct.effective_date,
  ct.term_months,
  ct.auto_renew,
  ct.currency,
  COALESCE(SUM(CASE cl.frequency
    WHEN 'monthly' THEN cl.quantity * cl.unit_price
    WHEN 'quarterly' THEN cl.quantity * cl.unit_price / 3
    WHEN 'annual' THEN cl.quantity * cl.unit_price / 12
    ELSE 0
  END), 0) AS mrr,
  COUNT(DISTINCT cl.seq) AS line_count,
  COUNT(DISTINCT cc.seq) AS clause_count
FROM contracts ct
JOIN customers cu ON cu.id = ct.customer_id
LEFT JOIN contract_lines cl ON cl.contract_id = ct.id
LEFT JOIN contract_clauses cc ON cc.contract_id = ct.id
GROUP BY ct.id, cu.company, ct.title, ct.status, ct.effective_date,
  ct.term_months, ct.auto_renew, ct.currency;

CREATE VIEW renewals_due AS
SELECT
  ct.id,
  cu.company,
  ct.title,
  ct.status,
  ct.auto_renew,
  DATE_ADD(ct.effective_date, INTERVAL ct.term_months MONTH) AS expiry_date,
  DATEDIFF(DATE_ADD(ct.effective_date, INTERVAL ct.term_months MONTH), CURRENT_DATE) AS days_left
FROM contracts ct
JOIN customers cu ON cu.id = ct.customer_id
WHERE ct.status = 'active'
  AND ct.term_months IS NOT NULL
  AND DATE_ADD(ct.effective_date, INTERVAL ct.term_months MONTH)
      <= DATE_ADD(CURRENT_DATE, INTERVAL 90 DAY)
ORDER BY expiry_date ASC;
