# map_utils.py
import streamlit as st
import pandas as pd

def render_map(locations_df: pd.DataFrame):
    """
    Renders an interactive map using Streamlit's st.map based on library locations.

    Args:
        locations_df (pd.DataFrame): A DataFrame containing library location data.
                                     Must include 'latitude', 'longitude' columns.
                                     Optional columns like 'libName' can be used for tooltips if supported
                                     by st.map in the future or if using other map libraries.
    """
    if locations_df is None or locations_df.empty:
        st.warning("지도에 표시할 도서관 위치 정보가 없습니다.")
        return

    # Ensure required columns exist and are numeric
    if not all(col in locations_df.columns for col in ['latitude', 'longitude']):
        st.error("지도 표시에 필요한 'latitude' 또는 'longitude' 컬럼이 없습니다.")
        return

    # Create a copy to avoid modifying the original DataFrame in session state
    map_df = locations_df.copy()

    # Ensure lat/lon are numeric and drop rows where conversion fails
    map_df['latitude'] = pd.to_numeric(map_df['latitude'], errors='coerce')
    map_df['longitude'] = pd.to_numeric(map_df['longitude'], errors='coerce')
    map_df.dropna(subset=['latitude', 'longitude'], inplace=True)

    if map_df.empty:
        st.warning("유효한 위도/경도 데이터를 가진 도서관이 없습니다.")
        return

    # Rename columns to what st.map expects ('lat' or 'latitude', 'lon' or 'longitude')
    # st.map should automatically detect 'latitude' and 'longitude'
    # map_df = map_df.rename(columns={'latitude': 'lat', 'longitude': 'lon'}) # Optional renaming if needed

    try:
        # Display the map
        st.map(map_df[['latitude', 'longitude']]) # Pass only lat/lon columns
        # Note: st.map currently doesn't support extensive customization like tooltips directly from the DataFrame.
        # For more features (tooltips, custom icons), consider libraries like pydeck or folium.
        # Example with potential future tooltip support (conceptual):
        # st.map(map_df, latitude='latitude', longitude='longitude', tooltip='libName')

    except Exception as e:
        st.error(f"지도 렌더링 중 오류 발생: {e}")


# Example Usage (for testing)
if __name__ == '__main__':
    # Create a sample DataFrame similar to what narou_api might return
    sample_data = [
        {'libCode': '111017', 'libName': '서울특별시교육청서울시립어린이도서관', 'address': '서울특별시 종로구 사직로 9길 7', 'latitude': '37.5763001', 'longitude': '126.968237'},
        {'libCode': '111004', 'libName': '서울특별시교육청정독도서관', 'address': '서울특별시 종로구 북촌로5길 48', 'latitude': '37.5806', 'longitude': '126.981'},
        {'libCode': '111005', 'libName': '서울시립종로도서관', 'address': '서울특별시 종로구 사직로 9길 15-14', 'latitude': '37.5770', 'longitude': '126.968'},
        {'libCode': 'XXXXXX', 'libName': 'Invalid Location Library', 'address': 'Somewhere', 'latitude': 'invalid', 'longitude': 'invalid'}, # Invalid data
        {'libCode': 'YYYYYY', 'libName': 'Missing Lon Library', 'address': 'Somewhere Else', 'latitude': '37.6', 'longitude': None}, # Missing data

    ]
    sample_df = pd.DataFrame(sample_data)

    st.title("Map Utils Test")
    st.write("Rendering map with sample library data:")
    render_map(sample_df)

    st.write("Rendering map with empty data:")
    render_map(pd.DataFrame())

    st.write("Rendering map with missing columns:")
    render_map(pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]}))