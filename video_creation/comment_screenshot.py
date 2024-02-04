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
            page.wait_for_selector(container_selector, timeout=50000)
            page.wait_for_selector(comment_selector, timeout=50000)

            # Scroll the comment into the middle of the viewport
            page.evaluate(f"document.querySelector('{comment_selector}').scrollIntoView({{behavior: 'auto', block: 'center', inline: 'center'}})")

            # Get the comment element
            comment_element = page.query_selector(comment_selector)
            if comment_element:
                # Disable CSS animations
                page.evaluate("""
                    const styleSheet = document.createElement('style');
                    styleSheet.type = 'text/css';
                    styleSheet.innerText = '* { animation: none !important; }';
                    document.head.appendChild(styleSheet);
                """)

                # Remove background completely
                page.evaluate(f"""
                    document.querySelector('{comment_selector}').style.background = 'none';
                """)
                
                time.sleep(5)  # Wait for 5 seconds to allow changes to take effect

                # Get bounding box of the comment element
                comment_box = comment_element.bounding_box()

                # Increase the screenshot width and height to capture the entire comment area
                screenshot_box = {
                    'x': comment_box['x'] - 10,  # Adjust as needed
                    'y': comment_box['y'] - 10,  # Adjust as needed
                    'width': comment_box['width'] + 20,  # Adjust as needed
                    'height': comment_box['height'] + 20  # Adjust as needed
                }

                # Take and save a screenshot of the adjusted comment bounding box
                page.screenshot(path=filename, clip=screenshot_box)
                print(f"Saved screenshot as {filename}")

                break
            else:
                print(f"Comment element not found in {url}")

        except TimeoutError as e:
            print(f"TimeoutError: {e}. Retrying {retry_count + 1}/{max_retries}...")
            retry_count += 1
            time.sleep(5)  # Wait 5 seconds before retrying
        except Exception as e:
            print(f"An error occurred: {e}")
            page.screenshot(path='error_screenshot.png')  # Take a full-page screenshot on error
            with open('error_page.html', 'w') as file:
                file.write(page.content())  # Save the current page HTML on error

    if retry_count == max_retries:
        print("Failed to take a screenshot after retries. Exiting...")
        return False

    return True
