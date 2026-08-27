CREATE USER 'mcp_analytics'@'%' IDENTIFIED BY '1029384756Liza';
GRANT SELECT ON trend_tracking_sample.* TO 'mcp_analytics'@'%';
FLUSH PRIVILEGES;