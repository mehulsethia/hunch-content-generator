def take_comment_screenshot(page, url, filename):
    # Navigate to the URL
    page.goto(url, wait_until='networkidle')

    # Selector for the comment
    comment_selector = '.rootComment.highlight'

    # Wait for the comment to be visible
    page.wait_for_selector(comment_selector, timeout=60000)

    # Get the comment element
    comment_element = page.query_selector(comment_selector)
    if comment_element:
        # Take and save a screenshot of the comment element
        comment_element.screenshot(path=filename)
        print(f"Saved screenshot as {filename}")
    else:
        print(f"Comment element not found in {url}")