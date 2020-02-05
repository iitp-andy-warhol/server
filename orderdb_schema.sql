-- MySQL Workbench Forward Engineering
/*
SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';
*/
-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema orderdb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema orderdb
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema orderdb
-- -----------------------------------------------------
 SET NAMES utf8mb4 ;
 SET SQL_MODE='ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Table `orderdb`.`scheduler`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `orderdb`.`scheduler` ;
SET character_set_client = utf8mb4 ;
CREATE TABLE IF NOT EXISTS `orderdb`.`scheduler` (
  `scheduler_id` INT NOT NULL AUTO_INCREMENT,
  `developed_date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `comment` VARCHAR(45) NULL DEFAULT '',
  PRIMARY KEY (`scheduler_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `orderdb`.`experiment`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `orderdb`.`experiment` ;

CREATE TABLE IF NOT EXISTS `orderdb`.`experiment` (
  `exp_id` INT NOT NULL AUTO_INCREMENT,
  `start_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_time` TIMESTAMP NULL DEFAULT NULL,
  `max_time` INT(4) NOT NULL,
  `num_order` INT(11) NOT NULL DEFAULT 0,
  `num_fulfilled` INT(11) NOT NULL DEFAULT 0,
  `order_stop_time` INT(4) NOT NULL,
  `dist_item` VARCHAR(45) NULL DEFAULT NULL,
  `dist_address` VARCHAR(45) NULL DEFAULT NULL,
  `dist_order` VARCHAR(45) NULL DEFAULT NULL,
  `scheduler_id` INT NOT NULL,
  `reliability` TINYINT(1) NULL DEFAULT 0,
  PRIMARY KEY (`exp_id`),
  INDEX `fk1_idx` (`scheduler_id` ASC),
  CONSTRAINT `fk1`
    FOREIGN KEY (`scheduler_id`)
    REFERENCES `orderdb`.`scheduler` (`scheduler_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `orderdb`.`orders`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `orderdb`.`orders` ;

CREATE TABLE IF NOT EXISTS `orderdb`.`orders` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `exp_id` INT NOT NULL DEFAULT 99999,
  `customer` VARCHAR(30) NOT NULL,
  `address` INT(3) NULL DEFAULT NULL,
  `orderdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `red` INT(11) NULL DEFAULT NULL,
  `green` INT(11) NULL DEFAULT NULL,
  `blue` INT(11) NULL DEFAULT NULL,
  `fulfilled_red` INT(11) NULL DEFAULT '0',
  `fulfilled_green` INT(11) NULL DEFAULT '0',
  `fulfilled_blue` INT(11) NULL DEFAULT '0',
  `required_red` INT(11) NULL DEFAULT NULL,
  `required_green` INT(11) NULL DEFAULT NULL,
  `required_blue` INT(11) NULL DEFAULT NULL,
  `pending` TINYINT(1) NULL DEFAULT '1',
  `filldate` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `total_item` INT(11) NULL DEFAULT 0,
  PRIMARY KEY (`id`, `exp_id`),
  INDEX `fk_orders_experiment_idx` (`exp_id` ASC),
  CONSTRAINT `fk_orders_experiment`
    FOREIGN KEY (`exp_id`)
    REFERENCES `orderdb`.`experiment` (`exp_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=latin1;


-- -----------------------------------------------------
-- Table `orderdb`.`scheduling`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `orderdb`.`scheduling` ;

CREATE TABLE IF NOT EXISTS `orderdb`.`scheduling` (
  `scheduling_id` INT NOT NULL AUTO_INCREMENT,
  `scheduler_id` INT NOT NULL,
  `exp_id` INT NOT NULL,
  `start_time` timestamp NULL DEFAULT NULL,
  `end_time` timestamp NULL DEFAULT NULL,  
  `total_comp_time` INT(11) NULL,
  `num_order` INT(11) NULL,
  `num_item` INT(5) NULL,
  `comp_time_per_order` FLOAT(11) NULL DEFAULT NULL,
  PRIMARY KEY (`scheduling_id`),
  INDEX `fk1_idx` (`scheduler_id` ASC),
  INDEX `fk2_idx` (`exp_id` ASC),
  CONSTRAINT `fk4`
    FOREIGN KEY (`scheduler_id`)
    REFERENCES `orderdb`.`scheduler` (`scheduler_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk5`
    FOREIGN KEY (`exp_id`)
    REFERENCES `orderdb`.`experiment` (`exp_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=latin1;


-- -----------------------------------------------------
-- Table `orderdb`.`departure`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `orderdb`.`departure` ;

CREATE TABLE IF NOT EXISTS `orderdb`.`departure` (
  `departure_id` INT(5) NOT NULL AUTO_INCREMENT,
  `exp_id` INT NOT NULL,
  `depart_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `arrive_time` timestamp NULL DEFAULT '0000-00-00 00:00:00',
  `travel_time` INT(5) NULL DEFAULT NULL,
  `num_order` INT(3) NULL DEFAULT 0 COMMENT '한번 LZ를 떠나서 다시 돌아오기까지 완료시킨 주문의 수. \n',
  `num_item` INT(3) NULL DEFAULT 0,
  `total_profit` FLOAT(11) NULL DEFAULT 0.0,
  PRIMARY KEY (`departure_id`),
  CONSTRAINT `fk6`
    FOREIGN KEY (`exp_id`)
    REFERENCES `orderdb`.`experiment` (`exp_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;



-- -----------------------------------------------------
-- Table `orderdb`.`timestamp_loading`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `orderdb`.`timestamp_loading` ;

CREATE TABLE IF NOT EXISTS `orderdb`.`timestamp_loading` (
  `loading_id` INT NOT NULL AUTO_INCREMENT,
  `exp_id` INT NOT NULL,
  `num_item` INT(4) NOT NULL,
  `refresh_alert_time` timestamp NULL DEFAULT NULL COMMENT 'UI 갱신신호 주는 시점',
  `connect_time` timestamp NULL DEFAULT NULL COMMENT '로딩워커UI 접속 시점',
  `confirm_time` timestamp NULL DEFAULT NULL COMMENT 'confirm 누르는 시점',
  `avg_loading_time_per_item` FLOAT(5) NULL DEFAULT NULL,
  PRIMARY KEY (`loading_id`),
  CONSTRAINT `fk7`
    FOREIGN KEY (`exp_id`)
    REFERENCES `orderdb`.`experiment` (`exp_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `orderdb`.`timestamp_unloading`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `orderdb`.`timestamp_unloading` ;

CREATE TABLE IF NOT EXISTS `orderdb`.`timestamp_unloading` (
  `unloading_id` INT NOT NULL AUTO_INCREMENT,
  `exp_id` INT NOT NULL,
  `num_item` INT(4) NOT NULL,
  `refresh_alert_time` timestamp NULL DEFAULT NULL COMMENT 'UI 갱신신호 주는 시점',
  `connect_time` timestamp NULL DEFAULT NULL COMMENT '언로딩워커UI 접속 시점',
  `confirm_time` timestamp NULL DEFAULT NULL COMMENT 'confirm 누르는 시점',
  `avg_unloading_time_per_item` FLOAT(5) NULL DEFAULT NULL,
  PRIMARY KEY (`unloading_id`),
  CONSTRAINT `fk8`
    FOREIGN KEY (`exp_id`)
    REFERENCES `orderdb`.`experiment` (`exp_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
) ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `orderdb`.`pending`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `orderdb`.`pending` ;

CREATE TABLE IF NOT EXISTS `orderdb`.`pending` (
  `time_point` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `exp_id` INT NOT NULL,
  `num_pending` INT(11) NOT NULL DEFAULT 0 COMMENT '주기적으로 pending 오더 수 insert 하도록 event scheduler 넣어야함',
  PRIMARY KEY (`time_point`),
  CONSTRAINT `fk9`
    FOREIGN KEY (`exp_id`)
    REFERENCES `orderdb`.`experiment` (`exp_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `orderdb`.`M_mode` (
  `mmode_id` INT NOT NULL AUTO_INCREMENT,
  `exp_id` INT NOT NULL,
  `start_time` TIMESTAMP NULL,
  `end_time` TIMESTAMP NULL,
  `error_type` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`mmode_id`),
  INDEX `fk10_idx` (`exp_id` ASC),
  CONSTRAINT `fk10`
    FOREIGN KEY (`exp_id`)
    REFERENCES `orderdb`.`experiment` (`exp_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;



USE `orderdb`;

DELIMITER $$

USE `orderdb`$$
DROP TRIGGER IF EXISTS `orderdb`.`experiment_BEFORE_UPDATE` $$
USE `orderdb`$$
CREATE DEFINER = CURRENT_USER TRIGGER `orderdb`.`experiment_BEFORE_UPDATE` BEFORE UPDATE ON `experiment` FOR EACH ROW
BEGIN
	IF NEW.end_time IS NOT NULL THEN 
		IF (SELECT SUM(num_item) FROM timestamp_unloading as tu WHERE tu.exp_id = NEW.exp_id) = 
			(SELECT SUM(total_item) FROM orders WHERE orders.exp_id = NEW.exp_id) THEN
			SET NEW.reliability = 1;
		END IF;
	END IF; 
END$$


USE `orderdb`$$
DROP TRIGGER IF EXISTS `orderdb`.`orders_BEFORE_INSERT` $$
USE `orderdb`$$
CREATE DEFINER = CURRENT_USER TRIGGER `orderdb`.`orders_BEFORE_INSERT` BEFORE INSERT ON `orders` FOR EACH ROW
BEGIN
	SET NEW.required_red = new.red;
	SET NEW.required_green = new.green;
	SET NEW.required_blue = new.blue;
	SET NEW.total_item = NEW.red + NEW.green + NEW.blue;
	SET NEW.exp_id = (SELECT MAX(exp_id) FROM experiment);
END$$

USE `orderdb`$$
DROP TRIGGER IF EXISTS `orderdb`.`m_mode_BEFORE_INSERT` $$
USE `orderdb`$$
CREATE DEFINER = CURRENT_USER TRIGGER `orderdb`.`m_mode_BEFORE_INSERT` BEFORE INSERT ON `m_mode` FOR EACH ROW
BEGIN
	SET NEW.exp_id = (SELECT MAX(exp_id) FROM experiment);
END$$

USE `orderdb`$$
DROP TRIGGER IF EXISTS `orderdb`.`orders_BEFORE_UPDATE` $$
USE `orderdb`$$
CREATE DEFINER = CURRENT_USER TRIGGER `orderdb`.`orders_BEFORE_UPDATE` BEFORE UPDATE ON `orders` FOR EACH ROW
BEGIN
		SET NEW.required_red = OLD.red - NEW.fulfilled_red;
		SET NEW.required_green = OLD.green - NEW.fulfilled_green;
		SET NEW.required_blue = OLD.blue - NEW.fulfilled_blue;
		
        IF OLD.red = NEW.fulfilled_red AND OLD.green = NEW.fulfilled_green AND OLD.blue = NEW.fulfilled_blue THEN 
			SET NEW.pending = 0, NEW.filldate = CURRENT_TIMESTAMP;
		END IF;        
END$$


USE `orderdb`$$
DROP TRIGGER IF EXISTS `orderdb`.`scheduling_BEFORE_INSERT` $$
USE `orderdb`$$
CREATE DEFINER = CURRENT_USER TRIGGER `orderdb`.`scheduling_BEFORE_INSERT` BEFORE INSERT ON `scheduling` FOR EACH ROW
BEGIN
	SET NEW.total_comp_time = TIMESTAMPDIFF(SECOND, NEW.start_time, NEW.end_time);
	SET NEW.comp_time_per_order = NEW.total_comp_time / NEW.num_order;
    SET NEW.exp_id = (SELECT MAX(exp_id) FROM experiment);
END;$$


USE `orderdb`$$
DROP TRIGGER IF EXISTS `orderdb`.`timestamp_loading_BEFORE_INSERT` $$
USE `orderdb`$$
CREATE DEFINER = CURRENT_USER TRIGGER `orderdb`.`timestamp_loading_BEFORE_INSERT` BEFORE INSERT ON `timestamp_loading` FOR EACH ROW
BEGIN
	SET NEW.exp_id = (SELECT MAX(exp_id) FROM experiment);
	SET NEW.avg_loading_time_per_item = (TIMESTAMPDIFF(SECOND, NEW.connect_time, NEW.confirm_time) / NEW.num_item);

END;$$


USE `orderdb`$$
DROP TRIGGER IF EXISTS `orderdb`.`timestamp_unloading_BEFORE_INSERT` $$
USE `orderdb`$$
CREATE DEFINER = CURRENT_USER TRIGGER `orderdb`.`timestamp_unloading_BEFORE_INSERT` BEFORE INSERT ON `timestamp_unloading` FOR EACH ROW
BEGIN
	SET NEW.exp_id = (SELECT MAX(exp_id) FROM experiment);
	SET NEW.avg_unloading_time_per_item = (TIMESTAMPDIFF(SECOND, NEW.connect_time, NEW.confirm_time) / NEW.num_item);

END;$$


USE `orderdb`$$
DROP TRIGGER IF EXISTS `orderdb`.`pending_BEFORE_INSERT` $$
USE `orderdb`$$
CREATE DEFINER = CURRENT_USER TRIGGER `orderdb`.`pending_BEFORE_INSERT` BEFORE INSERT ON `pending` FOR EACH ROW
BEGIN
	SET NEW.exp_id = (SELECT MAX(exp_id) FROM experiment);
END;$$

USE `orderdb`$$
DROP TRIGGER IF EXISTS `orderdb`.`departure_BEFORE_INSERT` $$
USE `orderdb`$$
CREATE DEFINER = CURRENT_USER TRIGGER `orderdb`.`departure_BEFORE_INSERT` BEFORE INSERT ON `departure` FOR EACH ROW
BEGIN
	SET NEW.exp_id = (SELECT MAX(exp_id) FROM experiment);
    SET NEW.travel_time = TIMESTAMPDIFF(SECOND, NEW.depart_time, NEW.arrive_time);
END;$$

DELIMITER ;
/*
SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
*/
INSERT INTO scheduler (comment) VALUES ('test');