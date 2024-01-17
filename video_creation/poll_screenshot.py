def take_poll_question_screenshot(page, url, filename):
    try:

        # CSS selectors for the poll elements
        poll_question_selector = '.container-text'
        
        page.goto(url, wait_until='networkidle')
        page.wait_for_load_state('networkidle')
        page.wait_for_selector(poll_question_selector, timeout=100000)
        border_width = 10  # Set the border width

        # Navigate to the URL
        page.goto(url, wait_until='networkidle')

        # Wait for the necessary elements to load
        page.wait_for_selector(poll_question_selector, timeout=100000)

        # Get the bounding box values of the poll question element
        question_element = page.query_selector(poll_question_selector)
        if question_element:
            question_box = question_element.bounding_box()
        else:
            raise ValueError("Poll question element not found") 
        
        # Add a border to the bounding box
        border_width = 10
        question_box_with_border = {
            'x': question_box['x'] - border_width,
            'y': question_box['y'] - border_width,
            'width': question_box['width'] + (2 * border_width),
            'height': question_box['height'] + (2 * border_width)
        }
        
        # Take and save the screenshot for the poll question
        page.screenshot(path=filename, clip=question_box_with_border)
        print(f"Saved poll question screenshot as {filename}")

    except Exception as e:
        print(f"Error occurred: {e}")
        print(f"Current URL: {page.url}")

def take_poll_screenshot(page, url, filename):
    try:

        # CSS selectors for the poll elements
        first_poll_selector = '.container-text'
        options_selector = '.options-container'
        
        page.goto(url, wait_until='networkidle')
        page.wait_for_load_state('networkidle')
        page.wait_for_selector(first_poll_selector, timeout=100000)
        page.wait_for_selector(options_selector, timeout=100000)
        border_width = 10  # Set the border width

        # Navigate to the URL
        page.goto(url, wait_until='networkidle')

        # Wait for the necessary elements to load
        page.wait_for_selector(first_poll_selector, timeout=100000)
        page.wait_for_selector(options_selector, timeout=100000)

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
