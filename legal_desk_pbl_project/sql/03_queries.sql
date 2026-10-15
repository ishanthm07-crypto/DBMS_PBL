USE legal_desk;
-- Who can log in, and as what
SELECT user_id, username, display_name, role, lawyer_id, client_id FROM app_user;
-- Cases with client, court and lawyers
SELECT c.case_id, c.title, cl.full_name AS client, co.name AS court,
       GROUP_CONCAT(l.full_name SEPARATOR ', ') AS lawyers
FROM legal_case c JOIN client cl ON cl.client_id=c.client_id JOIN court co ON co.court_id=c.court_id
LEFT JOIN case_lawyer cla ON cla.case_id=c.case_id LEFT JOIN lawyer l ON l.lawyer_id=cla.lawyer_id
GROUP BY c.case_id;
-- Hearings in the next 30 days
SELECT h.hearing_date, c.title, h.purpose FROM hearing h JOIN legal_case c USING (case_id)
WHERE h.hearing_date BETWEEN CURDATE() AND CURDATE() + INTERVAL 30 DAY ORDER BY h.hearing_date;
-- Views
SELECT * FROM v_case_summary;
SELECT * FROM v_pending_fees;
-- Lawyer workload
SELECT l.full_name, COUNT(cla.case_id) AS cases_handled FROM lawyer l
LEFT JOIN case_lawyer cla ON cla.lawyer_id=l.lawyer_id GROUP BY l.lawyer_id ORDER BY cases_handled DESC;
-- Latest activity (written by the web app and the trigger)
SELECT a.log_id, a.created_at, COALESCE(u.username,'system') AS who, a.action, a.table_name, a.record_id, a.details
FROM activity_log a LEFT JOIN app_user u USING (user_id) ORDER BY a.log_id DESC LIMIT 15;
-- Trigger demo: mark a bill paid, then look at the log
-- UPDATE billing SET status='Paid' WHERE bill_id=2;
-- Integrity demo: fails because the client still has cases
-- DELETE FROM client WHERE client_id=1;
