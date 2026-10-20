DROP VIEW IF EXISTS backward;
CREATE VIEW backward AS
SELECT 'YOUR CODE HERE';

SELECT * FROM backward WHERE run_size > 2 ORDER BY id, run, run_rank LIMIT 100;
