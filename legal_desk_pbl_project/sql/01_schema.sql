-- Legal Desk: Legal Case and Client Management System (MySQL 8 / MariaDB)
DROP DATABASE IF EXISTS legal_desk;
CREATE DATABASE legal_desk CHARACTER SET utf8mb4;
USE legal_desk;

CREATE TABLE client (
  client_id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(100) NOT NULL,
  phone     VARCHAR(20),
  email     VARCHAR(100) UNIQUE,
  address   VARCHAR(200)
);
CREATE TABLE lawyer (
  lawyer_id      INT AUTO_INCREMENT PRIMARY KEY,
  full_name      VARCHAR(100) NOT NULL,
  specialization VARCHAR(60),
  bar_no         VARCHAR(30) NOT NULL UNIQUE,
  phone          VARCHAR(20)
);
CREATE TABLE court (
  court_id INT AUTO_INCREMENT PRIMARY KEY,
  name     VARCHAR(120) NOT NULL,
  city     VARCHAR(60),
  type     ENUM('District','High Court','Supreme Court','Tribunal') NOT NULL
);
-- CASE is a reserved word in MySQL, so the table is named legal_case
CREATE TABLE legal_case (
  case_id   INT AUTO_INCREMENT PRIMARY KEY,
  title     VARCHAR(150) NOT NULL,
  case_type ENUM('Civil','Criminal','Family','Corporate','Property') NOT NULL,
  status    ENUM('Open','In hearing','Closed') NOT NULL DEFAULT 'Open',
  filed_on  DATE NOT NULL,
  client_id INT NOT NULL,
  court_id  INT NOT NULL,
  FOREIGN KEY (client_id) REFERENCES client(client_id) ON DELETE RESTRICT,
  FOREIGN KEY (court_id)  REFERENCES court(court_id)   ON DELETE RESTRICT
);
CREATE TABLE case_lawyer (            -- many-to-many
  case_id   INT NOT NULL,
  lawyer_id INT NOT NULL,
  PRIMARY KEY (case_id, lawyer_id),
  FOREIGN KEY (case_id)   REFERENCES legal_case(case_id) ON DELETE CASCADE,
  FOREIGN KEY (lawyer_id) REFERENCES lawyer(lawyer_id)   ON DELETE RESTRICT
);
CREATE TABLE document (
  document_id INT AUTO_INCREMENT PRIMARY KEY,
  case_id     INT NOT NULL,
  title       VARCHAR(150) NOT NULL,
  doc_type    ENUM('Petition','Affidavit','Evidence','Order','Contract') NOT NULL,
  added_on    DATE NOT NULL,
  FOREIGN KEY (case_id) REFERENCES legal_case(case_id) ON DELETE CASCADE
);
CREATE TABLE hearing (
  hearing_id   INT AUTO_INCREMENT PRIMARY KEY,
  case_id      INT NOT NULL,
  hearing_date DATE NOT NULL,
  purpose      VARCHAR(150),
  outcome      VARCHAR(150),
  FOREIGN KEY (case_id) REFERENCES legal_case(case_id) ON DELETE CASCADE
);
CREATE TABLE billing (
  bill_id     INT AUTO_INCREMENT PRIMARY KEY,
  case_id     INT NOT NULL,
  description VARCHAR(150) NOT NULL,
  amount      DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
  status      ENUM('Pending','Paid') NOT NULL DEFAULT 'Pending',
  FOREIGN KEY (case_id) REFERENCES legal_case(case_id) ON DELETE CASCADE
);
-- Login accounts: each role sees different data. Passwords are stored hashed.
CREATE TABLE app_user (
  user_id       INT AUTO_INCREMENT PRIMARY KEY,
  username      VARCHAR(40) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  display_name  VARCHAR(100) NOT NULL,
  role          ENUM('admin','clerk','lawyer','client') NOT NULL,
  lawyer_id     INT NULL,
  client_id     INT NULL,
  FOREIGN KEY (lawyer_id) REFERENCES lawyer(lawyer_id) ON DELETE RESTRICT,
  FOREIGN KEY (client_id) REFERENCES client(client_id) ON DELETE RESTRICT
);
CREATE TABLE activity_log (
  log_id     INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NULL,
  action     VARCHAR(30) NOT NULL,
  table_name VARCHAR(30),
  record_id  INT,
  details    VARCHAR(200),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES app_user(user_id) ON DELETE SET NULL
);
CREATE INDEX idx_case_client ON legal_case(client_id);
CREATE INDEX idx_hearing_date ON hearing(hearing_date);

CREATE VIEW v_case_summary AS
SELECT c.case_id, c.title, c.status, cl.full_name AS client, co.name AS court,
       (SELECT COUNT(*) FROM hearing h WHERE h.case_id = c.case_id) AS hearings,
       (SELECT COALESCE(SUM(amount),0) FROM billing b WHERE b.case_id = c.case_id) AS billed
FROM legal_case c JOIN client cl ON cl.client_id = c.client_id JOIN court co ON co.court_id = c.court_id;

CREATE VIEW v_pending_fees AS
SELECT cl.client_id, cl.full_name, SUM(b.amount) AS pending_amount
FROM billing b JOIN legal_case c ON c.case_id = b.case_id JOIN client cl ON cl.client_id = c.client_id
WHERE b.status = 'Pending' GROUP BY cl.client_id, cl.full_name;

-- Trigger: record a log entry whenever a bill changes from Pending to Paid
CREATE TRIGGER trg_bill_paid AFTER UPDATE ON billing FOR EACH ROW
INSERT INTO activity_log (user_id, action, table_name, record_id, details)
SELECT NULL, 'PAYMENT_RECEIVED', 'billing', NEW.bill_id, CONCAT('Bill paid: ', NEW.amount)
FROM DUAL WHERE NEW.status = 'Paid' AND OLD.status = 'Pending';
