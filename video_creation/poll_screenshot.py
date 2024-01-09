def take_poll_screenshot(page, url, filename):
    try:

        # CSS selectors for the poll elements
        first_poll_selector = '.container-text'
        options_selector = '.options-container'
        
        page.goto(url, wait_until='networkidle')
        page.wait_for_load_state('networkidle')
        page.wait_for_selector(first_poll_selector, timeout=60000)
        page.wait_for_selector(options_selector, timeout=60000)
        border_width = 10  # Set the border width

        # Navigate to the URL
        page.goto(url, wait_until='networkidle')

        # Wait for the necessary elements to load
        page.wait_for_selector(first_poll_selector, timeout=60000)
        page.wait_for_selector(options_selector, timeout=60000)

        # Find the elements
        question_element = page.query_selector(first_poll_selector)
        options_element = page.query_selector(options_selector)

        if question_element and options_element:
            # Get bounding boxes of elements
            question_box = question_element.bounding_box()
            options_box = options_element.bounding_box()

            # Calculate the combined bounding box with a border
            combined_box = {
                'x': question_box['x'] - border_width,
                'y': question_box['y'] - border_width,
                'width': max(question_box['width'], options_box['width']) + (2 * border_width),
                'height': (options_box['y'] - question_box['y']) + options_box['height'] + (2 * border_width)
            }

            # Take and save the screenshot
            page.screenshot(path=filename, clip=combined_box)
            print(f"Saved poll screenshot as {filename}")
        else:
            print("Elements not found")

    except Exception as e:
        print(f"Error occurred: {e}")
        print(f"Current URL: {page.url}")
        page.screenshot(path='error_screenshot.png')  # Take a full-page screenshot
        with open('error_page.html', 'w') as file:
            file.write(page.content())  # Save the current page HTML
