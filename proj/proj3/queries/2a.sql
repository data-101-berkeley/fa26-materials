DROP VIEW IF EXISTS labeled_data;
CREATE VIEW labeled_data AS

SELECT 'YOUR CODE HERE';

(SELECT * FROM labeled_data WHERE is_outlier ORDER BY time, id LIMIT 50)
UNION ALL
(SELECT * FROM labeled_data WHERE NOT is_outlier ORDER BY time, id LIMIT 50);
