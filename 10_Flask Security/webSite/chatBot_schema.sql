START TRANSACTION;
CREATE TABLE IF NOT EXISTS `role` (
	`id`	INTEGER NOT NULL AUTO_INCREMENT,
	`name`	VARCHAR(80) NOT NULL,
	`description`	VARCHAR(255),
	`permissions`	TEXT,
	PRIMARY KEY(`id`),
	UNIQUE(`name`)
);
CREATE TABLE IF NOT EXISTS `user` (
	`id`	VARCHAR(255) NOT NULL,
	`fs_uniquifier`	VARCHAR(64),
	`email`	VARCHAR(80) NOT NULL,
	`password`	VARCHAR(255),
	`name`	VARCHAR(80),
	`lineId`	VARCHAR(80),
	PRIMARY KEY(`id`),
	UNIQUE(`email`),
	`active`	BOOLEAN,
	CHECK(`active` IN (0, 1))
);
CREATE TABLE IF NOT EXISTS `roles_users` (
	`user_id`	VARCHAR(255),
	`role_id`	INTEGER,
	FOREIGN KEY(`role_id`) REFERENCES `role`(`id`),
	FOREIGN KEY(`user_id`) REFERENCES `user`(`id`)
);
INSERT INTO `role` VALUES (1,'admin',NULL,'admin-read,admin-write,admin-read,admin-write');
INSERT INTO `role` VALUES (2,'manager',NULL,'manager-read,manager-write');
INSERT INTO `role` VALUES (3,'customer',NULL,'customer-read,customer-write');

COMMIT;
