--hot_picks_most_voted_polls:

--most voted poll yesterday ranks
SELECT a.*, b.question, b.createdBy AS featuredUser
FROM (
    SELECT 
        date(v.createdAt) AS date, 
        pollId, 
        COUNT(*) AS total_votes,
        RANK() OVER (ORDER BY COUNT(*) DESC) AS rank 
    FROM `firestore_hunch_views.votes` v 
    LEFT JOIN `firestore_hunch_views.users` u ON v.createdBy = u.email
    WHERE 
        date(v.createdAt) = DATE_SUB(current_date, INTERVAL 1 DAY) 
        AND u.isDeleted = false
        AND u.countryGroup = "GROUP_IN"
        AND pollId NOT IN (
            SELECT DISTINCT pollId 
            FROM `firestore_hunch_views.options`
            WHERE 
                (options_text LIKE ('%comment%') OR options_text LIKE ('%LMK%') OR options_text LIKE ('%other%'))
                OR CHAR_LENGTH(options_text) <= 5 AND optionsDisplayType = 'image'
        )
    GROUP BY 1, 2
    ORDER BY 4 ASC
    LIMIT 100
) a
LEFT JOIN (
    SELECT 
        id AS pollId, 
        question, 
        createdBy 
    FROM `firestore_hunch_views.polls`
    WHERE 
        isArchived IS NULL
        AND EXISTS (SELECT 1 FROM UNNEST(countryGroups) AS cG WHERE REPLACE(cG,'"','') = "GROUP_IN")
) b ON a.pollId = b.pollId;
  

------------------------------------------------------------------------------------------------

--hot_picks_most_liked_comment:

--most likes on a comment on yesterday ranks
SELECT 
    a.*, 
    b.userId AS featuredUser, 
    b.pollId, 
    b.text
FROM (
    SELECT 
        date(l.createdAt) AS date, 
        commentId, 
        count(id) AS total_likes,
        RANK() OVER (ORDER BY count(id) DESC) AS rank 
    FROM `hunch-prod-e1130.firestore_hunch_views.likes` l
    LEFT JOIN `firestore_hunch_views.users` u ON l.createdBy = u.email
    WHERE 
        date(l.createdAt) = DATE_SUB(current_date, INTERVAL 1 DAY) 
        AND u.isDeleted = false 
        AND l.isDeleted = false
        AND u.countryGroup = "GROUP_IN"
    GROUP BY 1, 2
    ORDER BY 3 DESC
    LIMIT 10
) a
LEFT JOIN `firestore_hunch_views.comments` b ON a.commentId = b.id
LEFT JOIN `firestore_hunch_views.polls` c ON b.pollId = c.id
WHERE 
    b.isDeleted = false
    AND b.pollId NOT IN (
        SELECT DISTINCT pollId 
        FROM `firestore_hunch_views.options`
        WHERE 
            (options_text LIKE ('%comment%') OR options_text LIKE ('%LMK%') OR options_text LIKE ('%other%'))
            OR CHAR_LENGTH(options_text) <= 5 AND optionsDisplayType = 'image'
    )
    AND EXISTS (SELECT 1 FROM UNNEST(countryGroups) AS cG WHERE REPLACE(cG,'"','') = "GROUP_IN")


------------------------------------------------------------------------------------------------

--top_comments_for_a_specific_poll:

SELECT
  l.commentId,
  COUNT(l.id) AS total_likes,
  c.text
FROM
  `hunch-prod-e1130.firestore_hunch_views.likes` l
JOIN
  `hunch-prod-e1130.firestore_hunch_views.comments` c
ON
  l.commentId = c.id
WHERE
  c.pollId = "bf729b35-7ae6-44f6-ab52-166866f5d4dd"
  AND c.isDeleted = FALSE
GROUP BY
  l.commentId, c.text
ORDER BY total_likes DESC

------------------------------------------------------------------------------------------------

--INDIA top_voted_polls_and_top_comments_for_each_of_these_polls:

WITH TopVotedPolls AS (
    -- First query to fetch top voted polls
    SELECT
        a.*, b.question, b.slug, b.createdBy AS pollCreator
    FROM (
        SELECT
            v.pollId,
            COUNT(*) AS total_votes,
            RANK() OVER (ORDER BY COUNT(*) DESC) AS pollRank
        FROM `partitioned_tables.votes_partition` v
        WHERE 
        -- DATE(v.createdAt) BETWEEN DATE_SUB(current_date, INTERVAL 7 DAY)
        --     AND DATE(current_date) AND 
            createdBy != "deleted_user"
        GROUP BY 1
        ORDER BY 3 ASC
        LIMIT 5
    ) a
    LEFT JOIN (
        SELECT * FROM `partitioned_tables.polls_partition`p
        LEFT JOIN (
            SELECT email FROM `partitioned_tables.users_partition`WHERE isDeleted = FALSE
        ) u ON p.createdBy = u.email
        WHERE p.createdBy != "product@hunch.in" AND p.id NOT IN (
            SELECT DISTINCT pollId FROM `partitioned_tables.options_partition`
            WHERE (LOWER(options_text) LIKE ('%comment%') OR LOWER(options_text) LIKE ('%lmk%')
            OR LOWER(options_text) LIKE ('%other%'))
            OR CHAR_LENGTH(options_text) <= 5 AND optionsDisplayType = 'image'
        )
        AND countryGroups = "GROUP_IN"
    ) b ON a.pollId = b.id
    WHERE b.isDeleted IS NULL -- AND DATE(endTime) > DATE_ADD(current_date, INTERVAL 7 DAY)
        AND displayType != 'image'
    ORDER BY total_votes DESC
    LIMIT 100
),
TopLikedComments AS (
    -- Second query to fetch top liked comments
    SELECT
        c.*, p.pollId AS parentPollId,
        ROW_NUMBER() OVER (PARTITION BY c.pollId ORDER BY c.likesCount DESC) AS commentRank
    FROM (
        SELECT
            c.id as commentId, text as comment, likesCount, pollId,
            RANK() OVER (PARTITION BY c.pollId ORDER BY c.likesCount DESC) AS rank
        FROM `partitioned_tables.comments_partition` c
        LEFT JOIN `partitioned_tables.users_partition` u ON c.userId = u.email
        WHERE c.isDeleted = FALSE AND u.isDeleted = FALSE
    ) c
    JOIN TopVotedPolls p ON c.pollId = p.pollId
    ORDER BY c.rank ASC)
SELECT p.pollId, total_votes, pollRank, slug, question, pollCreator, commentId, comment, likesCount, commentRank
FROM TopVotedPolls p
JOIN TopLikedComments c ON p.pollId = c.parentPollId
WHERE commentRank <= 10
ORDER BY p.pollRank ASC, c.commentRank ASC 

------------------------------------------------------------------------------------------------

--US top_voted_polls_and_top_comments_for_each_of_these_polls:

WITH TopVotedPolls AS (
    -- First query to fetch top voted polls
    SELECT
        a.*, b.question, b.slug, b.pollDuration, b.createdBy AS pollCreator
    FROM (
        SELECT
            v.pollId,
            COUNT(*) AS total_votes,
            RANK() OVER (ORDER BY COUNT(*) DESC) AS pollRank
        FROM `partitioned_tables.votes_partition` v
        WHERE 
        -- DATE(v.createdAt) BETWEEN DATE_SUB(current_date, INTERVAL 7 DAY)
        --     AND DATE(current_date) AND 
            createdBy != "deleted_user"
        GROUP BY 1
        ORDER BY 3 ASC
        -- LIMIT 100
    ) a
    LEFT JOIN (
        SELECT * FROM `partitioned_tables.polls_partition`p
        LEFT JOIN (
            SELECT email FROM `partitioned_tables.users_partition`WHERE isDeleted = FALSE
        ) u ON p.createdBy = u.email
        WHERE p.createdBy != "product@hunch.in" AND p.id NOT IN (
            SELECT DISTINCT pollId FROM `partitioned_tables.options_partition`
            WHERE (LOWER(options_text) LIKE ('%comment%') OR LOWER(options_text) LIKE ('%lmk%')
            OR LOWER(options_text) LIKE ('%other%'))
            OR CHAR_LENGTH(options_text) <= 5 AND optionsDisplayType = 'image'
        )
        AND countryGroups = "GROUP_US" 
        -- AND pollDuration > 0
    ) b ON a.pollId = b.id
    WHERE b.isDeleted IS NULL -- AND DATE(endTime) > DATE_ADD(current_date, INTERVAL 7 DAY)
        AND displayType != 'image' 
    ORDER BY total_votes desc
    -- LIMIT 100
),
TopLikedComments AS (
    -- Second query to fetch top liked comments
    SELECT
        c.*, p.pollId AS parentPollId,
        ROW_NUMBER() OVER (PARTITION BY c.pollId ORDER BY c.likesCount DESC) AS commentRank
    FROM (
        SELECT
            c.id as commentId, text as comment, likesCount, pollId,
            RANK() OVER (PARTITION BY c.pollId ORDER BY c.likesCount DESC) AS rank
        FROM `partitioned_tables.comments_partition` c
        LEFT JOIN `partitioned_tables.users_partition` u ON c.userId = u.email
        WHERE c.isDeleted = FALSE AND u.isDeleted = FALSE
        AND c.text NOT LIKE '%@%' AND c.text NOT LIKE '%http%' -- Exclude comments with "@" or "http"
    ) c
    JOIN TopVotedPolls p ON c.pollId = p.pollId
    ORDER BY c.rank ASC)
SELECT p.pollId, total_votes, pollRank, slug, question, pollDuration, pollCreator, commentId, comment, likesCount, commentRank
FROM TopVotedPolls p
JOIN TopLikedComments c ON p.pollId = c.parentPollId
WHERE commentRank <= 10
ORDER BY p.pollRank ASC, c.commentRank ASC


------------------------------------------------------------------------------------------------

--US top_voted_polls_and_top_comments_for_different_categories:

WITH TopVotedPolls AS (
    -- First query to fetch top voted polls
    SELECT
        a.*, b.question, b.slug, b.categories, b.pollDuration, b.createdBy AS pollCreator
    FROM (
        SELECT
            v.pollId,
            COUNT(*) AS total_votes,
            RANK() OVER (ORDER BY COUNT(*) DESC) AS pollRank
        FROM `partitioned_tables.votes_partition` v
        WHERE 
        -- DATE(v.createdAt) BETWEEN DATE_SUB(current_date, INTERVAL 7 DAY)
        --     AND DATE(current_date) AND 
            createdBy != "deleted_user"
        GROUP BY 1
        ORDER BY 3 ASC
        -- LIMIT 100
    ) a
    LEFT JOIN (
        SELECT * FROM `partitioned_tables.polls_partition`p
        LEFT JOIN (
            SELECT email FROM `partitioned_tables.users_partition`WHERE isDeleted = FALSE
        ) u ON p.createdBy = u.email
        WHERE p.createdBy != "product@hunch.in" AND p.id NOT IN (
            SELECT DISTINCT pollId FROM `partitioned_tables.options_partition`
            WHERE (LOWER(options_text) LIKE ('%comment%') OR LOWER(options_text) LIKE ('%lmk%')
            OR LOWER(options_text) LIKE ('%other%'))
            OR CHAR_LENGTH(options_text) <= 5 AND optionsDisplayType = 'image'
        )
        AND countryGroups = "GROUP_US"
        AND (
              categories LIKE '%Dating and Relationship%'
              OR categories LIKE '%College Musings%'
              OR categories LIKE '%Hypothetical/Would You Rather%'
              OR categories LIKE '%Music%'
              OR categories LIKE '%Fashion and Makeup%'
          ) 
        -- AND pollDuration > 0
    ) b ON a.pollId = b.id
    WHERE b.isDeleted IS NULL -- AND DATE(endTime) > DATE_ADD(current_date, INTERVAL 7 DAY)
        AND displayType != 'image' 
    ORDER BY total_votes desc
    -- LIMIT 100
),
TopLikedComments AS (
    -- Second query to fetch top liked comments
    SELECT
        c.*, p.pollId AS parentPollId,
        ROW_NUMBER() OVER (PARTITION BY c.pollId ORDER BY c.likesCount DESC) AS commentRank
    FROM (
        SELECT
            c.id as commentId, text as comment, likesCount, pollId,
            RANK() OVER (PARTITION BY c.pollId ORDER BY c.likesCount DESC) AS rank
        FROM `partitioned_tables.comments_partition` c
        LEFT JOIN `partitioned_tables.users_partition` u ON c.userId = u.email
        WHERE c.isDeleted = FALSE AND u.isDeleted = FALSE
        AND c.text NOT LIKE '%@%' AND c.text NOT LIKE '%http%' -- Exclude comments with "@" or "http"
    ) c
    JOIN TopVotedPolls p ON c.pollId = p.pollId
    ORDER BY c.rank ASC)
SELECT p.pollId, total_votes, pollRank, slug, categories, question, pollDuration, pollCreator, commentId, comment, likesCount, commentRank
FROM TopVotedPolls p
JOIN TopLikedComments c ON p.pollId = c.parentPollId
WHERE commentRank <= 10
ORDER BY p.pollRank ASC, c.commentRank ASC