-- Q1 requests per intent

-- Q2 average latency per intent
SELECT intent,
       ROUND(AVG(latency_ms), 1) AS avg_latency_ms
FROM interaction
GROUP BY intent
ORDER BY avg_latency_ms DESC, intent;

-- Q3 topics with the most thumbs-down (JOIN feedback with interaction)
SELECT i.topic,
       COUNT(*) AS thumbs_down
FROM interaction i
JOIN feedback f ON f.request_id = i.request_id
WHERE f.rating = -1
  AND i.topic IS NOT NULL
GROUP BY i.topic
ORDER BY thumbs_down DESC, i.topic;
