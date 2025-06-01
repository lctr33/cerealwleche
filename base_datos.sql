-- MySQL dump 10.13  Distrib 8.0.41, for Linux (aarch64)
--
-- Host: localhost    Database: streaming
-- ------------------------------------------------------
-- Server version	8.0.41-0ubuntu0.24.10.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `Clientes`
--

DROP TABLE IF EXISTS `Clientes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Clientes` (
  `id_cliente` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(255) NOT NULL,
  `numero_tel` varchar(15) DEFAULT NULL,
  PRIMARY KEY (`id_cliente`)
) ENGINE=InnoDB AUTO_INCREMENT=55 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Clientes`
--

LOCK TABLES `Clientes` WRITE;
/*!40000 ALTER TABLE `Clientes` DISABLE KEYS */;
INSERT INTO `Clientes` VALUES (1,'alicia cañedo','5578626219'),(2,'jafet','messenger'),(3,'lizeth','messenger'),(4,'fercho','9611127588'),(5,'tita','ninguno'),(6,'ramiro','messenger'),(7,'aljrn','7772236786'),(8,'alex','5530425456'),(9,'amigo montesillo','ninguno'),(10,'yulidia peña','messenger'),(11,'monica_clienta','7775072604'),(12,'aislin','7771923497'),(13,'oh la lau','messenger'),(14,'cliente mama ','ninguno'),(15,'adriana','ninguno'),(16,'isa','ninguno'),(17,'montesillo','ninguno'),(18,'pablo','ninguno'),(19,'king','9373855357'),(20,'paulina','777 410 7912'),(21,'fernando','7775477459'),(22,'rodri','7775034432'),(23,'jetzibeth','messenger'),(24,'elizabeth efh','729 746 1871'),(25,'monica_clienta','777 507 2604'),(26,'angel','777 866 5882'),(27,'amor','7774696914'),(28,'daniela','messenger'),(29,'clienta sin nombre','7772496881'),(30,'cliente mama ','777 334 6421'),(31,'luis ramirez','messenger'),(32,'carlos','3312295148'),(33,'mariana','7343493399'),(34,'aldo','55114444292'),(35,'silvio','messenger'),(36,'edgar','messenger'),(37,'barrios','ninguno'),(38,'acua-met','7772408865'),(39,'angel lalo','618 838 2821'),(40,'jair','messenger'),(41,'hoby','4461311218'),(42,'flavio','messenger'),(43,'dan salinas','messenger'),(44,'amor ','7773759396'),(45,'jared ','7778279386'),(46,'bruno','7776317669'),(47,'jose','7775512235'),(48,'victor peres','7714866483'),(49,'oswaldo','messenger'),(50,'jane diaz','messenger'),(51,'sin nombre','7771972687'),(52,'amor','7773759396'),(53,'manuel porras','527352474812'),(54,'charly','3312295148');
/*!40000 ALTER TABLE `Clientes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Cuentas_Streaming`
--

DROP TABLE IF EXISTS `Cuentas_Streaming`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Cuentas_Streaming` (
  `id_cuenta` int NOT NULL AUTO_INCREMENT,
  `id_cliente` int NOT NULL,
  `id_servicio` int NOT NULL,
  `id_vendedor` int DEFAULT NULL,
  `tiempo_contratado` varchar(250) DEFAULT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_final` date NOT NULL,
  `activo` tinyint(1) DEFAULT '1',
  `desea_renovar` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id_cuenta`),
  KEY `id_cliente` (`id_cliente`),
  KEY `id_servicio` (`id_servicio`),
  CONSTRAINT `Cuentas_Streaming_ibfk_1` FOREIGN KEY (`id_cliente`) REFERENCES `Clientes` (`id_cliente`),
  CONSTRAINT `Cuentas_Streaming_ibfk_2` FOREIGN KEY (`id_servicio`) REFERENCES `Servicios_Streaming` (`id_servicio`)
) ENGINE=InnoDB AUTO_INCREMENT=74 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Cuentas_Streaming`
--

LOCK TABLES `Cuentas_Streaming` WRITE;
/*!40000 ALTER TABLE `Cuentas_Streaming` DISABLE KEYS */;
INSERT INTO `Cuentas_Streaming` VALUES (1,1,2,2,'1_año','2024-08-23','2025-08-23',1,1),(3,3,2,1,'3_meses','2025-02-09','2025-05-09',1,1),(4,4,2,1,'3_meses','2025-01-16','2025-04-16',1,1),(5,5,1,1,'1_año','2025-01-27','2026-01-27',1,1),(6,6,1,1,'1_año','2024-05-11','2025-05-11',1,1),(7,7,1,1,'6_meses','2024-09-17','2025-03-17',1,1),(8,8,1,1,'1_mes','2025-01-20','2025-02-20',1,1),(9,9,1,1,'3_meses','2024-12-12','2025-03-12',1,1),(11,8,3,1,'1_mes','2025-01-20','2025-02-20',1,1),(12,11,3,3,'1_mes','2025-01-23','2025-02-23',1,1),(14,13,3,1,'1_mes','2025-01-09','2025-02-09',1,1),(15,14,4,4,'1_año','2024-05-10','2025-05-10',1,1),(16,10,4,1,'1_año','2024-05-19','2025-05-19',1,1),(17,15,4,4,'1_año','2024-05-10','2025-05-10',1,1),(18,16,4,2,'1_año','2025-11-04','2026-11-04',1,1),(19,17,4,1,'1_año','2024-05-10','2025-05-10',1,1),(20,8,5,1,'1_mes','2025-01-20','2025-02-20',1,1),(21,15,5,4,'1_año','2024-06-07','2025-06-07',1,1),(22,18,5,2,'1_año','2024-05-21','2025-05-21',1,1),(23,19,5,1,'1_año','2024-09-01','2025-09-01',1,1),(24,20,6,2,'3_meses','2025-01-07','2025-04-07',1,1),(25,7,6,1,'1_año','2024-06-04','2025-06-04',1,1),(26,21,6,1,'1_año','2024-09-06','2025-09-06',1,1),(27,22,6,1,'1_año','2024-11-09','2025-11-09',1,1),(28,23,6,1,'1_año','2024-06-30','2025-06-30',1,1),(29,24,7,2,'1_año','2025-02-15','2026-02-15',1,1),(30,15,7,4,'1_año','2024-06-20','2025-06-20',1,1),(31,3,7,1,'1_año','2025-02-09','2026-02-09',1,1),(32,25,8,3,'1_año','2024-10-25','2025-10-25',1,1),(33,26,8,2,'3_meses','2025-01-07','2025-04-07',1,1),(34,22,8,1,'1_año','2024-09-11','2025-09-11',1,1),(35,27,8,1,'1_año','2024-07-21','2025-07-21',1,1),(36,1,9,2,'1_año','2024-06-21','2025-06-21',1,1),(37,28,9,1,'1_mes','2025-01-20','2025-02-20',1,1),(38,29,9,1,'3_meses','2024-12-09','2025-03-09',1,1),(39,30,9,4,'1_mes','2025-01-12','2025-02-12',1,1),(40,31,11,1,'1_año','2024-06-23','2025-06-23',1,1),(41,32,11,1,'1_año','2024-07-30','2025-07-30',1,1),(42,33,11,1,'1_año','2024-09-06','2025-09-06',1,1),(43,34,11,1,'1_año','2024-07-01','2025-07-01',1,1),(44,35,12,1,'3_meses','2025-01-30','2025-04-30',1,1),(46,29,12,1,'1_año','2024-11-17','2025-11-17',1,1),(48,11,13,3,'3_meses','2025-02-02','2025-05-02',1,1),(50,11,13,3,'1_año','2024-08-13','2025-08-13',1,1),(51,21,13,1,'1_año','2024-08-14','2025-08-14',1,1),(52,39,14,1,'1_año','2024-07-11','2025-07-11',1,1),(53,40,14,1,'1_año','2024-07-10','2025-07-10',1,1),(54,41,14,1,'1_año','2024-08-10','2025-08-10',1,1),(55,42,14,1,'1_año','2024-07-12','2025-07-12',1,1),(56,43,14,1,'1_año','2024-07-12','2025-07-12',1,1),(57,44,15,1,'1_año','2025-02-10','2026-02-10',1,1),(58,7,15,1,'1_mes','2025-03-02','2025-04-02',1,1),(60,46,16,1,'1_año','2024-07-18','2025-07-18',1,1),(61,47,16,1,'3_meses','2024-12-10','2025-03-10',1,1),(62,48,16,1,'1_año','2024-07-21','2025-07-21',1,1),(63,49,16,1,'1_año','2024-07-29','2025-07-29',1,1),(64,50,16,1,'1_año','2025-02-12','2026-02-12',1,1),(65,51,17,1,'1_año','2024-07-20','2025-07-20',1,1),(66,19,18,1,'1_mes','2025-01-22','2025-02-22',1,1),(67,52,18,1,'1_año','2025-02-13','2026-02-13',1,1),(68,22,18,1,'1_mes','2025-01-28','2025-02-28',1,1),(69,7,18,1,'1_mes','2025-03-19','2025-04-19',1,1),(70,11,13,3,'3_meses','2025-02-13','2025-05-13',1,1),(71,53,15,2,'1_mes','2025-02-17','2025-03-17',1,1),(72,21,18,1,'1_mes','2025-02-18','2025-03-18',1,1),(73,54,12,1,'1_mes','2025-02-20','2025-03-20',1,1);
/*!40000 ALTER TABLE `Cuentas_Streaming` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Historial_Clientes_Streaming`
--

DROP TABLE IF EXISTS `Historial_Clientes_Streaming`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Historial_Clientes_Streaming` (
  `id_historial` int NOT NULL AUTO_INCREMENT,
  `id_cliente` int NOT NULL,
  `nombre_cliente` varchar(255) NOT NULL,
  `id_servicio` int NOT NULL,
  `nombre_servicio` varchar(255) NOT NULL,
  `id_cuenta` int NOT NULL,
  `id_perfil` int DEFAULT NULL,
  `nombre_perfil` varchar(255) DEFAULT NULL,
  `alias_perfil` varchar(255) DEFAULT NULL,
  `tiempo_contratado` date NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_final` date NOT NULL,
  `id_vendedor` int DEFAULT NULL,
  `activo` tinyint(1) DEFAULT '1',
  `desea_renovar` tinyint(1) DEFAULT '1',
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_historial`),
  KEY `id_cliente` (`id_cliente`),
  KEY `id_servicio` (`id_servicio`),
  KEY `id_cuenta` (`id_cuenta`),
  CONSTRAINT `Historial_Clientes_Streaming_ibfk_1` FOREIGN KEY (`id_cliente`) REFERENCES `Clientes` (`id_cliente`),
  CONSTRAINT `Historial_Clientes_Streaming_ibfk_2` FOREIGN KEY (`id_servicio`) REFERENCES `Servicios_Streaming` (`id_servicio`),
  CONSTRAINT `Historial_Clientes_Streaming_ibfk_3` FOREIGN KEY (`id_cuenta`) REFERENCES `Cuentas_Streaming` (`id_cuenta`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Historial_Clientes_Streaming`
--

LOCK TABLES `Historial_Clientes_Streaming` WRITE;
/*!40000 ALTER TABLE `Historial_Clientes_Streaming` DISABLE KEYS */;
/*!40000 ALTER TABLE `Historial_Clientes_Streaming` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Perfiles_Streaming`
--

DROP TABLE IF EXISTS `Perfiles_Streaming`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Perfiles_Streaming` (
  `id_perfil` int NOT NULL AUTO_INCREMENT,
  `id_servicio` int NOT NULL,
  `id_cliente` int DEFAULT NULL,
  `nombre_perfil` varchar(255) NOT NULL,
  `alias_perfil` varchar(255) DEFAULT NULL,
  `pin_perfil` varchar(10) DEFAULT NULL,
  `libre` tinyint(1) DEFAULT NULL,
  `id_cuenta` int DEFAULT NULL,
  PRIMARY KEY (`id_perfil`),
  KEY `id_cliente` (`id_cliente`),
  KEY `id_servicio` (`id_servicio`),
  KEY `id_cuenta` (`id_cuenta`),
  CONSTRAINT `id_cuenta` FOREIGN KEY (`id_cuenta`) REFERENCES `Cuentas_Streaming` (`id_cuenta`),
  CONSTRAINT `Perfiles_Streaming_ibfk_1` FOREIGN KEY (`id_cliente`) REFERENCES `Clientes` (`id_cliente`),
  CONSTRAINT `Perfiles_Streaming_ibfk_2` FOREIGN KEY (`id_servicio`) REFERENCES `Servicios_Streaming` (`id_servicio`)
) ENGINE=InnoDB AUTO_INCREMENT=103 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Perfiles_Streaming`
--

LOCK TABLES `Perfiles_Streaming` WRITE;
/*!40000 ALTER TABLE `Perfiles_Streaming` DISABLE KEYS */;
INSERT INTO `Perfiles_Streaming` VALUES (1,1,5,'perfil 1','sil','1212',0,5),(2,1,6,'perfil 2','perfil 1','1596',0,6),(3,1,7,'perfil 3','perfil 2','1111',0,7),(4,1,8,'perfil 4','perfil 3','1234',0,8),(5,1,9,'perfil 5','perfil 4','1234',0,9),(6,2,1,'Perfil 1','ninguno','5555',0,1),(7,2,NULL,'Perfil 2',NULL,'2343',1,NULL),(8,2,NULL,'Perfil 3',NULL,NULL,1,NULL),(9,2,3,'Perfil 4','noodle','3223',0,3),(10,2,4,'Perfil 5','ninguno','5555',0,4),(11,3,NULL,'perfil 1',NULL,'1212',1,NULL),(12,3,8,'perfil 2','ninguno','2323',0,11),(13,3,11,'perfil 3','ninguno','1111',0,12),(14,3,NULL,'perfil 4',NULL,'6969',1,NULL),(15,3,13,'perfil 5','oh la lau','5252',0,14),(16,3,NULL,'Perfil 6',NULL,NULL,1,NULL),(17,4,14,'perfil 1','ninguno','ninguno',0,15),(18,4,10,'perfil 2','ninguno','ninguno',0,16),(19,4,15,'perfil 3','ninguno','ninguno',0,17),(20,4,16,'perfil 4','vilchis','ninguno',0,18),(21,4,17,'perfil 5','ninguno','ninguno',0,19),(22,5,8,'perfil 1','ninguno','12122',0,20),(23,5,15,'perfil 2','ninguno','ninguno',0,21),(24,5,NULL,'Perfil 3',NULL,'44444',1,NULL),(25,5,18,'perfil 4','pablo','ninguno',0,22),(26,5,19,'perfil 5','king','ninguno',0,23),(27,5,NULL,'Perfil 6',NULL,'66666',1,NULL),(28,6,20,'perfil 1','ninguno','ninguno',0,24),(29,6,7,'perfil 2','ninguno','ninguno',0,25),(30,6,21,'perfil 3','ninguno','ninguno',0,26),(31,6,22,'perfil 4','ninguno','ninguno',0,27),(32,6,23,'perfil 5','ninguno','ninguno',0,28),(33,7,NULL,'Perfil 1',NULL,'21212',1,NULL),(34,7,24,'perfil 2','ninguno','33333',0,29),(35,7,NULL,'Perfil 3',NULL,'75485',1,NULL),(36,7,NULL,'Perfil 4',NULL,'42424',1,NULL),(37,7,15,'perfil 5','ninguno','ninguno',0,30),(38,7,3,'perfil 6','noodle','66666',0,31),(39,8,25,'perfil 1','ninguno','23456',0,32),(40,8,26,'perfil 2','ninguno','12345',0,33),(41,8,NULL,'Perfil 3',NULL,'44444',1,NULL),(42,8,NULL,'Perfil 4',NULL,NULL,1,NULL),(43,8,22,'perfil 5','ninguno','12321',0,34),(44,8,27,'perfil 6','mel','12345',0,35),(45,9,1,'perfil 1','ninguno','5555',0,36),(46,9,28,'perfil 2','ninguno','ninguno',0,37),(47,9,29,'perfil 3','RENE','1234',0,38),(48,9,30,'perfil 4','ninguno','1221',0,39),(49,9,NULL,'Perfil 5',NULL,'3454',1,NULL),(50,10,NULL,'Perfil 1',NULL,NULL,1,NULL),(51,10,NULL,'Perfil 2',NULL,NULL,1,NULL),(52,10,NULL,'Perfil 3',NULL,NULL,1,NULL),(53,10,NULL,'Perfil 4',NULL,NULL,1,NULL),(54,10,NULL,'Perfil 5',NULL,NULL,1,NULL),(55,11,NULL,'Perfil 1',NULL,NULL,1,NULL),(56,11,31,'perfil 2','perfil 2','ninguno',0,40),(57,11,32,'perfil 3','ninguno','ninguno',0,41),(58,11,33,'perfil 4','ninguno','ninguno',0,42),(59,11,34,'perfil 5','ninguno','ninguno',0,43),(60,12,35,'perfil 1','ninguno','2323',0,44),(61,12,54,'perfil 2','ninguno','5645',0,73),(62,12,NULL,'perfil 3',NULL,'2332',1,NULL),(63,12,29,'perfil 4','ninguno','8888',0,46),(64,12,NULL,'perfil 5',NULL,'3456',1,NULL),(65,13,NULL,'Perfil 1',NULL,'15963',1,NULL),(66,13,11,'perfil 2','natalia','12345',0,48),(67,13,NULL,'perfil 3',NULL,'15963',1,NULL),(68,13,11,'perfil 4','gregorio','11111',0,50),(69,13,11,'perfil 5','','66666',0,70),(70,13,21,'perfil 6','fer','111111',0,51),(71,14,39,'perfil 1','angel','ninguno',0,52),(72,14,40,'perfil 2','Demzy','ninguno',0,53),(73,14,41,'perfil 3','hoby','ninguno',0,54),(74,14,42,'perfil 4','flavio','ninguno',0,55),(75,14,43,'perfil 5','dan ','ninguno',0,56),(76,15,44,'perfil 1','mel','1111',0,57),(77,15,53,'perfil 2','ninguno','3333',0,71),(78,15,7,'perfil 3','ninguno','5555',0,58),(79,15,NULL,'perfil 4',NULL,'2346',1,NULL),(80,15,NULL,'Perfil 5',NULL,'1596',1,NULL),(81,15,NULL,'Perfil 6',NULL,'7777',1,NULL),(82,16,46,'perfil 1','principal','ninguno',0,60),(83,16,47,'perfil 2','ninguno','ninguno',0,61),(84,16,48,'perfil 3','ninguno','ninguno',0,62),(85,16,49,'perfil 4','ninguno','ninguno',0,63),(86,16,50,'perfil 5','ninguno','ninguno',0,64),(87,17,51,'perfil 1','ninguno','11111',0,65),(88,17,NULL,'Perfil 2',NULL,'33333',1,NULL),(89,17,NULL,'Perfil 3',NULL,'99999',1,NULL),(90,17,NULL,'Perfil 4',NULL,'77777',1,NULL),(91,17,NULL,'Perfil 5',NULL,'66666',1,NULL),(92,17,NULL,'Perfil 6',NULL,'22222',1,NULL),(93,18,19,'perfil 1','king','1212',0,66),(94,18,52,'perfil 2','mel','1221',0,67),(95,18,22,'perfil 3','perfil 1','1596',0,68),(96,18,7,'perfil 4','mike','1316',0,69),(97,18,21,'perfil 5','perfil 4','9345',0,72),(98,19,NULL,'Perfil 1',NULL,NULL,1,NULL),(99,19,NULL,'Perfil 2',NULL,NULL,1,NULL),(100,19,NULL,'Perfil 3',NULL,NULL,1,NULL),(101,19,NULL,'Perfil 4',NULL,NULL,1,NULL),(102,19,NULL,'Perfil 5',NULL,NULL,1,NULL);
/*!40000 ALTER TABLE `Perfiles_Streaming` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Servicios_Streaming`
--

DROP TABLE IF EXISTS `Servicios_Streaming`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Servicios_Streaming` (
  `id_servicio` int NOT NULL AUTO_INCREMENT,
  `nombre_servicio` varchar(255) NOT NULL,
  `correo_asociado` varchar(255) NOT NULL,
  `contraseña` varchar(255) NOT NULL,
  PRIMARY KEY (`id_servicio`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Servicios_Streaming`
--

LOCK TABLES `Servicios_Streaming` WRITE;
/*!40000 ALTER TABLE `Servicios_Streaming` DISABLE KEYS */;
INSERT INTO `Servicios_Streaming` VALUES (1,'max','amarobryan31@gmail.com','Maxcuenta@10'),(2,'max','bryan.amaro.vaz.afk@gmail.com','Maxcuenta@123'),(3,'disney_standar','bryan.amaro.vaz@gmail.com','disneycuenta@03'),(4,'crunchyroll','amarobryan31@gmail.com','Crunchyroll@03'),(5,'prime_video','strimingmx01@gmail.com','Amazon@0909'),(6,'vix','strimingmx01@gmail.com','Cuentavix@12'),(7,'prime_video','amarobryan32@gmail.com','Amazon@123'),(8,'prime_video','amarobryan31@gmail.com','cuentaamazon@12'),(9,'max','amarobryan909@gmail.com','cuentamax@09'),(10,'crunchyroll','bryan.amaro.vaz@gmail.com','crunchyroll@12'),(11,'crunchyroll','amarobryan32@gmail.com','Crunchyroll@12345'),(12,'max','am2516102@gmail.com','Maxcuenta@07'),(13,'prime_video','amarobryan59@gmail.com','Amazon@321'),(14,'crunchyroll','amarobryan59@gmail.com','crunchyroll@123'),(15,'disney_premium','amarobryan909@gmail.com','cuentadisney@15'),(16,'crunchyroll','amarobryan12@gmail.com','Crunchyroll@12'),(17,'prime_video','amarobryan12@gmail.com','Amazon@1234'),(18,'netflix','amarobryan59@gmail.com','netflix@0909'),(19,'paramount','amarobryan59@gmail.com','paramunt@12');
/*!40000 ALTER TABLE `Servicios_Streaming` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Vendedores`
--

DROP TABLE IF EXISTS `Vendedores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Vendedores` (
  `id_vendedor` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(255) NOT NULL,
  `numero_tel` varchar(15) DEFAULT NULL,
  PRIMARY KEY (`id_vendedor`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Vendedores`
--

LOCK TABLES `Vendedores` WRITE;
/*!40000 ALTER TABLE `Vendedores` DISABLE KEYS */;
INSERT INTO `Vendedores` VALUES (1,'bryan','5646404427'),(2,'amor','7773759396'),(3,'monica_clienta','7775072604'),(4,'mama','7774696914');
/*!40000 ALTER TABLE `Vendedores` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-05-18 15:36:21
