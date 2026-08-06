import pandas as pd
import pytest
from app import (
    compute_batting_insights,
    compute_bowling_insights,
    get_featured_insights,
    get_page_name,
    get_team_summary,
    get_player_summary,
)

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


def test_compute_batting_insights():
    df = pd.DataFrame({
        'batter': ['A', 'A', 'B', 'B', 'B'],
        'batsman_runs': [4, 6, 10, 0, 2]
    })

    stats = compute_batting_insights(df, min_balls=1)

    assert stats.loc['B', 'runs'] == 12
    assert stats.loc['B', 'balls_faced'] == 3
    assert stats.loc['B', 'strike_rate'] == 400.0


def test_compute_bowling_insights():
    df = pd.DataFrame({
        'bowler': ['X', 'X', 'Y', 'Y'],
        'total_runs': [4, 6, 10, 2],
        'ball': [1, 1, 1, 1],
        'dismissal_kind': ['caught', 'bowled', 'lbw', None]
    })

    stats = compute_bowling_insights(df, min_balls=1)

    assert stats.loc['X', 'wickets'] == 2
    assert stats.loc['X', 'economy_rate'] == 30.0
    assert stats.loc['Y', 'wickets'] == 1


def test_compute_batting_insights_sort_by_strike_rate():
    df = pd.DataFrame({
        'batter': ['A', 'A', 'B', 'B'],
        'batsman_runs': [10, 10, 4, 4]
    })

    stats = compute_batting_insights(df, min_balls=1, sort_by='strike_rate')

    assert stats.index[0] == 'A'


def test_compute_bowling_insights_sort_by_economy_rate():
    df = pd.DataFrame({
        'bowler': ['X', 'Y'],
        'total_runs': [6, 4],
        'ball': [1, 1],
        'dismissal_kind': ['caught', 'bowled']
    })

    stats = compute_bowling_insights(df, min_balls=1, sort_by='economy_rate')

    assert stats.index[0] == 'Y'


def test_get_featured_insights():
    combined_df = pd.DataFrame({
        'batter': ['A', 'A', 'B', 'C'],
        'batsman_runs': [10, 20, 5, 30],
        'bowler': ['X', 'Y', 'Z', 'X'],
        'total_runs': [10, 5, 20, 4],
        'ball': [1, 1, 1, 1],
        'dismissal_kind': ['caught', 'bowled', 'lbw', 'caught'],
    })

    featured = get_featured_insights(combined_df)

    assert featured['top_batsman_name'] == 'A'
    assert featured['top_batsman_value'] == 30
    assert featured['top_bowler_name'] == 'X'
    assert featured['top_bowler_value'] == 2


def test_get_team_summary():
    matches_df = pd.DataFrame({
        'team1': ['MI', 'CSK', 'MI'],
        'team2': ['CSK', 'MI', 'CSK'],
        'winner': ['MI', 'CSK', 'CSK'],
        'season': [2020, 2021, 2022]
    })

    summary = get_team_summary(matches_df, 'MI')

    assert summary['total_matches'] == 3
    assert summary['matches_won'] == 1
    assert summary['win_percentage'] == 33.3


def test_get_player_summary():
    combined_df = pd.DataFrame({
        'batter': ['A', 'A', 'B'],
        'batsman_runs': [10, 20, 5],
        'bowler': ['A', 'B', 'A'],
        'total_runs': [10, 5, 20],
        'ball': [1, 1, 1],
        'dismissal_kind': ['caught', None, 'bowled'],
        'season': [2020, 2020, 2021],
    })

    summary = get_player_summary(combined_df, 'A')

    assert summary['runs'] == 30
    assert summary['balls_faced'] == 2
    assert summary['strike_rate'] == 1500.0
    assert summary['wickets'] == 2