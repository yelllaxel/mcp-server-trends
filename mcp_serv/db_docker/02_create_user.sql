CREATE USER 'mcp_analytics'@'%' IDENTIFIED BY '1029384756Liza';
CREATE USER 'mcp_analytics'@'localhost' IDENTIFIED BY '1029384756Liza';
GRANT SELECT ON trend_tracking_sample.* TO 'mcp_analytics'@'%';
GRANT SELECT ON trend_tracking_sample.* TO 'mcp_analytics'@'localhost';
FLUSH PRIVILEGES;