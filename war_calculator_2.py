import pandas as pd
import pybaseball

# Start with Lahman, all 2025 batting seasons
lahman = pd.read_csv("Batting.csv")
batting_2025 = lahman[lahman['yearID'] == 2025]
# Calculate PA, wobaPA, UBB
batting_2025['UBB'] = batting_2025['BB'] - batting_2025['IBB']
batting_2025['PA'] = batting_2025['AB'] + batting_2025['BB'] + batting_2025['HBP'] + batting_2025['SF'] + batting_2025['SH']
batting_2025['wobaPA'] = batting_2025['AB'] + batting_2025['UBB'] + batting_2025['HBP'] + batting_2025['SF'] # IBB and SH don't count for wOBA because they are managers decisions(?)
batting_2025['1B'] = batting_2025['H'] - batting_2025['2B'] - batting_2025['3B'] - batting_2025['HR']
# Calculate woba
woba_guts = pd.read_csv("woba_guts.csv")
woba_guts = woba_guts[woba_guts['Season'] == 2025].iloc[0] # to make it a Series
print(woba_guts)
batting_2025['woba'] = (
    woba_guts['wBB'] * batting_2025['UBB'] +
    woba_guts['wHBP'] * batting_2025['HBP'] +
    woba_guts['w1B'] * batting_2025['1B'] +
    woba_guts['w2B'] * batting_2025['2B'] +
    woba_guts['w3B'] * batting_2025['3B']
    + woba_guts['wHR'] * batting_2025['HR']
) / batting_2025['wobaPA']

batting_2025['wraa_nonpf'] =  (batting_2025['woba'] - woba_guts['wOBA']) / woba_guts['wOBAScale'] * batting_2025['PA']
print(batting_2025.head())
# merge park factors left on teamName, right on Team
park_factors = pd.read_csv("park_factors_guts.csv")
park_factors.rename(columns={"Basic (5yr)": "BPF"}, inplace=True)


# stealing runs
batting_2025['stealing_runs'] = woba_guts['runSB'] * batting_2025['SB'] + woba_guts['runCS'] * batting_2025['CS']


# save hitting leaderboard to csv

# Add Defense
fielding_2025 = pybaseball.fielding_stats(2025)


# merge in ids from chadwick_register/data/people_combined.csv
chadwick_people = pd.read_csv("people_combined.csv")
batting_2025 = batting_2025.merge(chadwick_people, left_on='playerID', right_on='key_bbref', how='left')
batting_2025 = batting_2025.merge(fielding_2025[['IDfg', 'DRS', 'UZR']], left_on='key_fangraphs', right_on='IDfg', how='left')

# Positional adjustments
CATCHER_RUNS = 12.5
FIRST_BASE_RUNS = -12.5
SECOND_BASE_RUNS = 2.5
THIRD_BASE_RUNS = 2.5
SHORTSTOP_RUNS = 7.5
LEFT_FIELD_RUNS = -7.5
CENTER_FIELD_RUNS = 2.5
RIGHT_FIELD_RUNS = -7.5
DESIGNATED_HITTER_RUNS = -17.5

lahman_fielding = pd.read_csv("Fielding.csv")
lahman_fielding = lahman_fielding[lahman_fielding['yearID'] == 2025]
lahman_fielding['innings'] = lahman_fielding['InnOuts'] / 3
position_map = {
    'C': CATCHER_RUNS,
    '1B': FIRST_BASE_RUNS,
    '2B': SECOND_BASE_RUNS,
    '3B': THIRD_BASE_RUNS,
    'SS': SHORTSTOP_RUNS,
    'LF': LEFT_FIELD_RUNS,
    'CF': CENTER_FIELD_RUNS,
    'RF': RIGHT_FIELD_RUNS,
    'DH': DESIGNATED_HITTER_RUNS
}
lahman_fielding['positional_runs'] = lahman_fielding['POS'].map(position_map) * (lahman_fielding['innings'] / 9 / 162)
positional_runs = lahman_fielding.groupby('playerID')['positional_runs'].sum().reset_index()
batting_2025 = batting_2025.merge(positional_runs, on='playerID', how='left')
batting_2025['positional_runs'] = batting_2025['positional_runs'].fillna(0)
# Calculate runs above average
batting_2025['raa'] = batting_2025['wraa_nonpf'] + batting_2025['stealing_runs'] + batting_2025['DRS'].fillna(0) + batting_2025['positional_runs']

# Convert to replacement level - 20.5 runs below average per 600 PA
batting_2025['runs_above_replacement'] = batting_2025['raa'] + (20.5 / 600 * batting_2025['PA'])
batting_2025['WAR'] = batting_2025['runs_above_replacement'] / woba_guts['R/W']

# save to csv
batting_2025[['playerID', 'WAR']].to_csv('war_2025.csv', index=False)