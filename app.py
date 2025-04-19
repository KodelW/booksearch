# app.py
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os

# Import utility modules
from openai_utils import get_search_terms_from_gpt
from narou_api import search_books, find_libraries_for_book
from map_utils import render_map
# from utils import some_helper_function # Import helpers if needed

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
NAROU_API_KEY = os.getenv("NAROU_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Streamlit App ---

st.set_page_config(layout="wide") # Use wide layout

# --- Custom CSS Injection ---
st.markdown("""
<style>
    /* Center the title */
    h1 {
        text-align: center;
        margin-bottom: 2rem; /* Add some space below the title */
    }

    /* Style the form container to center elements and resemble search bar */
    div[data-testid="stForm"] {
        /* border: 1px solid #dfe1e5; */ /* Optional border */
        border-radius: 24px; /* Rounded corners */
        padding: 5px 15px;
        /* margin: 0 auto; /* Center the form */
        /* max-width: 700px; /* Limit width */
        /* box-shadow: 0 2px 5px rgba(0,0,0,0.1); */ /* Optional shadow */
        /* display: flex; */ /* Use flexbox for alignment */
        /* align-items: center; */ /* Center items vertically */
    }

     /* Style the text input */
    div[data-testid="stTextInput"] > div > div > input {
        border: none; /* Remove default border */
        /* padding: 10px; */
        /* flex-grow: 1; /* Allow input to take available space */
        /* margin-right: 10px; /* Space between input and button */
        /* outline: none; /* Remove focus outline */
        /* border-radius: 20px; /* Ensure rounded corners inside */
        /* background-color: #f1f3f4; /* Light gray background */
    }

    /* Style the submit button */
    div[data-testid="stForm"] div[data-testid="stButton"] > button {
        background-color: #4285F4; /* Google blue */
        color: white;
        border: none;
        border-radius: 50%; /* Make it round */
        width: 45px; /* Fixed width */
        height: 45px; /* Fixed height */
        padding: 0;
        margin-left: 10px; /* Space from input */
        font-size: 20px; /* Adjust icon size */
        line-height: 45px; /* Center icon vertically */
        text-align: center;
        cursor: pointer;
        transition: background-color 0.3s;
    }

    div[data-testid="stForm"] div[data-testid="stButton"] > button:hover {
        background-color: #357ae8; /* Darker blue on hover */
    }

    /* Ensure form elements are in a row */
    div[data-testid="stForm"] > form > div {
       display: flex;
       align-items: center;
       justify-content: center; /* Center input and button horizontally */
       gap: 10px; /* Add gap between input and button */
    }

    /* Adjust the text input width within the flex container */
     div[data-testid="stForm"] div[data-testid="stTextInput"] {
        flex-grow: 1; /* Allow input to take most space */
        max-width: 600px; /* Limit input width */
     }

     /* Center search results cards */
     .stApp > div:nth-child(1) > div > div > div > div:nth-child(2) > div > div > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] {
         justify-content: center;
         gap: 1rem; /* Add gap between cards */
     }

     /* Style for book cards */
     div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] [data-testid="stVerticalBlockBorderWrapper"] {
         padding: 1rem;
         border-radius: 10px; /* Rounded corners for cards */
         height: 350px; /* Ensure consistent height */
         display: flex;
         flex-direction: column;
         justify-content: space-between; /* Pushes button to bottom */
     }
     div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] [data-testid="stVerticalBlockBorderWrapper"] img {
         max-height: 150px; /* Limit image height */
         object-fit: contain; /* Scale image nicely */
         margin-bottom: 0.5rem;
     }


</style>
""", unsafe_allow_html=True)


# --- App Title ---
st.title("Book Search") # Changed title

# --- Initialize Session State ---
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'selected_book_isbn' not in st.session_state:
    st.session_state.selected_book_isbn = None
if 'library_locations' not in st.session_state:
    st.session_state.library_locations = None
if 'error_message' not in st.session_state:
    st.session_state.error_message = None
if 'loading' not in st.session_state:
    st.session_state.loading = False

# --- Search Input Form (Styled) ---
with st.form(key='search_form'):
    user_input = st.text_input(
        "찾고 싶은 책에 대해 알려주세요", # Label (can be hidden with CSS if needed)
        value=st.session_state.search_query,
        placeholder="AI 관련 책 추천...", # Placeholder text
        label_visibility="collapsed" # Hide the label visually
    )
    # Submit button styled as a search icon
    submit_button = st.form_submit_button(label='🔍') # Use magnifying glass emoji


# --- Main Logic ---
if submit_button and user_input:
    st.session_state.search_query = user_input
    st.session_state.search_results = None # Reset results
    st.session_state.selected_book_isbn = None # Reset selection
    st.session_state.library_locations = None # Reset locations
    st.session_state.error_message = None # Reset error
    st.session_state.loading = True

    # --- Step 1 & 2: Get Keywords/Titles from GPT ---
    with st.spinner('GPT가 검색어를 분석 중입니다... 🤔'):
        try:
            # Ensure API key is available
            if not OPENAI_API_KEY:
                raise ValueError("OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

            gpt_analysis = get_search_terms_from_gpt(user_input, OPENAI_API_KEY)
            keywords = gpt_analysis.get("keywords", [])
            titles = gpt_analysis.get("titles", [])
            narou_query = gpt_analysis.get("narou_query", user_input) # Use specific query if provided

            if not narou_query and keywords:
                narou_query = " ".join(keywords) # Fallback to keywords if no specific query
            elif not narou_query and titles:
                 narou_query = titles[0] # Fallback to first title if no query/keywords

            if narou_query: # Check if we have a query to show
                st.info(f"GPT 분석 결과: 검색어='{narou_query}'") # Show the query being used
            else:
                st.warning("GPT 분석에서 검색어를 추출하지 못했습니다. 입력값을 직접 사용합니다.")
                narou_query = user_input # Fallback to raw user input

        except Exception as e:
            st.session_state.error_message = f"GPT 분석 중 오류 발생: {e}"
            st.error(st.session_state.error_message)
            st.session_state.loading = False
            narou_query = None # Ensure we don't proceed if GPT failed

    # --- Step 3: Search Books via Narou API ---
    if narou_query and not st.session_state.error_message:
        with st.spinner(f"'{narou_query}' 관련 도서를 검색 중입니다... 📚"):
            try:
                 # Ensure API key is available
                if not NAROU_API_KEY:
                    raise ValueError("도서관 정보나루 API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

                search_results = search_books(narou_query, NAROU_API_KEY)
                if search_results:
                    st.session_state.search_results = search_results
                else:
                    st.session_state.error_message = "검색 결과가 없습니다. 다른 키워드로 시도해보세요."
                    st.warning(st.session_state.error_message) # Show warning immediately
            except Exception as e:
                st.session_state.error_message = f"도서 검색 중 오류 발생: {e}"
                st.error(st.session_state.error_message) # Display error immediately
    elif not st.session_state.error_message and not narou_query and submit_button: # Only show if submit was pressed
         st.session_state.error_message = "GPT 분석에서 유효한 검색어를 추출하지 못했습니다."
         st.warning(st.session_state.error_message)


    st.session_state.loading = False # Ensure loading is turned off


# --- Display Search Results ---
if st.session_state.search_results:
    st.subheader("📚 검색 결과")
    results_df = pd.DataFrame(st.session_state.search_results)

    # Display results in columns for better layout
    num_columns = 3 # Adjust number of columns as needed
    cols = st.columns(num_columns)
    col_idx = 0

    for index, book in results_df.iterrows():
        # Ensure book is a dictionary
        if not isinstance(book, pd.Series) and not isinstance(book, dict):
             print(f"Skipping invalid book data type: {type(book)}") # Debugging
             continue

        book_dict = book.to_dict() if isinstance(book, pd.Series) else book

        with cols[col_idx % num_columns]:
            # Use markdown for richer display and button-like interaction
            # Added border=True for clearer card separation
            container = st.container(border=True) # Removed fixed height for flexibility
            with container: # Use container context manager
                st.markdown(f"**{book_dict.get('bookname', '제목 없음')}**")
                st.caption(f"저자: {book_dict.get('authors', '저자 정보 없음')}")
                st.caption(f"출판사: {book_dict.get('publisher', '출판사 정보 없음')}")
                if 'bookImageURL' in book_dict and book_dict['bookImageURL']:
                    # *** FIX: Removed use_column_width ***
                    st.image(
                        book_dict['bookImageURL'],
                        width=100, # Keep fixed width
                        caption=f"{book_dict.get('bookname', '')} 표지"
                        # removed: use_column_width='auto'
                    )
                else:
                    # Placeholder if no image URL
                    st.image("https://placehold.co/100x150/eee/ccc?text=No+Image", width=100)


                # Button to trigger library search for this book
                # Ensure key is unique and valid
                isbn_key = book_dict.get('isbn13', f"noisbn_{index}")
                if st.button("소장 도서관 찾기", key=f"find_{isbn_key}"):
                    st.session_state.selected_book_isbn = book_dict.get('isbn13')
                    st.session_state.library_locations = None # Reset map for new selection
                    st.session_state.loading = True # Show loading for library search
                    st.rerun() # Rerun to trigger library search

        col_idx += 1

# --- Step 4: Find and Display Library Locations ---
# This logic runs if a book was selected in the previous step (via rerun)
if st.session_state.selected_book_isbn and st.session_state.library_locations is None and st.session_state.loading:
     with st.spinner(f"ISBN '{st.session_state.selected_book_isbn}' 소장 도서관을 검색 중입니다... 🗺️"):
        try:
            # Ensure API key is available
            if not NAROU_API_KEY:
                raise ValueError("도서관 정보나루 API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

            # Search Seoul (11) and Gyeonggi (31) for wider coverage
            libraries_seoul = find_libraries_for_book(st.session_state.selected_book_isbn, NAROU_API_KEY, region_code="11")
            libraries_gyeonggi = find_libraries_for_book(st.session_state.selected_book_isbn, NAROU_API_KEY, region_code="31")
            libraries = libraries_seoul + libraries_gyeonggi

            if libraries:
                # Convert to DataFrame for map utility
                st.session_state.library_locations = pd.DataFrame(libraries)
                # Ensure latitude and longitude are numeric
                st.session_state.library_locations['latitude'] = pd.to_numeric(st.session_state.library_locations['latitude'], errors='coerce')
                st.session_state.library_locations['longitude'] = pd.to_numeric(st.session_state.library_locations['longitude'], errors='coerce')
                st.session_state.library_locations.dropna(subset=['latitude', 'longitude'], inplace=True)
                # Remove duplicates just in case same library listed in both results
                st.session_state.library_locations.drop_duplicates(subset=['libCode'], inplace=True)

                if st.session_state.library_locations.empty:
                     st.session_state.error_message = "도서관 정보를 찾았지만, 유효한 위치 데이터가 없습니다."
                     st.warning(st.session_state.error_message)
                     st.session_state.library_locations = pd.DataFrame() # Set to empty df to prevent re-search

            else:
                st.session_state.error_message = "선택한 도서를 소장한 도서관 정보를 찾을 수 없습니다 (서울/경기 지역)."
                st.warning(st.session_state.error_message)
                st.session_state.library_locations = pd.DataFrame() # Set to empty df to prevent re-search

        except Exception as e:
            st.session_state.error_message = f"도서관 검색 중 오류 발생: {e}"
            st.error(st.session_state.error_message)
            st.session_state.library_locations = pd.DataFrame() # Set to empty df on error
        finally:
             st.session_state.loading = False # Turn off loading indicator
             # Only rerun if loading is complete, avoids potential loop if error occurs before loading=False
             if not st.session_state.loading:
                st.rerun()


# --- Display Map ---
# Check if library_locations is not None (meaning search was attempted)
if st.session_state.library_locations is not None:
    # Check if the dataframe is actually empty after processing
    if not st.session_state.library_locations.empty:
        st.subheader("📍 소장 도서관 위치")
        # Find the book title for the map header
        selected_book_title = "선택된 도서"
        if st.session_state.search_results and st.session_state.selected_book_isbn:
            # Ensure search_results is a list of dicts
            results_list = st.session_state.search_results
            if isinstance(results_list, pd.DataFrame):
                results_list = results_list.to_dict('records')

            if isinstance(results_list, list):
                 book_info = next((b for b in results_list if isinstance(b, dict) and b.get('isbn13') == st.session_state.selected_book_isbn), None)
                 if book_info:
                    selected_book_title = book_info.get('bookname', selected_book_title)

        st.markdown(f"**'{selected_book_title}'** 소장 도서관 지도 (검색 지역: 서울/경기)") # Indicate search region
        render_map(st.session_state.library_locations)
    # If search was attempted but resulted in empty dataframe or error, message is already shown above.


# --- Footer or additional info ---
st.markdown("---")
st.caption("Powered by OpenAI & 도서관 정보나루")