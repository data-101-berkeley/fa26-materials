DROP VIEW IF EXISTS cleaned_data;
CREATE VIEW cleaned_data AS

SELECT 'YOUR CODE HERE';

(SELECT * FROM cleaned_data WHERE is_outlier ORDER BY time, id LIMIT 50)
UNION ALL
(SELECT * FROM cleaned_data WHERE NOT is_outlier ORDER BY time, id LIMIT 50);
