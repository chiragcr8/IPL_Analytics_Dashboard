import os
import base64
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# Team name mapping
TEAM_NAMES = {
    'MI': 'Mumbai Indians',
    'CSK': 'Chennai Super Kings',
    'RCB': 'Royal Challengers Bangalore',
    'KKR': 'Kolkata Knight Riders',
    'RR': 'Rajasthan Royals',
    'DC': 'Delhi Capitals',
    'PBKS': 'Punjab Kings',
    'SRH': 'Sunrisers Hyderabad',
    'GT': 'Gujarat Titans',
    'LSG': 'Lucknow Super Giants',
    'DD': 'Delhi Daredevils',
    'KXIP': 'Kings XI Punjab',
    'KTK': 'Kochi Tuskers Kerala',
    'PWI': 'Pune Warriors India',
    'GL': 'Gujarat Lions',
    'RPS': 'Rising Pune Supergiant',
    'DCH': 'Deccan Chargers'
}


def compute_batting_insights(combined_df, min_balls=50, sort_by='runs'):
    """Return batters with runs, balls faced, and strike rate."""
    batter_col = 'batter' if 'batter' in combined_df.columns else 'batsman'
    runs_col = 'batsman_runs' if 'batsman_runs' in combined_df.columns else 'batsman_run'

    if batter_col not in combined_df.columns or runs_col not in combined_df.columns:
        return pd.DataFrame(columns=['runs', 'balls_faced', 'strike_rate'])

    batting_df = combined_df[[batter_col, runs_col]].copy()
    batting_df = batting_df.dropna(subset=[batter_col])
    batting_df['balls_faced'] = 1

    batting_stats = batting_df.groupby(batter_col, dropna=False).agg(
        runs=(runs_col, 'sum'),
        balls_faced=('balls_faced', 'count')
    )
    batting_stats['strike_rate'] = (
        batting_stats['runs'] / batting_stats['balls_faced'] * 100
    ).round(2)

    filtered_stats = batting_stats[batting_stats['balls_faced'] >= min_balls]

    if sort_by == 'strike_rate':
        return filtered_stats.sort_values(['strike_rate', 'runs'], ascending=[False, False])

    return filtered_stats.sort_values(['runs', 'strike_rate'], ascending=[False, False])


def compute_bowling_insights(combined_df, min_balls=30, sort_by='wickets'):
    """Return bowlers with runs conceded, balls bowled, wickets, and economy."""
    if 'bowler' not in combined_df.columns:
        return pd.DataFrame(columns=['runs_conceded', 'balls_bowled', 'wickets', 'economy_rate'])

    bowling_df = combined_df[['bowler', 'total_runs', 'ball', 'dismissal_kind']].copy()
    bowling_df = bowling_df.dropna(subset=['bowler'])
    bowling_df['balls_bowled'] = 1

    bowling_stats = bowling_df.groupby('bowler', dropna=False).agg(
        runs_conceded=('total_runs', 'sum'),
        balls_bowled=('balls_bowled', 'count')
    )

    valid_dismissals = (
        bowling_df['dismissal_kind'].notna() &
        bowling_df['dismissal_kind'].ne('run out') &
        bowling_df['dismissal_kind'].astype(str).str.strip().ne('')
    )
    wickets = bowling_df.loc[valid_dismissals].groupby('bowler', dropna=False).size()

    bowling_stats['wickets'] = wickets.reindex(bowling_stats.index).fillna(0).astype(int)
    bowling_stats['economy_rate'] = (
        bowling_stats['runs_conceded'] / bowling_stats['balls_bowled'] * 6
    ).round(2)

    filtered_stats = bowling_stats[bowling_stats['balls_bowled'] >= min_balls]

    if sort_by == 'economy_rate':
        return filtered_stats.sort_values(['economy_rate', 'wickets'], ascending=[True, False])

    return filtered_stats.sort_values(['wickets', 'economy_rate'], ascending=[False, True])


def get_featured_insights(combined_df):
    """Return all-time top run scorer and wicket taker values for the overview cards."""
    batter_col = 'batter' if 'batter' in combined_df.columns else 'batsman'
    runs_col = 'batsman_runs' if 'batsman_runs' in combined_df.columns else 'batsman_run'

    if batter_col in combined_df.columns and runs_col in combined_df.columns:
        batting_totals = combined_df[[batter_col, runs_col]].dropna(subset=[batter_col]).groupby(batter_col)[runs_col].sum()
        top_batsman_name = batting_totals.sort_values(ascending=False).index[0] if not batting_totals.empty else 'N/A'
        top_batsman_value = int(batting_totals.sort_values(ascending=False).iloc[0]) if not batting_totals.empty else 0
    else:
        top_batsman_name = 'N/A'
        top_batsman_value = 0

    if 'bowler' in combined_df.columns:
        bowling_rows = combined_df[['bowler', 'dismissal_kind']].dropna(subset=['bowler'])
        valid_wickets = bowling_rows[
            bowling_rows['dismissal_kind'].notna() &
            (bowling_rows['dismissal_kind'] != 'run out') &
            (bowling_rows['dismissal_kind'].astype(str).str.strip() != '')
        ]
        wicket_totals = valid_wickets.groupby('bowler').size()
        top_bowler_name = wicket_totals.sort_values(ascending=False).index[0] if not wicket_totals.empty else 'N/A'
        top_bowler_value = int(wicket_totals.sort_values(ascending=False).iloc[0]) if not wicket_totals.empty else 0
    else:
        top_bowler_name = 'N/A'
        top_bowler_value = 0

    return {
        'top_batsman_name': top_batsman_name,
        'top_batsman_value': top_batsman_value,
        'top_bowler_name': top_bowler_name,
        'top_bowler_value': top_bowler_value,
    }


def get_page_name(page_label: str) -> str:
    """Strip emoji prefixes from sidebar page labels."""
    cleaned = page_label.strip()
    if not cleaned:
        return 'Overview'

    parts = cleaned.split()
    non_emoji_parts = [part for part in parts if not any(ord(char) > 127 for char in part)]
    return ' '.join(non_emoji_parts) if non_emoji_parts else 'Overview'

def get_full_team_name(team_abbr: str) -> str:
    return TEAM_NAMES.get(team_abbr, team_abbr)


def get_team_summary(matches_df, team_name):
    """Return simple team summary metrics."""
    team_matches = matches_df[(matches_df['team1'] == team_name) | (matches_df['team2'] == team_name)]
    total_matches = len(team_matches)
    matches_won = int((team_matches['winner'] == team_name).sum())
    win_percentage = round((matches_won / total_matches * 100) if total_matches else 0, 1)
    season_wins = team_matches[team_matches['winner'] == team_name]['season'].dropna().value_counts().sort_index()

    return {
        'total_matches': total_matches,
        'matches_won': matches_won,
        'win_percentage': win_percentage,
        'season_wins': season_wins,
    }


def get_player_summary(combined_df, player_name):
    """Return player summary metrics across all seasons."""
    batter_col = 'batter' if 'batter' in combined_df.columns else 'batsman'
    runs_col = 'batsman_runs' if 'batsman_runs' in combined_df.columns else 'batsman_run'

    batting_rows = combined_df[combined_df[batter_col] == player_name] if batter_col in combined_df.columns else pd.DataFrame()
    bowling_rows = combined_df[combined_df['bowler'] == player_name] if 'bowler' in combined_df.columns else pd.DataFrame()

    runs = int(batting_rows[runs_col].sum()) if not batting_rows.empty and runs_col in batting_rows.columns else 0
    balls_faced = int(len(batting_rows)) if not batting_rows.empty else 0
    strike_rate = round((runs / balls_faced * 100) if balls_faced else 0, 2)

    wickets = 0
    if not bowling_rows.empty:
        valid_wickets = bowling_rows[
            bowling_rows['dismissal_kind'].notna() &
            (bowling_rows['dismissal_kind'] != 'run out') &
            (bowling_rows['dismissal_kind'].astype(str).str.strip() != '')
        ]
        wickets = int(len(valid_wickets))

    runs_conceded = int(bowling_rows['total_runs'].sum()) if not bowling_rows.empty else 0
    balls_bowled = int(len(bowling_rows)) if not bowling_rows.empty else 0
    economy_rate = round((runs_conceded / balls_bowled * 6) if balls_bowled else 0, 2)
    seasons = sorted(set(batting_rows['season'].tolist() + bowling_rows['season'].tolist()) if not batting_rows.empty or not bowling_rows.empty else [])

    return {
        'runs': runs,
        'balls_faced': balls_faced,
        'strike_rate': strike_rate,
        'wickets': wickets,
        'runs_conceded': runs_conceded,
        'balls_bowled': balls_bowled,
        'economy_rate': economy_rate,
        'seasons': seasons,
    }


@st.cache_data(show_spinner=False)
def load_data():
    """Load and validate IPL data files"""
    if not os.path.exists('matches.csv') or not os.path.exists('deliveries.csv'):
        st.error("Required data files (matches.csv and/or deliveries.csv) are missing!")
        st.stop()
    
    try:
        matches_df = pd.read_csv('matches.csv')
        deliveries_df = pd.read_csv('deliveries.csv')
        combined_df = pd.merge(deliveries_df, matches_df, left_on='match_id', right_on='id')
        return matches_df, deliveries_df, combined_df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

def show_overview(matches_df, deliveries_df, combined_df):
    """Display overview page with all-time statistics"""
    st.title('🏏 IPL Data Analysis Dashboard')
    st.header('📊 IPL Overview - All Seasons')

    # Total wins across all seasons (ignore missing winners)
    all_seasons_wins = matches_df['winner'].dropna().value_counts()

    batting_insights = compute_batting_insights(combined_df, min_balls=50, sort_by='strike_rate')
    bowling_insights = compute_bowling_insights(combined_df, min_balls=30, sort_by='economy_rate')

    st.subheader('🔍 Featured Insights')
    total_matches = len(matches_df)
    runs_col = 'batsman_runs' if 'batsman_runs' in combined_df.columns else 'batsman_run'
    total_runs = int(combined_df[runs_col].sum()) if runs_col in combined_df.columns else 0

    if 'dismissal_kind' in combined_df.columns:
        valid_dismissals = combined_df['dismissal_kind'].notna() & (
            combined_df['dismissal_kind'] != 'run out'
        ) & (combined_df['dismissal_kind'].astype(str).str.strip() != '')
        total_wickets = int(valid_dismissals.sum())
    else:
        total_wickets = 0

    featured_insights = get_featured_insights(combined_df)
    top_batsman_name = featured_insights['top_batsman_name']
    top_bowler_name = featured_insights['top_bowler_name']
    top_batsman_value = featured_insights['top_batsman_value']
    top_bowler_value = featured_insights['top_bowler_value']

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric('Total Matches', f'{total_matches:,}')
    with col2:
        st.metric('Total Runs', f'{total_runs:,}')
    with col3:
        st.metric('Top Run Scorer (All Time)', top_batsman_name, delta=f'{top_batsman_value} runs')
    with col4:
        st.metric('Top Wicket Taker (All Time)', top_bowler_name, delta=f'{top_bowler_value} wickets')

    st.caption('These highlight cards use minimum thresholds so the rankings stay meaningful.')

    st.subheader('🏆 Total Wins by Teams')
    st.dataframe(
        all_seasons_wins.rename('Total Wins').reset_index().rename(columns={'index': 'Team'}),
        height=400
    )

    # Visualization
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.barplot(
        x=all_seasons_wins.values,
        y=all_seasons_wins.index,
        hue=all_seasons_wins.index,
        palette='coolwarm',
        legend=False,
        ax=ax
    )
    ax.set_title('Total Wins by Teams Across All Seasons', fontsize=16, fontweight='bold')
    ax.set_xlabel('Number of Wins')
    ax.set_ylabel('Teams')
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    st.pyplot(fig)

    # Top run scorers
    st.subheader('🏏 Top 10 Run Scorers (All Time)')
    all_time_runs = compute_batting_insights(combined_df, min_balls=1, sort_by='runs')
    st.dataframe(
        all_time_runs.head(10).reset_index().rename(columns={
            'index': 'Batter',
            'runs': 'Total Runs',
            'balls_faced': 'Balls Faced',
            'strike_rate': 'Strike Rate'
        }),
        height=400
    )

    st.subheader('⚡ Top Strike Rates (Min 50 Balls)')
    if not batting_insights.empty:
        st.dataframe(
            batting_insights.head(10).reset_index().rename(columns={
                'index': 'Batter',
                'runs': 'Runs',
                'balls_faced': 'Balls Faced',
                'strike_rate': 'Strike Rate'
            }),
            height=320
        )
    else:
        st.info('No batting data available for strike-rate ranking.')

    # Top wicket takers
    st.subheader('🎯 Top 10 Wicket Takers (All Time)')
    all_time_wickets = compute_bowling_insights(combined_df, min_balls=1, sort_by='wickets')
    st.dataframe(
        all_time_wickets.head(10).reset_index().rename(columns={
            'index': 'Bowler',
            'runs_conceded': 'Runs Conceded',
            'balls_bowled': 'Balls Bowled',
            'wickets': 'Total Wickets',
            'economy_rate': 'Economy Rate'
        }),
        height=400
    )

    st.subheader('📉 Top Economy Rates (Min 30 Balls)')
    if not bowling_insights.empty:
        st.dataframe(
            bowling_insights.head(10).reset_index().rename(columns={
                'index': 'Bowler',
                'runs_conceded': 'Runs Conceded',
                'balls_bowled': 'Balls Bowled',
                'wickets': 'Wickets',
                'economy_rate': 'Economy Rate'
            }),
            height=320
        )
    else:
        st.info('No bowling data available for economy ranking.')

def show_season_analysis(matches_df, selected_season):
    """Display season-specific analysis"""
    st.title('🏏 IPL Data Analysis Dashboard')
    st.header(f'📅 Season {selected_season} Analysis')
    
    season_data = matches_df[matches_df['season'] == selected_season]
    
    # Season statistics
    total_matches = len(season_data)
    total_teams = len(set(season_data['team1'].tolist() + season_data['team2'].tolist()))
    # Safer winner selection: use mode of non-null winners or 'N/A'
    if not season_data.empty and not season_data['winner'].dropna().empty:
        winner_abbr = season_data['winner'].dropna().mode().iloc[0]
    else:
        winner_abbr = 'N/A'
    winner = get_full_team_name(winner_abbr)

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total Matches", total_matches)
    with col2: st.metric("Teams Participated", total_teams)
    with col3: st.metric("Season Winner", winner)

    # Team performance
    st.subheader('🏆 Team Performance')
    # Team wins for the season (ignore missing winners)
    team_wins = season_data['winner'].dropna().value_counts()
    team_wins_full = pd.Series({get_full_team_name(t): w for t, w in team_wins.items()})

    if team_wins_full.empty:
        st.warning(f"No wins recorded for season {selected_season}")
    else:
        fig, ax = plt.subplots(figsize=(14, 8))
        sns.barplot(
            x=team_wins_full.values,
            y=team_wins_full.index,
            hue=team_wins_full.index,
            palette='mako',
            legend=False,
            ax=ax
        )
        ax.set_title(f'Team Wins in {selected_season}', fontsize=16)
        ax.set_xlabel('Number of Wins')
        ax.set_ylabel('Teams')
        plt.tight_layout()
        st.pyplot(fig)

    # Get season deliveries data for player stats
    season_match_ids = season_data['id'].tolist()
    
    # Load combined data for player analysis
    matches_df_temp, deliveries_df_temp, combined_df_temp = load_data()
    season_combined_df = combined_df_temp[combined_df_temp['match_id'].isin(season_match_ids)]
    
    if not season_combined_df.empty:
        season_batting_insights = compute_batting_insights(season_combined_df, min_balls=50)
        season_bowling_insights = compute_bowling_insights(season_combined_df, min_balls=30)

        st.subheader('✨ Season Highlights')
        col1, col2, col3, col4 = st.columns(4)
        top_batter_name = season_batting_insights.index[0] if not season_batting_insights.empty else 'N/A'
        top_bowler_name = season_bowling_insights.index[0] if not season_bowling_insights.empty else 'N/A'
        top_batter_runs = int(season_batting_insights.iloc[0]['runs']) if not season_batting_insights.empty else 0
        top_batter_sr = float(season_batting_insights.iloc[0]['strike_rate']) if not season_batting_insights.empty else 0.0
        top_bowler_wickets = int(season_bowling_insights.iloc[0]['wickets']) if not season_bowling_insights.empty else 0
        top_bowler_economy = float(season_bowling_insights.iloc[0]['economy_rate']) if not season_bowling_insights.empty else 0.0

        with col1:
            st.metric('Best Batting Runs', top_batter_name, delta=f'{top_batter_runs} runs')
        with col2:
            st.metric('Best Strike Rate', top_batter_name, delta=f'{top_batter_sr:.1f}')
        with col3:
            st.metric('Most Wickets', top_bowler_name, delta=f'{top_bowler_wickets} wickets')
        with col4:
            st.metric('Best Economy', top_bowler_name, delta=f'{top_bowler_economy:.2f}')

        # Top 10 Batsmen in the season
        st.subheader(f'🏏 Top 10 Batsmen - Season {selected_season}')
        
        # Check for correct column names
        batter_col = 'batter' if 'batter' in season_combined_df.columns else 'batsman'
        runs_col = 'batsman_runs' if 'batsman_runs' in season_combined_df.columns else 'batsman_run'
        
        if batter_col in season_combined_df.columns and runs_col in season_combined_df.columns:
            season_batting_stats = season_combined_df.groupby(batter_col).agg({
                runs_col: ['sum', 'count']
            })
            season_batting_stats.columns = ['Total Runs', 'Balls Faced']
            season_batting_stats['Strike Rate'] = (season_batting_stats['Total Runs'] / season_batting_stats['Balls Faced']) * 100
            season_batting_stats = season_batting_stats.sort_values('Total Runs', ascending=False)
            
            # Filter batsmen with minimum 50 balls
            season_batting_filtered = season_batting_stats[season_batting_stats['Balls Faced'] >= 50]
            
            if not season_batting_filtered.empty:
                top_10_batsmen = season_batting_filtered.head(10)
                
                # Display top 3 in metrics
                col1, col2, col3 = st.columns(3)
                medals = ['🥇', '🥈', '🥉']
                for i in range(min(3, len(top_10_batsmen))):
                    with [col1, col2, col3][i]:
                        st.metric(
                            label=f"{medals[i]} {top_10_batsmen.index[i]}",
                            value=f"{int(top_10_batsmen.iloc[i]['Total Runs'])} runs",
                            delta=f"SR: {top_10_batsmen.iloc[i]['Strike Rate']:.1f}"
                        )
                
                # Visualization
                fig, ax = plt.subplots(figsize=(14, 8))
                sns.barplot(
                    x=top_10_batsmen['Total Runs'].values,
                    y=top_10_batsmen.index,
                    hue=top_10_batsmen.index,
                    palette='viridis',
                    legend=False,
                    ax=ax
                )
                ax.set_title(f'Top 10 Run Scorers - Season {selected_season}', fontsize=16, fontweight='bold')
                ax.set_xlabel('Total Runs')
                ax.set_ylabel('Batsman')
                ax.grid(axis='x', linestyle='--', alpha=0.7)
                plt.tight_layout()
                st.pyplot(fig)
                
                # Detailed table
                st.dataframe(top_10_batsmen.round(2), height=400)
            else:
                st.warning(f"No batsmen with minimum 50 balls found for season {selected_season}")
        
        # Top 10 Bowlers in the season
        st.subheader(f'🎯 Top 10 Bowlers - Season {selected_season}')
        
        if 'bowler' in season_combined_df.columns:
            # Filter for valid dismissals
            valid_dismissals = season_combined_df[
                season_combined_df['dismissal_kind'].notna() & 
                (season_combined_df['dismissal_kind'] != 'run out') &
                (season_combined_df['dismissal_kind'].str.strip() != '')
            ]
            
            # Calculate bowling stats
            season_bowling_stats = season_combined_df.groupby('bowler').agg({
                'total_runs': 'sum',
                'ball': 'count'
            }).rename(columns={
                'total_runs': 'Runs Conceded',
                'ball': 'Balls Bowled'
            })
            
            # Calculate wickets
            if not valid_dismissals.empty:
                wicket_stats = valid_dismissals.groupby('bowler').size().rename('Wickets')
                season_bowling_stats = season_bowling_stats.join(wicket_stats, how='left').fillna(0)
            else:
                season_bowling_stats['Wickets'] = 0
            
            season_bowling_stats['Wickets'] = season_bowling_stats['Wickets'].astype(int)
            season_bowling_stats['Economy Rate'] = (season_bowling_stats['Runs Conceded'] / season_bowling_stats['Balls Bowled']) * 6
            season_bowling_stats = season_bowling_stats.sort_values('Wickets', ascending=False)
            
            # Filter bowlers with minimum 30 balls (5 overs)
            season_bowling_filtered = season_bowling_stats[season_bowling_stats['Balls Bowled'] >= 30]
            
            if not season_bowling_filtered.empty:
                top_10_bowlers = season_bowling_filtered.head(10)
                
                # Display top 3 in metrics
                col1, col2, col3 = st.columns(3)
                medals = ['🥇', '🥈', '🥉']
                for i in range(min(3, len(top_10_bowlers))):
                    with [col1, col2, col3][i]:
                        st.metric(
                            label=f"{medals[i]} {top_10_bowlers.index[i]}",
                            value=f"{int(top_10_bowlers.iloc[i]['Wickets'])} wickets",
                            delta=f"ER: {top_10_bowlers.iloc[i]['Economy Rate']:.2f}"
                        )
                
                # Visualization
                fig, ax = plt.subplots(figsize=(14, 8))
                sns.barplot(
                    x=top_10_bowlers['Wickets'].values,
                    y=top_10_bowlers.index,
                    hue=top_10_bowlers.index,
                    palette='plasma',
                    legend=False,
                    ax=ax
                )
                ax.set_title(f'Top 10 Wicket Takers - Season {selected_season}', fontsize=16, fontweight='bold')
                ax.set_xlabel('Total Wickets')
                ax.set_ylabel('Bowler')
                ax.grid(axis='x', linestyle='--', alpha=0.7)
                plt.tight_layout()
                st.pyplot(fig)
                
                # Detailed table
                st.dataframe(top_10_bowlers.round(2), height=400)
            else:
                st.warning(f"No bowlers with minimum 5 overs found for season {selected_season}")
    else:
        st.warning(f"No ball-by-ball data available for season {selected_season}")

def show_team_analysis(matches_df):
    """Display team-specific analysis"""
    st.title('🏏 IPL Data Analysis Dashboard')
    st.header('🏏 Team Analysis')
    
    teams = sorted(pd.concat([matches_df['team1'], matches_df['team2']]).dropna().unique())
    selected_team = st.selectbox('Select Team', teams)
    
    team_matches = matches_df[(matches_df['team1'] == selected_team) | (matches_df['team2'] == selected_team)]
    total_matches = len(team_matches)
    matches_won = (team_matches['winner'] == selected_team).sum()
    win_percentage = (matches_won / total_matches * 100) if total_matches else 0

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total Matches", total_matches)
    with col2: st.metric("Matches Won", int(matches_won))
    with col3: st.metric("Win Percentage", f"{win_percentage:.1f}%")

    # Season-wise performance
    st.subheader('📈 Season-wise Wins')
    season_wins = team_matches[team_matches['winner'] == selected_team]['season'].dropna().value_counts().sort_index()

    if season_wins.empty:
        st.warning(f"No wins found for {selected_team}")
    else:
        fig, ax = plt.subplots(figsize=(14, 8))
        sns.barplot(
            x=season_wins.index.astype(str), 
            y=season_wins.values, 
            hue=season_wins.index.astype(str),
            palette='mako', 
            legend=False,
            ax=ax
        )
        ax.set_title(f'{selected_team} - Wins by Season')
        ax.set_xlabel('Season')
        ax.set_ylabel('Wins')
        plt.xticks(rotation=45)
        st.pyplot(fig)

def show_player_stats(combined_df, seasons):
    """Display player statistics"""
    st.title('🏏 IPL Data Analysis Dashboard')
    st.header('👤 Player Statistics')
    
    # Get all unique players for search
    batter_col = 'batter' if 'batter' in combined_df.columns else 'batsman'
    runs_col = 'batsman_runs' if 'batsman_runs' in combined_df.columns else 'batsman_run'
    
    all_batters = sorted(combined_df[batter_col].dropna().unique()) if batter_col in combined_df.columns else []
    all_bowlers = sorted(combined_df['bowler'].dropna().unique()) if 'bowler' in combined_df.columns else []
    all_players = sorted(list(set(all_batters + all_bowlers)))
    
    # Player search
    st.subheader('🔍 Search Player')
    selected_player = st.selectbox(
        'Search and select a player:',
        [''] + all_players,
        help="Type to search for a player name"
    )
    
    if not selected_player:
        st.info("Please select a player to view their statistics across all seasons.")
        return
    
    st.write(f"**Analyzing data for: {selected_player}**")
    
    # Player batting statistics across all seasons
    st.subheader(f'🏏 {selected_player} - Batting Statistics')
    
    if batter_col in combined_df.columns and runs_col in combined_df.columns:
        player_batting = combined_df[combined_df[batter_col] == selected_player]

        if not player_batting.empty:
            # Overall batting stats
            total_runs = player_batting[runs_col].sum()
            total_balls = len(player_batting)
            strike_rate = (total_runs / total_balls * 100) if total_balls > 0 else 0

            # Season-wise batting breakdown
            season_batting = player_batting.groupby('season').agg({
                runs_col: ['sum', 'count']
            })
            season_batting.columns = ['Runs', 'Balls']
            season_batting['Strike Rate'] = (season_batting['Runs'] / season_batting['Balls']) * 100
            season_batting = season_batting.sort_values('Runs', ascending=False)

            # Display overall metrics
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Total Runs", f"{total_runs:,}")
            with col2: st.metric("Total Balls", f"{total_balls:,}")
            with col3: st.metric("Overall Strike Rate", f"{strike_rate:.1f}")

            if len(season_batting) > 1:
                # Season-wise performance chart
                fig, ax = plt.subplots(figsize=(14, 8))
                sns.barplot(
                    x=season_batting.index.astype(str),
                    y=season_batting['Runs'].values,
                    hue=season_batting.index.astype(str),
                    palette='viridis',
                    legend=False,
                    ax=ax
                )
                ax.set_title(f'{selected_player} - Runs by Season', fontsize=16, fontweight='bold')
                ax.set_xlabel('Season')
                ax.set_ylabel('Runs')
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(fig)

            # Detailed season-wise table
            st.write("**Season-wise Batting Performance:**")
            st.dataframe(season_batting.round(2), height=300)

            # Best season
            if not season_batting.empty:
                best_season = season_batting['Runs'].idxmax()
                best_runs = int(season_batting.loc[best_season, 'Runs'])
                st.success(f"🏆 Best Season: {best_season} with {best_runs} runs")
        else:
            st.warning(f"{selected_player} has no batting records in the dataset.")
    
    # Player bowling statistics across all seasons
    st.subheader(f'🎯 {selected_player} - Bowling Statistics')
    
    if 'bowler' in combined_df.columns:
        player_bowling = combined_df[combined_df['bowler'] == selected_player]
        
        if not player_bowling.empty:
            # Filter for valid dismissals
            player_wickets = player_bowling[
                player_bowling['dismissal_kind'].notna() & 
                (player_bowling['dismissal_kind'] != 'run out') &
                (player_bowling['dismissal_kind'].str.strip() != '')
            ]
            
            # Overall bowling stats
            total_wickets = len(player_wickets)
            total_runs_conceded = player_bowling['total_runs'].sum()
            total_balls_bowled = len(player_bowling)
            economy_rate = (total_runs_conceded / total_balls_bowled * 6) if total_balls_bowled > 0 else 0
            
            # Season-wise bowling breakdown
            season_bowling_stats = player_bowling.groupby('season').agg({
                'total_runs': 'sum',
                'ball': 'count'
            }).rename(columns={
                'total_runs': 'Runs Conceded',
                'ball': 'Balls Bowled'
            })
            
            # Add wickets per season
            if not player_wickets.empty:
                season_wickets = player_wickets.groupby('season').size().rename('Wickets')
                season_bowling_stats = season_bowling_stats.join(season_wickets, how='left').fillna(0)
            else:
                season_bowling_stats['Wickets'] = 0
            
            season_bowling_stats['Wickets'] = season_bowling_stats['Wickets'].astype(int)
            season_bowling_stats['Economy Rate'] = (season_bowling_stats['Runs Conceded'] / season_bowling_stats['Balls Bowled']) * 6
            season_bowling_stats = season_bowling_stats.sort_values('Wickets', ascending=False)
            
            # Display overall metrics
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Total Wickets", f"{total_wickets}")
            with col2: st.metric("Total Balls Bowled", f"{total_balls_bowled:,}")
            with col3: st.metric("Overall Economy Rate", f"{economy_rate:.2f}")
            
            if len(season_bowling_stats) > 1:
                # Season-wise wickets chart
                fig, ax = plt.subplots(figsize=(14, 8))
                sns.barplot(
                    x=season_bowling_stats.index.astype(str),
                    y=season_bowling_stats['Wickets'].values,
                    hue=season_bowling_stats.index.astype(str),
                    palette='plasma',
                    legend=False,
                    ax=ax
                )
                ax.set_title(f'{selected_player} - Wickets by Season', fontsize=16, fontweight='bold')
                ax.set_xlabel('Season')
                ax.set_ylabel('Wickets')
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(fig)
            
            # Detailed season-wise table
            st.write("**Season-wise Bowling Performance:**")
            st.dataframe(season_bowling_stats.round(2), height=300)
            
            # Best bowling season
            if total_wickets > 0:
                best_bowling_season = season_bowling_stats['Wickets'].idxmax()
                best_wickets = int(season_bowling_stats.loc[best_bowling_season, 'Wickets'])
                st.success(f"🏆 Best Bowling Season: {best_bowling_season} with {best_wickets} wickets")
        else:
            st.warning(f"{selected_player} has no bowling records in the dataset.")
    
    # Player career summary
    st.subheader(f'📈 {selected_player} - Career Summary')
    
    # Get all seasons the player participated in
    batting_seasons = set()
    bowling_seasons = set()
    
    if batter_col in combined_df.columns:
        player_batting_seasons = combined_df[combined_df[batter_col] == selected_player]['season'].unique()
        batting_seasons = set(player_batting_seasons)
    
    if 'bowler' in combined_df.columns:
        player_bowling_seasons = combined_df[combined_df['bowler'] == selected_player]['season'].unique()
        bowling_seasons = set(player_bowling_seasons)
    
    all_player_seasons = sorted(batting_seasons.union(bowling_seasons))
    
    if all_player_seasons:
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Seasons Played", len(all_player_seasons))
        with col2: st.metric("Career Span", f"{min(all_player_seasons)} - {max(all_player_seasons)}")
        with col3: st.metric("Active Years", len(all_player_seasons))
        
        st.write(f"**Seasons participated:** {', '.join(map(str, all_player_seasons))}")
    else:
        st.error(f"No data found for player: {selected_player}")

def show_venue_stats(matches_df):
    """Display venue statistics"""
    st.title('🏏 IPL Data Analysis Dashboard')
    st.header('🏟️ Venue Statistics')
    
    venues = sorted(matches_df['venue'].dropna().unique())
    selected_venue = st.selectbox('Select Venue', venues)
    
    venue_matches = matches_df[matches_df['venue'] == selected_venue]
    st.write(f"Total Matches: {len(venue_matches)}")
    
    venue_wins = venue_matches['winner'].value_counts()
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.barplot(
        x=venue_wins.values, 
        y=venue_wins.index, 
        hue=venue_wins.index,
        palette='coolwarm', 
        legend=False,
        ax=ax
    )
    ax.set_title(f'Team Performance at {selected_venue}')
    ax.set_xlabel('Wins')
    ax.set_ylabel('Team')
    st.pyplot(fig)

def show_comparison(matches_df, combined_df):
    """Display comparison dashboard for teams and players."""
    st.title('🏏 IPL Data Analysis Dashboard')
    st.header('🔍 Comparison Hub')
    st.caption('Compare teams and players side by side to uncover standout performers and trends.')

    compare_mode = st.radio('Choose comparison type', ['Team vs Team', 'Player vs Player'], horizontal=True)

    if compare_mode == 'Team vs Team':
        teams = sorted(pd.concat([matches_df['team1'], matches_df['team2']]).dropna().unique())
        col1, col2 = st.columns(2)
        with col1:
            team1 = st.selectbox('Select Team 1', teams, key='comp_team1')
        with col2:
            team2 = st.selectbox('Select Team 2', [t for t in teams if t != team1], key='comp_team2')

        summary1 = get_team_summary(matches_df, team1)
        summary2 = get_team_summary(matches_df, team2)

        st.subheader(f'{team1} vs {team2}')
        comparison_df = pd.DataFrame({
            'Metric': ['Total Matches', 'Matches Won', 'Win Percentage'],
            team1: [summary1['total_matches'], summary1['matches_won'], f"{summary1['win_percentage']:.1f}%"],
            team2: [summary2['total_matches'], summary2['matches_won'], f"{summary2['win_percentage']:.1f}%"],
        })
        st.dataframe(comparison_df, hide_index=True)

        fig, ax = plt.subplots(figsize=(10, 4))
        labels = ['Matches Won', 'Win %']
        values1 = [summary1['matches_won'], summary1['win_percentage']]
        values2 = [summary2['matches_won'], summary2['win_percentage']]
        x = range(len(labels))
        ax.bar([i - 0.2 for i in x], values1, width=0.35, label=team1, color='#FF4B4B')
        ax.bar([i + 0.2 for i in x], values2, width=0.35, label=team2, color='#4CAF50')
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels)
        ax.set_ylabel('Value')
        ax.set_title('Team Comparison')
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)
    else:
        batter_col = 'batter' if 'batter' in combined_df.columns else 'batsman'
        all_batters = sorted(combined_df[batter_col].dropna().unique()) if batter_col in combined_df.columns else []
        all_bowlers = sorted(combined_df['bowler'].dropna().unique()) if 'bowler' in combined_df.columns else []
        all_players = sorted(list(set(all_batters + all_bowlers)))

        col1, col2 = st.columns(2)
        with col1:
            player1 = st.selectbox('Select Player 1', all_players, key='comp_player1')
        with col2:
            player2 = st.selectbox('Select Player 2', [p for p in all_players if p != player1], key='comp_player2')

        summary1 = get_player_summary(combined_df, player1)
        summary2 = get_player_summary(combined_df, player2)

        st.subheader(f'{player1} vs {player2}')
        comparison_df = pd.DataFrame({
            'Metric': ['Runs', 'Balls Faced', 'Strike Rate', 'Wickets', 'Economy Rate', 'Seasons Played'],
            player1: [summary1['runs'], summary1['balls_faced'], f"{summary1['strike_rate']:.2f}", summary1['wickets'], f"{summary1['economy_rate']:.2f}", len(summary1['seasons'])],
            player2: [summary2['runs'], summary2['balls_faced'], f"{summary2['strike_rate']:.2f}", summary2['wickets'], f"{summary2['economy_rate']:.2f}", len(summary2['seasons'])],
        })
        st.dataframe(comparison_df, hide_index=True)

        fig, ax = plt.subplots(figsize=(10, 4))
        labels = ['Runs', 'Strike Rate', 'Wickets']
        values1 = [summary1['runs'], summary1['strike_rate'], summary1['wickets']]
        values2 = [summary2['runs'], summary2['strike_rate'], summary2['wickets']]
        x = range(len(labels))
        ax.bar([i - 0.2 for i in x], values1, width=0.35, label=player1, color='#FF4B4B')
        ax.bar([i + 0.2 for i in x], values2, width=0.35, label=player2, color='#4CAF50')
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels)
        ax.set_ylabel('Value')
        ax.set_title('Player Comparison')
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)


def show_head_to_head(matches_df):
    """Display head-to-head analysis"""
    st.title('🏏 IPL Data Analysis Dashboard')
    st.header('🤝 Head to Head Analysis')
    
    teams = sorted(pd.concat([matches_df['team1'], matches_df['team2']]).dropna().unique())
    team1 = st.selectbox('Select Team 1', teams, key='h2h_t1')
    team2 = st.selectbox('Select Team 2', [t for t in teams if t != team1], key='h2h_t2')
    
    h2h_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) |
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if not h2h_matches.empty:
        st.write(f"Total Matches: {len(h2h_matches)}")
        h2h_stats = h2h_matches['winner'].value_counts()
        st.write("Head to Head Record:")
        st.dataframe(
            h2h_stats.rename('Wins').reset_index().rename(columns={'index': 'Team'}),
            height=240
        )
        
        fig, ax = plt.subplots(figsize=(14, 8))
        sns.barplot(
            x=h2h_stats.values, 
            y=h2h_stats.index, 
            hue=h2h_stats.index,
            palette='coolwarm', 
            legend=False,
            ax=ax
        )
        ax.set_title(f'Head to Head: {team1} vs {team2}')
        ax.set_xlabel('Wins')
        ax.set_ylabel('Team')
        st.pyplot(fig)
        
        # Match selection dropdown
        st.subheader('📅 Select Specific Match')
        h2h_matches_display = h2h_matches.copy()
        h2h_matches_display['match_display'] = (
            h2h_matches_display['season'].astype(str) + ' - ' +
            h2h_matches_display['team1'] + ' vs ' + h2h_matches_display['team2'] + 
            ' (' + h2h_matches_display['date'].astype(str) + ')'
        )
        
        selected_match_display = st.selectbox(
            'Choose a match to view details:',
            ['All Matches'] + h2h_matches_display['match_display'].tolist(),
            key='match_selector'
        )
        
        # Get match IDs for player analysis
        if selected_match_display == 'All Matches':
            h2h_match_ids = h2h_matches['id'].tolist()
            analysis_title = f"All {team1} vs {team2} Matches"
        else:
            selected_match = h2h_matches_display[h2h_matches_display['match_display'] == selected_match_display]
            h2h_match_ids = selected_match['id'].tolist()
            analysis_title = f"Selected Match: {selected_match_display}"
            
            # Display match details
            st.subheader('🏟️ Match Details')
            match_info = selected_match.iloc[0]
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Season", match_info['season'])
            with col2: st.metric("Date", match_info['date'])
            with col3: st.metric("Venue", match_info['venue'])
            with col4: st.metric("Winner", match_info['winner'])
            
            # Additional match info
            if 'toss_winner' in match_info:
                col1, col2 = st.columns(2)
                with col1: st.info(f"🪙 Toss Winner: {match_info['toss_winner']}")
                with col2: st.info(f"🎯 Toss Decision: {match_info.get('toss_decision', 'N/A')}")
        
        # Load combined data for player analysis
        matches_df_temp, deliveries_df_temp, combined_df_temp = load_data()
        h2h_combined_df = combined_df_temp[combined_df_temp['match_id'].isin(h2h_match_ids)]
        
        if not h2h_combined_df.empty:
            # Top 5 Batsmen in selected matches
            st.subheader(f'🏏 Top 5 Batsmen in {analysis_title}')
            
            batter_col = 'batter' if 'batter' in h2h_combined_df.columns else 'batsman'
            runs_col = 'batsman_runs' if 'batsman_runs' in h2h_combined_df.columns else 'batsman_run'
            
            if batter_col in h2h_combined_df.columns and runs_col in h2h_combined_df.columns:
                h2h_batting_stats = h2h_combined_df.groupby(batter_col).agg({
                    runs_col: ['sum', 'count']
                })
                h2h_batting_stats.columns = ['Total Runs', 'Balls Faced']
                h2h_batting_stats['Strike Rate'] = (h2h_batting_stats['Total Runs'] / h2h_batting_stats['Balls Faced']) * 100
                h2h_batting_stats = h2h_batting_stats.sort_values('Total Runs', ascending=False)
                
                # Adjust minimum balls based on selection
                min_balls = 10 if selected_match_display != 'All Matches' else 20
                h2h_batting_filtered = h2h_batting_stats[h2h_batting_stats['Balls Faced'] >= min_balls]
                
                if not h2h_batting_filtered.empty:
                    top_5_batsmen = h2h_batting_filtered.head(5)
                    
                    # Display top 3 in metrics
                    if len(top_5_batsmen) >= 3:
                        col1, col2, col3 = st.columns(3)
                        medals = ['🥇', '🥈', '🥉']
                        for i in range(3):
                            with [col1, col2, col3][i]:
                                st.metric(
                                    label=f"{medals[i]} {top_5_batsmen.index[i]}",
                                    value=f"{int(top_5_batsmen.iloc[i]['Total Runs'])} runs",
                                    delta=f"SR: {top_5_batsmen.iloc[i]['Strike Rate']:.1f}"
                                )
                    
                    # Visualization
                    fig, ax = plt.subplots(figsize=(14, 8))
                    sns.barplot(
                        x=top_5_batsmen['Total Runs'].values,
                        y=top_5_batsmen.index,
                        hue=top_5_batsmen.index,
                        palette='viridis',
                        legend=False,
                        ax=ax
                    )
                    ax.set_title(f'Top 5 Run Scorers - {analysis_title}', fontsize=16, fontweight='bold')
                    ax.set_xlabel('Total Runs')
                    ax.set_ylabel('Batsman')
                    ax.grid(axis='x', linestyle='--', alpha=0.7)
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    # Detailed table
                    st.dataframe(top_5_batsmen.round(2), height=300)
                else:
                    st.warning(f"No batsmen with minimum {min_balls} balls found in selected match(es)")
            
            # Top 5 Bowlers in selected matches
            st.subheader(f'🎯 Top 5 Bowlers in {analysis_title}')
            
            if 'bowler' in h2h_combined_df.columns:
                # Filter for valid dismissals
                h2h_valid_dismissals = h2h_combined_df[
                    h2h_combined_df['dismissal_kind'].notna() & 
                    (h2h_combined_df['dismissal_kind'] != 'run out') &
                    (h2h_combined_df['dismissal_kind'].str.strip() != '')
                ]
                
                # Calculate bowling stats
                h2h_bowling_stats = h2h_combined_df.groupby('bowler').agg({
                    'total_runs': 'sum',
                    'ball': 'count'
                }).rename(columns={
                    'total_runs': 'Runs Conceded',
                    'ball': 'Balls Bowled'
                })
                
                # Calculate wickets
                if not h2h_valid_dismissals.empty:
                    h2h_wicket_stats = h2h_valid_dismissals.groupby('bowler').size().rename('Wickets')
                    h2h_bowling_stats = h2h_bowling_stats.join(h2h_wicket_stats, how='left').fillna(0)
                else:
                    h2h_bowling_stats['Wickets'] = 0
                
                h2h_bowling_stats['Wickets'] = h2h_bowling_stats['Wickets'].astype(int)
                h2h_bowling_stats['Economy Rate'] = (h2h_bowling_stats['Runs Conceded'] / h2h_bowling_stats['Balls Bowled']) * 6
                h2h_bowling_stats = h2h_bowling_stats.sort_values('Wickets', ascending=False)
                
                # Adjust minimum balls based on selection
                min_balls = 6 if selected_match_display != 'All Matches' else 18
                h2h_bowling_filtered = h2h_bowling_stats[h2h_bowling_stats['Balls Bowled'] >= min_balls]
                
                if not h2h_bowling_filtered.empty:
                    top_5_bowlers = h2h_bowling_filtered.head(5)
                    
                    # Display top 3 in metrics
                    if len(top_5_bowlers) >= 3:
                        col1, col2, col3 = st.columns(3)
                        medals = ['🥇', '🥈', '🥉']
                        for i in range(3):
                            with [col1, col2, col3][i]:
                                st.metric(
                                    label=f"{medals[i]} {top_5_bowlers.index[i]}",
                                    value=f"{int(top_5_bowlers.iloc[i]['Wickets'])} wickets",
                                    delta=f"ER: {top_5_bowlers.iloc[i]['Economy Rate']:.2f}"
                                )
                    
                    # Visualization
                    fig, ax = plt.subplots(figsize=(14, 8))
                    sns.barplot(
                        x=top_5_bowlers['Wickets'].values,
                        y=top_5_bowlers.index,
                        hue=top_5_bowlers.index,
                        palette='plasma',
                        legend=False,
                        ax=ax
                    )
                    ax.set_title(f'Top 5 Wicket Takers - {analysis_title}', fontsize=16, fontweight='bold')
                    ax.set_xlabel('Total Wickets')
                    ax.set_ylabel('Bowler')
                    ax.grid(axis='x', linestyle='--', alpha=0.7)
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    # Detailed table
                    st.dataframe(top_5_bowlers.round(2), height=300)
                else:
                    overs = min_balls // 6
                    st.warning(f"No bowlers with minimum {overs} over(s) found in selected match(es)")
        else:
            st.warning(f"No ball-by-ball data available for selected match(es)")
    else:
        st.info("No matches found between these teams.")

def main():
    """Main application function"""
    st.set_page_config(
        page_title='IPL Data Analytics Dashboard',
        page_icon='🏏',
        layout='wide'
    )

    # Load data
    matches_df, deliveries_df, combined_df = load_data()

    # Load custom CSS safely
    try:
        with open('static/style.css', 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

    # Session state initialization
    seasons = sorted(matches_df['season'].unique())
    if 'selected_season' not in st.session_state:
        st.session_state.selected_season = seasons[0]

    # Sidebar setup
    logo_path = Path(__file__).resolve().parent / 'static' / 'Indian_Premier_League_Official_Logo.svg'
    with open(logo_path, 'rb') as logo_file:
        logo_data = base64.b64encode(logo_file.read()).decode('utf-8')
    st.sidebar.markdown(
        f'<img src="data:image/svg+xml;base64,{logo_data}" style="width:240px; max-width:100%; height:auto; display:block; margin-bottom:0.75rem;" alt="Indian Premier League logo" />',
        unsafe_allow_html=True,
    )
    st.sidebar.title("Navigation")
    
    # Navigation
    page = st.sidebar.radio(
        "Select Page",
        ["Overview", "Season Analysis", "Team Analysis", "Player Stats", "Venue Stats", "Head to Head", "Comparison Hub"]
    )
    
    # Season selector
    st.session_state.selected_season = st.sidebar.selectbox(
        "Season",
        seasons,
        index=seasons.index(st.session_state.selected_season)
    )

    # Page routing
    if page == "Overview":
        show_overview(matches_df, deliveries_df, combined_df)
    elif page == "Season Analysis":
        show_season_analysis(matches_df, st.session_state.selected_season)
    elif page == "Team Analysis":
        show_team_analysis(matches_df)
    elif page == "Player Stats":
        show_player_stats(combined_df, seasons)
    elif page == "Venue Stats":
        show_venue_stats(matches_df)
    elif page == "Head to Head":
        show_head_to_head(matches_df)
    elif page == "Comparison Hub":
        show_comparison(matches_df, combined_df)

if __name__ == '__main__':
    main()

