-- ============================================================================
-- CLEAN INSTALLATION SCRIPT FOR PLACEMENT MANAGEMENT SYSTEM
-- This script will drop and recreate everything
-- ============================================================================

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- ============================================================================
-- STEP 1: DROP EXISTING DATABASE (CLEAN SLATE)
-- ============================================================================
DROP DATABASE IF EXISTS `placementdb`;
DROP DATABASE IF EXISTS `PlacementDB`;

-- ============================================================================
-- STEP 2: CREATE DATABASE
-- ============================================================================
CREATE DATABASE `placementdb` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE `placementdb`;

-- ============================================================================
-- STEP 3: CREATE TABLES
-- ============================================================================

-- Table: student
CREATE TABLE `student` (
  `student_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `phone` VARCHAR(15) NULL DEFAULT NULL,
  `department` VARCHAR(30) NOT NULL,
  `cgpa` DECIMAL(3,2) NOT NULL,
  `backlogs` INT NULL DEFAULT 0,
  `resume` VARCHAR(255) NULL DEFAULT NULL,
  `password` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`student_id`),
  UNIQUE INDEX `email` (`email` ASC),
  UNIQUE INDEX `phone` (`phone` ASC),
  INDEX `idx_department` (`department` ASC),
  INDEX `idx_cgpa` (`cgpa` DESC)
) ENGINE = InnoDB;

-- Table: admin_user
CREATE TABLE `admin_user` (
  `admin_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `role` ENUM('TPO', 'Admin', 'HR') NOT NULL DEFAULT 'TPO',
  `phone` VARCHAR(15) NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`admin_id`),
  UNIQUE INDEX `email` (`email` ASC)
) ENGINE = InnoDB;

-- Table: company
CREATE TABLE `company` (
  `company_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `location` VARCHAR(50) NULL DEFAULT NULL,
  `industry` VARCHAR(50) NULL DEFAULT NULL,
  `website` VARCHAR(255) NULL,
  `hr_contact` VARCHAR(100) NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`company_id`),
  UNIQUE INDEX `name` (`name` ASC)
) ENGINE = InnoDB;

-- Table: job_role
CREATE TABLE `job_role` (
  `job_id` INT NOT NULL AUTO_INCREMENT,
  `role_name` VARCHAR(50) NOT NULL,
  `min_cgpa` DECIMAL(3,2) NOT NULL,
  `job_type` ENUM('Internship', 'Full-time') NOT NULL,
  `salary_range` VARCHAR(50) NULL,
  `description` TEXT NULL,
  `company_id` INT NOT NULL,
  PRIMARY KEY (`job_id`),
  INDEX `company_id` (`company_id` ASC),
  CONSTRAINT `job_role_ibfk_1`
    FOREIGN KEY (`company_id`)
    REFERENCES `company` (`company_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- Table: placement_drive
CREATE TABLE `placement_drive` (
  `drive_id` INT NOT NULL AUTO_INCREMENT,
  `drive_date` DATE NOT NULL,
  `mode` ENUM('Online', 'Offline', 'Hybrid') NOT NULL,
  `deadline` DATE NOT NULL,
  `venue` VARCHAR(255) NULL,
  `company_id` INT NOT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`drive_id`),
  INDEX `company_id` (`company_id` ASC),
  INDEX `idx_deadline` (`deadline` ASC),
  CONSTRAINT `placement_drive_ibfk_1`
    FOREIGN KEY (`company_id`)
    REFERENCES `company` (`company_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- Table: application
CREATE TABLE `application` (
  `application_id` INT NOT NULL AUTO_INCREMENT,
  `student_id` INT NOT NULL,
  `drive_id` INT NOT NULL,
  `status` ENUM('Applied', 'Shortlisted', 'Interviewed', 'Selected', 'Rejected') NULL DEFAULT 'Applied',
  `applied_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`application_id`),
  UNIQUE INDEX `student_drive_unique` (`student_id` ASC, `drive_id` ASC),
  INDEX `drive_id` (`drive_id` ASC),
  INDEX `idx_status` (`status` ASC),
  CONSTRAINT `application_ibfk_1`
    FOREIGN KEY (`student_id`)
    REFERENCES `student` (`student_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `application_ibfk_2`
    FOREIGN KEY (`drive_id`)
    REFERENCES `placement_drive` (`drive_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- Table: interview_round
CREATE TABLE `interview_round` (
  `round_id` INT NOT NULL AUTO_INCREMENT,
  `application_id` INT NOT NULL,
  `round_number` INT NOT NULL,
  `round_type` ENUM('Technical', 'HR', 'Aptitude', 'Group Discussion') NULL,
  `result` ENUM('Pass', 'Fail', 'Pending') NULL DEFAULT 'Pending',
  `feedback` TEXT NULL,
  `interview_date` DATE NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`round_id`),
  UNIQUE INDEX `application_round_unique` (`application_id` ASC, `round_number` ASC),
  CONSTRAINT `interview_round_ibfk_1`
    FOREIGN KEY (`application_id`)
    REFERENCES `application` (`application_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- Table: offer
CREATE TABLE `offer` (
  `offer_id` INT NOT NULL AUTO_INCREMENT,
  `application_id` INT NOT NULL,
  `salary` DECIMAL(10,2) NULL DEFAULT NULL,
  `status` ENUM('Accepted', 'Rejected', 'Pending') NULL DEFAULT 'Pending',
  `joining_date` DATE NULL DEFAULT NULL,
  `offered_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `response_deadline` DATE NULL,
  PRIMARY KEY (`offer_id`),
  UNIQUE INDEX `application_id` (`application_id` ASC),
  CONSTRAINT `offer_ibfk_1`
    FOREIGN KEY (`application_id`)
    REFERENCES `application` (`application_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- Table: skill
CREATE TABLE `skill` (
  `skill_id` INT NOT NULL AUTO_INCREMENT,
  `skill_name` VARCHAR(50) NOT NULL,
  `category` VARCHAR(50) NULL,
  PRIMARY KEY (`skill_id`),
  UNIQUE INDEX `skill_name` (`skill_name` ASC)
) ENGINE = InnoDB;

-- Table: student_skill
CREATE TABLE `student_skill` (
  `student_id` INT NOT NULL,
  `skill_id` INT NOT NULL,
  `proficiency_level` ENUM('Beginner', 'Intermediate', 'Advanced', 'Expert') NULL DEFAULT 'Intermediate',
  PRIMARY KEY (`student_id`, `skill_id`),
  INDEX `skill_id` (`skill_id` ASC),
  CONSTRAINT `student_skill_ibfk_1`
    FOREIGN KEY (`student_id`)
    REFERENCES `student` (`student_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `student_skill_ibfk_2`
    FOREIGN KEY (`skill_id`)
    REFERENCES `skill` (`skill_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- Table: user_sessions
CREATE TABLE `user_sessions` (
  `session_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `user_type` ENUM('Student', 'Admin') NOT NULL,
  `token` VARCHAR(500) NOT NULL,
  `expires_at` TIMESTAMP NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`session_id`),
  UNIQUE INDEX `token` (`token` ASC),
  INDEX `idx_user` (`user_id`, `user_type`)
) ENGINE = InnoDB;

-- Table: activity_log
CREATE TABLE `activity_log` (
  `log_id` INT NOT NULL AUTO_INCREMENT,
  `user_type` ENUM('Student', 'Admin', 'HR') NOT NULL,
  `user_id` INT NOT NULL,
  `action` VARCHAR(255) NOT NULL,
  `table_affected` VARCHAR(50) NULL,
  `record_id` INT NULL,
  `ip_address` VARCHAR(45) NULL,
  `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`log_id`),
  INDEX `idx_user_type_id` (`user_type`, `user_id`),
  INDEX `idx_timestamp` (`timestamp`)
) ENGINE = InnoDB;

-- ============================================================================
-- STEP 4: CREATE STORED PROCEDURES
-- ============================================================================

DELIMITER $$

-- Procedure: EnrollStudent
DROP PROCEDURE IF EXISTS `EnrollStudent`$$
CREATE PROCEDURE `EnrollStudent`(
  IN  p_student_id INT,
  IN  p_drive_id   INT,
  OUT p_message    VARCHAR(255)
)
BEGIN
  DECLARE v_cgpa     DECIMAL(3,2);
  DECLARE v_min_cgpa DECIMAL(3,2);
  DECLARE v_deadline DATE;
  DECLARE v_already  INT DEFAULT 0;
 
  SELECT cgpa INTO v_cgpa FROM student WHERE student_id = p_student_id;
  SELECT deadline INTO v_deadline FROM placement_drive WHERE drive_id = p_drive_id;
  
  SELECT MIN(jr.min_cgpa) INTO v_min_cgpa
  FROM job_role jr 
  JOIN placement_drive pd ON jr.company_id = pd.company_id
  WHERE pd.drive_id = p_drive_id;
 
  IF CURDATE() > v_deadline THEN
    SET p_message = 'ERROR: Application deadline has passed.';
  ELSEIF v_cgpa < v_min_cgpa THEN
    SET p_message = CONCAT('ERROR: CGPA ', v_cgpa, ' below required ', v_min_cgpa);
  ELSE
    SELECT COUNT(*) INTO v_already 
    FROM application
    WHERE student_id = p_student_id AND drive_id = p_drive_id;
    
    IF v_already > 0 THEN
      SET p_message = 'ERROR: Already applied to this drive.';
    ELSE
      INSERT INTO application (student_id, drive_id, status) 
      VALUES (p_student_id, p_drive_id, 'Applied');
      SET p_message = 'SUCCESS: Application submitted.';
    END IF;
  END IF;
END$$

-- Procedure: UpdateApplicationStatus
DROP PROCEDURE IF EXISTS `UpdateApplicationStatus`$$
CREATE PROCEDURE `UpdateApplicationStatus`(
  IN p_application_id INT,
  IN p_new_status ENUM('Applied','Shortlisted','Interviewed','Selected','Rejected'),
  IN p_round_number INT,
  IN p_result ENUM('Pass','Fail','Pending'),
  IN p_feedback TEXT
)
BEGIN
  UPDATE application SET status = p_new_status WHERE application_id = p_application_id;
  
  IF p_round_number IS NOT NULL THEN
    INSERT INTO interview_round (application_id, round_number, result, feedback)
    VALUES (p_application_id, p_round_number, p_result, p_feedback)
    ON DUPLICATE KEY UPDATE result = p_result, feedback = p_feedback;
  END IF;
END$$

-- Procedure: GetStudentReport
DROP PROCEDURE IF EXISTS `GetStudentReport`$$
CREATE PROCEDURE `GetStudentReport`(IN p_student_id INT)
BEGIN
  -- Student basic info
  SELECT student_id, name, email, department, cgpa, backlogs
  FROM student WHERE student_id = p_student_id;
 
  -- Student skills
  SELECT sk.skill_name, ss.proficiency_level
  FROM student_skill ss
  JOIN skill sk ON ss.skill_id = sk.skill_id
  WHERE ss.student_id = p_student_id;
 
  -- Applications and offers
  SELECT c.name AS Company, pd.drive_date, a.status,
         o.salary, o.status AS OfferStatus
  FROM application a
  JOIN placement_drive pd ON a.drive_id = pd.drive_id
  JOIN company c ON pd.company_id = c.company_id
  LEFT JOIN offer o ON a.application_id = o.application_id
  WHERE a.student_id = p_student_id;
END$$

DELIMITER ;

-- ============================================================================
-- STEP 5: CREATE FUNCTIONS
-- ============================================================================

DELIMITER $$

-- Function: GetPlacementStatus
DROP FUNCTION IF EXISTS `GetPlacementStatus`$$
CREATE FUNCTION `GetPlacementStatus`(p_student_id INT) 
RETURNS VARCHAR(20) 
READS SQL DATA
DETERMINISTIC
BEGIN
  DECLARE v_status VARCHAR(20);
  
  SELECT CASE
    WHEN SUM(o.status = 'Accepted') > 0 THEN 'Placed'
    WHEN MAX(a.status) = 'Selected' THEN 'Selected'
    WHEN MAX(a.status) = 'Interviewed' THEN 'In Process'
    WHEN MAX(a.status) = 'Applied' THEN 'Applied'
    ELSE 'Not Applied'
  END INTO v_status
  FROM application a 
  LEFT JOIN offer o ON a.application_id = o.application_id
  WHERE a.student_id = p_student_id;
  
  RETURN IFNULL(v_status, 'Not Applied');
END$$

-- Function: IsEligible
DROP FUNCTION IF EXISTS `IsEligible`$$
CREATE FUNCTION `IsEligible`(p_student_id INT, p_drive_id INT) 
RETURNS TINYINT(1)
READS SQL DATA
DETERMINISTIC
BEGIN
  DECLARE v_cgpa DECIMAL(3,2);
  DECLARE v_min_cgpa DECIMAL(3,2);
  
  SELECT cgpa INTO v_cgpa FROM student WHERE student_id = p_student_id;
  
  SELECT MIN(jr.min_cgpa) INTO v_min_cgpa
  FROM job_role jr 
  JOIN placement_drive pd ON jr.company_id = pd.company_id
  WHERE pd.drive_id = p_drive_id;
  
  RETURN (v_cgpa >= IFNULL(v_min_cgpa, 0));
END$$

-- Function: GetSkillCount
DROP FUNCTION IF EXISTS `GetSkillCount`$$
CREATE FUNCTION `GetSkillCount`(p_student_id INT) 
RETURNS INT
READS SQL DATA
DETERMINISTIC
BEGIN
  DECLARE v_count INT;
  SELECT COUNT(*) INTO v_count 
  FROM student_skill 
  WHERE student_id = p_student_id;
  RETURN v_count;
END$$

DELIMITER ;

-- ============================================================================
-- STEP 6: CREATE VIEWS
-- ============================================================================

-- View: vw_placement_summary
CREATE OR REPLACE VIEW `vw_placement_summary` AS
SELECT 
  s.student_id,
  s.name AS Student_Name,
  s.department,
  s.cgpa,
  c.name AS Company,
  a.status AS App_Status,
  o.salary AS Offered_Salary,
  o.status AS Offer_Status
FROM application a
JOIN student s ON a.student_id = s.student_id
JOIN placement_drive pd ON a.drive_id = pd.drive_id
JOIN company c ON pd.company_id = c.company_id
LEFT JOIN offer o ON a.application_id = o.application_id;

-- View: vw_drive_stats
CREATE OR REPLACE VIEW `vw_drive_stats` AS
SELECT 
  c.name AS Company,
  pd.drive_id,
  pd.drive_date,
  pd.mode,
  COUNT(a.application_id) AS Applications,
  SUM(a.status = 'Selected') AS Selected,
  SUM(a.status = 'Rejected') AS Rejected,
  SUM(a.status = 'Shortlisted') AS Shortlisted
FROM placement_drive pd
JOIN company c ON pd.company_id = c.company_id
LEFT JOIN application a ON pd.drive_id = a.drive_id
GROUP BY c.name, pd.drive_id, pd.drive_date, pd.mode;

-- View: vw_student_skills
CREATE OR REPLACE VIEW `vw_student_skills` AS
SELECT 
  s.student_id,
  s.name,
  GROUP_CONCAT(sk.skill_name ORDER BY sk.skill_name SEPARATOR ', ') AS Skills,
  COUNT(sk.skill_id) AS Skill_Count
FROM student s
LEFT JOIN student_skill ss ON s.student_id = ss.student_id
LEFT JOIN skill sk ON ss.skill_id = sk.skill_id
GROUP BY s.student_id, s.name;

-- ============================================================================
-- STEP 7: CREATE TRIGGERS
-- ============================================================================

DELIMITER $$

-- Trigger: prevent_placed_student_delete
DROP TRIGGER IF EXISTS `prevent_placed_student_delete`$$
CREATE TRIGGER `prevent_placed_student_delete`
BEFORE DELETE ON `student`
FOR EACH ROW
BEGIN
  DECLARE v_count INT;
  
  SELECT COUNT(*) INTO v_count
  FROM offer o 
  JOIN application a ON o.application_id = a.application_id
  WHERE a.student_id = OLD.student_id AND o.status = 'Accepted';
  
  IF v_count > 0 THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Cannot delete student with an accepted offer.';
  END IF;
END$$

-- Trigger: check_deadline
DROP TRIGGER IF EXISTS `check_deadline`$$
CREATE TRIGGER `check_deadline`
BEFORE INSERT ON `application`
FOR EACH ROW
BEGIN
  DECLARE v_deadline DATE;
  
  SELECT deadline INTO v_deadline 
  FROM placement_drive 
  WHERE drive_id = NEW.drive_id;
  
  IF CURDATE() > v_deadline THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Application rejected: Deadline has passed.';
  END IF;
END$$

-- Trigger: check_eligibility
DROP TRIGGER IF EXISTS `check_eligibility`$$
CREATE TRIGGER `check_eligibility`
BEFORE INSERT ON `application`
FOR EACH ROW
BEGIN
  DECLARE student_cgpa DECIMAL(3,2);
  DECLARE required_cgpa DECIMAL(3,2);

  SELECT cgpa INTO student_cgpa
  FROM student
  WHERE student_id = NEW.student_id;

  SELECT MIN(jr.min_cgpa) INTO required_cgpa
  FROM job_role jr
  JOIN placement_drive pd ON jr.company_id = pd.company_id
  WHERE pd.drive_id = NEW.drive_id;

  IF student_cgpa < required_cgpa THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Application rejected: CGPA below eligibility';
  END IF;
END$$

-- Trigger: auto_create_offer
DROP TRIGGER IF EXISTS `auto_create_offer`$$
CREATE TRIGGER `auto_create_offer`
AFTER UPDATE ON `application`
FOR EACH ROW
BEGIN
  IF NEW.status = 'Selected' AND OLD.status != 'Selected' THEN
    IF NOT EXISTS (
      SELECT 1 FROM offer WHERE application_id = NEW.application_id
    ) THEN
      INSERT INTO offer (application_id, status) 
      VALUES (NEW.application_id, 'Pending');
    END IF;
  END IF;
END$$

DELIMITER ;

-- ============================================================================
-- STEP 8: INSERT SAMPLE DATA (Optional - for testing)
-- ============================================================================

-- Insert Admin User (Password: admin123)
INSERT INTO admin_user (name, email, password, role) VALUES
('TPO Officer', 'tpo@university.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5U7gtE8cDkRGy', 'TPO');

-- Insert Sample Skills
INSERT INTO skill (skill_name, category) VALUES
('Python', 'Programming'),
('Java', 'Programming'),
('JavaScript', 'Programming'),
('React', 'Frontend'),
('MySQL', 'Database'),
('Communication', 'Soft Skill'),
('Leadership', 'Soft Skill'),
('Data Structures', 'Programming');

-- ============================================================================
-- STEP 9: VERIFICATION
-- ============================================================================

-- Show all tables
SELECT 'Tables Created:' AS Status;
SHOW TABLES;

-- Show all procedures
SELECT 'Stored Procedures:' AS Status;
SHOW PROCEDURE STATUS WHERE Db = 'placementdb';

-- Show all functions
SELECT 'Functions:' AS Status;
SHOW FUNCTION STATUS WHERE Db = 'placementdb';

-- Show all views
SELECT 'Views:' AS Status;
SHOW FULL TABLES WHERE Table_type = 'VIEW';

-- Show all triggers
SELECT 'Triggers:' AS Status;
SHOW TRIGGERS;

-- ============================================================================
-- RESET SETTINGS
-- ============================================================================
SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

SELECT '✅ DATABASE SETUP COMPLETE!' AS Status;
SELECT 'Database: placementdb' AS Info;
SELECT 'You can now start building the Python backend!' AS NextStep;