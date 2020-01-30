-- MySQL dump 10.13  Distrib 8.0.11, for osx10.13 (x86_64)
--
-- Host: localhost    Database: orderdb
-- ------------------------------------------------------
-- Server version	8.0.11

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
 SET NAMES utf8mb4 ;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `orders` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `customer` varchar(30) NOT NULL,
  `address` int(3) DEFAULT NULL,
  `orderdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  `red` int(11) DEFAULT NULL,
  `green` int(11) DEFAULT NULL,
  `blue` int(11) DEFAULT NULL,
  `fulfilled_red` int(11) DEFAULT 0,
  `fulfilled_green` int(11) DEFAULT 0,
  `fulfilled_blue` int(11) DEFAULT 0,
  `required_red` int(11) DEFAULT NULL,
  `required_green` int(11) DEFAULT NULL,
  `required_blue` int(11) DEFAULT NULL,
  `pending` tinyint(1) DEFAULT 0,
  `filldate` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00' ,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=latin1;

delimiter //
CREATE TRIGGER insert_trigger BEFORE INSERT ON orders
       FOR EACH ROW
       BEGIN
		SET NEW.required_red = new.red;
		SET NEW.required_green = new.green;
		SET NEW.required_blue = new.blue;
	   END;//
delimiter ;

delimiter //
CREATE TRIGGER update_trigger BEFORE UPDATE ON orders
       FOR EACH ROW
       BEGIN
		SET NEW.required_red = OLD.red - NEW.fulfilled_red;
		SET NEW.required_green = OLD.green - NEW.fulfilled_green;
		SET NEW.required_blue = OLD.blue - NEW.fulfilled_blue;
		
        IF OLD.red = NEW.fulfilled_red AND OLD.green = NEW.fulfilled_green AND OLD.blue = NEW.fulfilled_blue THEN 
			SET NEW.pending = 0, NEW.filldate = CURRENT_TIMESTAMP;
		END IF;        
	   END;//
delimiter ;

/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-11-04 18:39:15
