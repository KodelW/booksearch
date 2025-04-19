# openai_utils.py
import openai
import json
import os
import re

def get_search_terms_from_gpt(user_query: str, api_key: str) -> dict:
    """
    Analyzes the user's natural language query using OpenAI GPT
    to extract keywords, potential book titles, and a refined search query
    suitable for the Narou API.

    Args:
        user_query (str): The user's input in natural Korean.
        api_key (str): The OpenAI API key.

    Returns:
        dict: A dictionary containing 'keywords', 'titles', and 'narou_query'.
              Returns empty lists/string if analysis fails.
    """
    if not api_key:
        raise ValueError("OpenAI API key is not configured.")

    openai.api_key = api_key

    # Define the prompt structure based on the user's request
    prompt = f"""
    당신은 전문 한국 도서 리뷰어 및 추천가입니다. 사용자의 다음 요청을 분석하여 도서관 정보나루 API에서 검색하기 가장 좋은 형태로 정보를 추출해주세요.

    사용자 요청: "{user_query}"

    분석 단계 (Chain-of-Thought):
    1. 사용자 요청의 핵심 주제 또는 의도를 파악합니다.
    2. 주제와 관련된 핵심 키워드를 한국어로 1-3개 추출합니다. (예: "인공지능", "머신러닝")
    3. 사용자 요청에 부합할 만한 가상의 도서 제목 예시를 1-2개 제안합니다. (예: "AI 시대의 생존법", "미래를 바꿀 딥러닝")
    4. 위 키워드 또는 제목을 바탕으로, 도서관 정보나루 API의 '도서 검색(/api/srchBooks)' 기능에 가장 적합한 검색어(쿼리) 1개를 생성합니다. 이 검색어는 키워드 조합이나 가장 가능성 높은 제목일 수 있습니다. 간결하고 명확해야 합니다.

    출력 형식 (JSON):
    {{
      "keywords": ["키워드1", "키워드2", ...],
      "titles": ["추천 제목 예시 1", "추천 제목 예시 2", ...],
      "narou_query": "도서관 API 검색에 사용할 최종 쿼리"
    }}

    Self-reflection:
    - 키워드가 주제와 관련 있는가?
    - 제목 예시가 사용자 요청과 관련 있는가?
    - 생성된 narou_query가 도서관 API에서 실제 도서를 찾기에 적합한가? 너무 광범위하거나 모호하지 않은가?

    위 단계와 형식에 따라 분석 결과를 JSON으로만 제공해주세요. 설명은 포함하지 마세요.
    """

    try:
        # Using the newer OpenAI client syntax if available, otherwise fallback
        # Assuming newer syntax for this example
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o", # Or another suitable model like gpt-3.5-turbo
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}, # Enforce JSON output
            temperature=0.5, # Lower temperature for more focused output
        )

        # Extract the JSON content
        analysis_result = response.choices[0].message.content
        # Attempt to parse the JSON string
        parsed_result = json.loads(analysis_result)

        # Validate the structure
        keywords = parsed_result.get("keywords", [])
        titles = parsed_result.get("titles", [])
        narou_query = parsed_result.get("narou_query", "")

        # Basic validation
        if not isinstance(keywords, list): keywords = []
        if not isinstance(titles, list): titles = []
        if not isinstance(narou_query, str): narou_query = ""

        return {
            "keywords": keywords,
            "titles": titles,
            "narou_query": narou_query.strip()
        }

    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from GPT response: {analysis_result}")
        # Attempt to extract JSON using regex as a fallback
        match = re.search(r'\{.*\}', analysis_result, re.DOTALL)
        if match:
            try:
                parsed_result = json.loads(match.group(0))
                keywords = parsed_result.get("keywords", [])
                titles = parsed_result.get("titles", [])
                narou_query = parsed_result.get("narou_query", "")
                if not isinstance(keywords, list): keywords = []
                if not isinstance(titles, list): titles = []
                if not isinstance(narou_query, str): narou_query = ""
                return {
                    "keywords": keywords,
                    "titles": titles,
                    "narou_query": narou_query.strip()
                }
            except json.JSONDecodeError:
                 print("Error: Regex fallback failed to parse JSON.")
                 return {"keywords": [], "titles": [], "narou_query": ""}
        else:
            print("Error: No JSON object found in GPT response.")
            return {"keywords": [], "titles": [], "narou_query": ""}
    except Exception as e:
        print(f"An error occurred during OpenAI API call: {e}")
        # In case of API errors, return an empty structure
        return {"keywords": [], "titles": [], "narou_query": ""}

# Example Usage (for testing)
if __name__ == '__main__':
    load_dotenv() # Load .env for testing
    test_api_key = os.getenv("OPENAI_API_KEY")
    if test_api_key:
        test_query = "인공지능이 어떻게 세상을 바꾸는지 알려주는 책 찾아줘"
        result = get_search_terms_from_gpt(test_query, test_api_key)
        print(f"Query: {test_query}")
        print(f"GPT Analysis Result: {result}")

        test_query_2 = "요즘 인기있는 판타지 소설"
        result_2 = get_search_terms_from_gpt(test_query_2, test_api_key)
        print(f"\nQuery: {test_query_2}")
        print(f"GPT Analysis Result: {result_2}")
    else:
        print("Skipping example usage: OPENAI_API_KEY not found in .env")