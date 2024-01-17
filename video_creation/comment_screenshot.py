import time
from playwright.sync_api import sync_playwright, TimeoutError

def take_comment_screenshot(page, url, filename):
    retry_count = 0
    max_retries = 3
    while retry_count < max_retries:
        try:
            # Navigate to the URL
            page.goto(url, wait_until='networkidle')

            # Selector for the container
            container_selector = '.content-container'

            # Selector for the comment
            comment_selector = '.rootComment.highlight'

            # Wait for the necessary elements to load
            page.wait_for_selector(container_selector, timeout=100000)
            page.wait_for_selector(comment_selector, timeout=100000)

            # Scroll the comment into the middle of the viewport
            page.evaluate(f"document.querySelector('{comment_selector}').scrollIntoView({{behavior: 'auto', block: 'center', inline: 'center'}})")

            # Get the comment element
            comment_element = page.query_selector(comment_selector)

            if comment_element:
                # Set comment background to black and take a screenshot
                page.evaluate(f"""
                    const commentSelector = '{comment_selector}';
                    document.querySelector(commentSelector).style.backgroundColor = 'black';
                """)
                
                # Get bounding box of the comment element
                comment_box = comment_element.bounding_box()

                # Increase the screenshot width and height to capture the black border
                screenshot_box = {
                    'x': comment_box['x'] - 10,  # Adjust as needed
                    'y': comment_box['y'] - 10,  # Adjust as needed
                    'width': comment_box['width'] + 20,  # Adjust as needed
                    'height': comment_box['height'] + 20  # Adjust as needed
                }

                # Take and save a screenshot of the adjusted comment bounding box with a black border
                page.screenshot(path=filename, clip=screenshot_box)
                print(f"Saved screenshot as {filename}")
                return True
            else:
                print(f"Comment element not found in {url}")

        except TimeoutError as e:
            print(f"TimeoutError: {e}. Retrying {retry_count + 1}/{max_retries}...")
            retry_count += 1
            time.sleep(5)  # Wait 5 seconds before retrying
            return False
        except Exception as e:
            print(f"An error occurred: {e}")
            return False