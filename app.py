import os
import pandas as pd
import matplotlib.pyplot as plt  # type: ignore[import-not-found]
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
    all_time_runs = combined_df.groupby('batter')['batsman_runs'].sum().sort_values(ascending=False)
    st.dataframe(
        all_time_runs.head(10).rename('Total Runs').reset_index().rename(columns={'batter': 'Batter'}),
        height=400
    )

    # Top wicket takers
    st.subheader('🎯 Top 10 Wicket Takers (All Time)')
    all_time_wickets = combined_df[combined_df['dismissal_kind'].notna()].groupby('bowler').size().sort_values(ascending=False)
    st.dataframe(
        all_time_wickets.head(10).rename('Total Wickets').reset_index().rename(columns={'bowler': 'Bowler'}),
        height=400
    )

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
    st.sidebar.image("https://www.iplt20.com/assets/images/ipl-logo-new-old.png", width=200)
    st.sidebar.title("Navigation")
    
    # Navigation
    page = st.sidebar.radio(
        "Select Page",
        ["Overview", "Season Analysis", "Team Analysis", "Player Stats", "Venue Stats", "Head to Head"]
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

if __name__ == '__main__':
    main()

