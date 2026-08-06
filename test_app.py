import pytest
from app import get_page_name

def test_get_page_name_with_emoji():
    assert get_page_name("📊 Overview") == "Overview"
    assert get_page_name("📅 Season Analysis") == "Season Analysis"
    assert get_page_name("🏏 Team Analysis") == "Team Analysis"
    assert get_page_name("👤 Player Stats") == "Player Stats"
    assert get_page_name("🏟️ Venue Stats") == "Venue Stats"
    assert get_page_name("🤝 Head to Head") == "Head to Head"

def test_get_page_name_without_emoji():
    assert get_page_name("Overview") == "Overview"
    assert get_page_name("Season Analysis") == "Season Analysis"
    
def test_get_page_name_empty():
    assert get_page_name("") == "Overview"
    assert get_page_name("📊") == "Overview"
    assert get_page_name("📊 ") == "Overview"

def test_get_page_name_multiple_emojis():
    assert get_page_name("📊 🏏 Overview Stats") == "Overview Stats"