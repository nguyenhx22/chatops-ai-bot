import json
import logging
from agents.tools.ira_tools import IRATools

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def test_get_ira_information():
    # Test case 1: Valid input
    input_text = json.dumps({"platform_name": "example_platform"})
    result = IRATools.get_platform_information(input_text)
    print("Test case 1 - Valid input:")
    print(result)
    print()

    # # Test case 2: Missing 'platform_name'
    # input_text = json.dumps({})
    # result = get_ira_information(input_text)
    # print("Test case 2 - Missing 'platform_name':")
    # print(result)
    # print()

    # # Test case 3: File not found
    # input_text = json.dumps({"platform_name": "example_platform"})
    # try:
    #     with open("data/mpa_platform_data.txt", "w") as file:
    #         file.write("Sample data")
    # except Exception as e:
    #     logging.error(f"Error creating test file: {e}")
    # result = get_ira_information(input_text)
    # print("Test case 3 - File not found:")
    # print(result)
    # print()
    
if __name__ == "__main__":
    test_get_ira_information()