# narou_api.py
import requests
import xml.etree.ElementTree as ET
import json

# --- Constants ---
BASE_URL = "http://data4library.kr/api"

# --- Helper Function ---
def _parse_xml_response(xml_string: str, result_tag: str, item_tag: str) -> list:
    """
    Parses XML response from Narou API into a list of dictionaries.

    Args:
        xml_string (str): The XML response string.
        result_tag (str): The tag containing the list of items (e.g., 'docs', 'libs').
        item_tag (str): The tag for each individual item (e.g., 'doc', 'lib').

    Returns:
        list: A list of dictionaries, where each dictionary represents an item.
              Returns an empty list if parsing fails or no items are found.
    """
    items = []
    try:
        root = ET.fromstring(xml_string)
        results_element = root.find(result_tag)
        if results_element is None:
             # Sometimes the root itself might contain the items if result_tag is not present
             results_element = root

        item_elements = results_element.findall(item_tag) if results_element is not None else []

        for item_elem in item_elements:
            item_data = {}
            for child in item_elem:
                # Handle potential CDATA sections or just text content
                text_content = child.text.strip() if child.text else ""
                item_data[child.tag] = text_content
            if item_data: # Only add if data was extracted
                items.append(item_data)
    except ET.ParseError as e:
        print(f"XML Parsing Error: {e}")
    except Exception as e:
        print(f"Error parsing XML: {e}")
    return items

# --- API Functions ---

def search_books(query: str, api_key: str, page_no: int = 1, page_size: int = 20) -> list:
    """
    Searches for books using the Narou API's /srchBooks endpoint.

    Args:
        query (str): The search keyword or title.
        api_key (str): The Narou API authentication key.
        page_no (int): The page number to retrieve.
        page_size (int): The number of results per page.

    Returns:
        list: A list of dictionaries, each representing a book found.
              Returns an empty list if the search fails or no results are found.
    """
    if not api_key:
        raise ValueError("Narou API key is not configured.")

    endpoint = f"{BASE_URL}/srchBooks"
    params = {
        'authKey': api_key,
        'keyword': query, # Using keyword search for broader results
        'pageNo': page_no,
        'pageSize': page_size,
        'format': 'xml' # Request XML format
    }

    try:
        response = requests.get(endpoint, params=params, timeout=15) # Added timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        # The Narou API seems to return XML even if JSON is requested sometimes,
        # so explicitly parse XML.
        return _parse_xml_response(response.text, 'docs', 'doc')

    except requests.exceptions.RequestException as e:
        print(f"Error during Narou API book search request: {e}")
        # Consider specific handling for timeouts, connection errors etc.
        raise ConnectionError(f"Failed to connect to Narou API: {e}") from e
    except Exception as e:
        print(f"An unexpected error occurred during book search: {e}")
        return [] # Return empty list on other errors

def find_libraries_for_book(isbn13: str, api_key: str, region_code: str = "11", page_no: int = 1, page_size: int = 50) -> list:
    """
    Finds libraries that own a specific book using its ISBN13.
    Searches within a specific region.

    Args:
        isbn13 (str): The 13-digit ISBN of the book.
        api_key (str): The Narou API authentication key.
        region_code (str): The region code to search within (e.g., '11' for Seoul).
                           Refer to Narou API docs for codes.
        page_no (int): The page number.
        page_size (int): The number of results per page.

    Returns:
        list: A list of dictionaries, each representing a library.
              Returns an empty list if the search fails or no libraries are found.
    """
    if not api_key:
        raise ValueError("Narou API key is not configured.")
    if not isbn13:
        raise ValueError("ISBN13 must be provided to find libraries.")
    if not region_code:
         raise ValueError("Region code must be provided for library search.")


    endpoint = f"{BASE_URL}/libSrchByBook"
    params = {
        'authKey': api_key,
        'isbn': isbn13, # API parameter is 'isbn' but expects ISBN13
        'region': region_code,
        'pageNo': page_no,
        'pageSize': page_size,
        'format': 'xml' # Request XML format
    }

    try:
        response = requests.get(endpoint, params=params, timeout=20) # Longer timeout for potentially slower searches
        response.raise_for_status()

        return _parse_xml_response(response.text, 'libs', 'lib')

    except requests.exceptions.RequestException as e:
        print(f"Error during Narou API library search request: {e}")
        raise ConnectionError(f"Failed to connect to Narou API: {e}") from e
    except Exception as e:
        print(f"An unexpected error occurred during library search: {e}")
        return []


# Example Usage (for testing)
if __name__ == '__main__':
    load_dotenv() # Load .env for testing
    test_api_key = os.getenv("NAROU_API_KEY")
    if test_api_key:
        # --- Test Book Search ---
        test_query = "파이썬"
        print(f"\nSearching for books with query: '{test_query}'")
        books = search_books(test_query, test_api_key, page_size=5)
        if books:
            print(f"Found {len(books)} books (showing first {len(books)}):")
            for i, book in enumerate(books):
                 print(f"  {i+1}. {book.get('bookname')} (ISBN: {book.get('isbn13')})")
            test_isbn = books[0].get('isbn13') # Use the first book's ISBN for library search

            # --- Test Library Search ---
            if test_isbn:
                 print(f"\nSearching for libraries with book ISBN: {test_isbn} in Seoul (11)")
                 # Note: This might return empty if the specific book isn't in Seoul libraries
                 # in the Narou database sample used for testing.
                 libraries = find_libraries_for_book(test_isbn, test_api_key, region_code="11", page_size=5)
                 if libraries:
                     print(f"Found {len(libraries)} libraries (showing first {len(libraries)}):")
                     for i, lib in enumerate(libraries):
                          print(f"  {i+1}. {lib.get('libName')} ({lib.get('address')}) - Lat: {lib.get('latitude')}, Lon: {lib.get('longitude')}")
                 else:
                     print("No libraries found for this ISBN in the specified region.")
            else:
                 print("Could not get ISBN from book search results to test library search.")

        else:
            print("No books found for the query.")

    else:
        print("Skipping example usage: NAROU_API_KEY not found in .env")