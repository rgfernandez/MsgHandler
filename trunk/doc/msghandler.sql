-- MySQL Administrator dump 1.4
--
-- ------------------------------------------------------
-- Server version	5.1.30


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;


--
-- Create schema msghandler
--

CREATE DATABASE IF NOT EXISTS msghandler;
USE msghandler;

--
-- Definition of table `msghandler`.`attachments`
--

DROP TABLE IF EXISTS `msghandler`.`attachments`;
CREATE TABLE  `msghandler`.`attachments` (
  `uuid` varchar(23) NOT NULL,
  `name` text,
  `content` longblob
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Definition of table `msghandler`.`contents`
--

DROP TABLE IF EXISTS `msghandler`.`contents`;
CREATE TABLE  `msghandler`.`contents` (
  `uuid` varchar(23) NOT NULL,
  `contact` text,
  `body` longtext
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Definition of table `msghandler`.`headers`
--

DROP TABLE IF EXISTS `msghandler`.`headers`;
CREATE TABLE  `msghandler`.`headers` (
  `uuid` varchar(23) NOT NULL,
  `field` text,
  `value` text
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Definition of table `msghandler`.`responses`
--

DROP TABLE IF EXISTS `msghandler`.`responses`;
CREATE TABLE  `msghandler`.`responses` (
  `keyword` text NOT NULL,
  `language` text,
  `mode` text,
  `response` text
) ENGINE=MyISAM DEFAULT CHARSET=utf8;


/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
