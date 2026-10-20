DROP VIEW IF EXISTS likely_data;
CREATE VIEW likely_data AS
SELECT 'YOUR CODE HERE';

SELECT * FROM likely_data WHERE run_size > 2 ORDER BY id, time LIMIT 100;
