CREATE DATABASE IF NOT EXISTS smart_learning_portfolio
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'smart_learning_app'@'localhost'
  IDENTIFIED BY 'change-this-password';

GRANT ALL PRIVILEGES ON smart_learning_portfolio.*
  TO 'smart_learning_app'@'localhost';

FLUSH PRIVILEGES;
