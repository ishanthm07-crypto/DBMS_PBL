USE legal_desk;
INSERT INTO client (full_name,phone,email,address) VALUES
('Anita Rao','98480 11223','anita.rao@example.com','Banjara Hills, Hyderabad'),
('Vikram Industries Pvt Ltd','040 2345 6789','legal@vikram.example','Madhapur, Hyderabad'),
('Suresh Kumar','99890 33445','suresh.k@example.com','Secunderabad'),
('Lakshmi Textiles','040 2788 1100','accounts@lakshmi.example','Gachibowli, Hyderabad');
INSERT INTO lawyer (full_name,specialization,bar_no,phone) VALUES
('Adv. Meera Reddy','Family','TS/1024/2012','98490 55667'),
('Adv. Rohan Shah','Corporate','TS/2231/2016','98660 44321'),
('Adv. Kiran Naidu','Criminal','TS/3310/2010','98851 77889');
INSERT INTO court (name,city,type) VALUES
('Telangana High Court','Hyderabad','High Court'),
('City Civil Court','Hyderabad','District'),
('NCLT Hyderabad Bench','Hyderabad','Tribunal');
INSERT INTO legal_case (title,case_type,status,filed_on,client_id,court_id) VALUES
('Rao vs Rao (custody)','Family','In hearing',CURDATE() - INTERVAL 60 DAY,1,2),
('Vikram Industries vs Sai Traders','Corporate','Open',CURDATE() - INTERVAL 20 DAY,2,1),
('State vs Suresh Kumar','Criminal','Open',CURDATE() - INTERVAL 35 DAY,3,2),
('Lakshmi Textiles vs Orion Exports','Corporate','In hearing',CURDATE() - INTERVAL 45 DAY,4,3),
('Rao property partition','Property','Closed',CURDATE() - INTERVAL 200 DAY,1,2);
INSERT INTO case_lawyer VALUES (1,1),(2,2),(2,1),(3,3),(4,2),(5,1);
INSERT INTO document (case_id,title,doc_type,added_on) VALUES
(1,'Custody petition','Petition',CURDATE() - INTERVAL 60 DAY),
(2,'Supply contract 2024','Contract',CURDATE() - INTERVAL 19 DAY),
(3,'Bail affidavit','Affidavit',CURDATE() - INTERVAL 30 DAY),
(4,'Share purchase agreement','Contract',CURDATE() - INTERVAL 44 DAY),
(4,'Statement of claim','Petition',CURDATE() - INTERVAL 40 DAY),
(5,'Final decree','Order',CURDATE() - INTERVAL 150 DAY);
INSERT INTO hearing (case_id,hearing_date,purpose,outcome) VALUES
(1,CURDATE() + INTERVAL 4 DAY,'Evidence of witnesses',NULL),
(2,CURDATE() + INTERVAL 12 DAY,'Admission of claim',NULL),
(1,CURDATE() - INTERVAL 14 DAY,'Interim order','Adjourned'),
(3,CURDATE() + INTERVAL 7 DAY,'Bail hearing',NULL),
(4,CURDATE() + INTERVAL 2 DAY,'Arguments on jurisdiction',NULL),
(4,CURDATE() - INTERVAL 20 DAY,'Notice served','Reply due in 3 weeks'),
(5,CURDATE() - INTERVAL 150 DAY,'Final hearing','Decree passed');
INSERT INTO billing (case_id,description,amount,status) VALUES
(1,'Filing and drafting fees',25000,'Paid'),
(2,'Retainer',60000,'Pending'),
(3,'Appearance fee',15000,'Pending'),
(4,'Drafting and filing',45000,'Paid'),
(4,'Hearing appearance',20000,'Pending'),
(5,'Final settlement fee',30000,'Paid');
INSERT INTO app_user (username,password_hash,display_name,role,lawyer_id,client_id) VALUES
('admin','pbkdf2:sha256:1000000$azk4GAepLNSwZo81$7d990ea780469072bb52d901c3a9940664998164bab530e9b6aadd8f32bfcbb9','Firm Administrator','admin',NULL,NULL),
('clerk','pbkdf2:sha256:1000000$trk6gSQokozy7Vyz$b02409f46d0c8d6b97b072645372b011520b3c3d229c42026b1d7681c76ee6e9','Priya (Office Clerk)','clerk',NULL,NULL),
('meera','pbkdf2:sha256:1000000$C4DCZZBgMITNhy0b$7e86fe5cb123f63fb7f8ae594e81f65fad697cdf547d36e615ffac91117a0938','Adv. Meera Reddy','lawyer',1,NULL),
('rohan','pbkdf2:sha256:1000000$ScLyhH2n7ZshjAPW$8d5f73b7cf830be20eccf72ef09f9e9af32e3b0d971cd343b562a79287b565df','Adv. Rohan Shah','lawyer',2,NULL),
('anita','pbkdf2:sha256:1000000$DPuuAZNB5Adh7i1p$56a2359182f79dd7f0bd6a858415148f65ef6e71dbb25c37d3795687857bffdb','Anita Rao','client',NULL,1),
('vikram','pbkdf2:sha256:1000000$BXgNwqSoxjf28HoZ$fd6e7893c5e4071fe918a4b63b4325dd6fdf95ce57ab08296d66cd0d7afa4cd6','Vikram Industries','client',NULL,2);
