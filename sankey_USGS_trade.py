# -*- coding: utf-8 -*-
"""
Created on Mon Dec  4 10:21:47 2023

@author: aaron
"""
# assumption: no country imports and exports without changing the product
import pandas as pd
import plotly.graph_objects as go
# from itertools import product

#%% User input / decisions

# MFA
second_threshold = 0.05 # this is the actual threshold for the USGS values after the impacts
usgs_threshold = 0.001 # threshold for share that countries must have in one of the stages (mining, smelting, refining) to be considered in the sankey
# Problem with usgs threshold: required for code (unclear why) + applied before adding LCA impacts --> changes the impact calculation as "other" is multiplied with RoW factors
scale_to_NL = True # if True than all values will be scaled for NL and the energy sector, if false the global values are shown
NL_share = 0.00808 # share of global refined copper going into NL ultimately (also in form of intermediates etc.) 
NL_energy_share = 0.2506 # share of copper in NL used for the energy sector

# Choice what to display
display = 'copper'
# display = 'ghg'
# display = 'land_use'
# display = 'water'

# Sankey style
highlight_LMIC = True # True means that the sankey will have colours grouped by high income and LMIC, false that colours are unique for each country
sankey_labels_absolute = True # if True, absolute numbers are shown in the sankey, otherwise percent

#%% Data import

# choice of year
year = 2019

# USGS data
usgs_mining = pd.read_excel("data/usgs_data.xlsx", sheet_name = 'mining')[['country',year]]
usgs_mining.rename(columns={year:'mining_tonnes'}, inplace=True)

usgs_smelting = pd.read_excel("data/usgs_data.xlsx", sheet_name = 'smelting')[['country',year]]
usgs_smelting.rename(columns={year:'smelting_tonnes'}, inplace=True)

usgs_refining = pd.read_excel("data/usgs_data.xlsx", sheet_name = 'refining')[['country',year]]
usgs_refining.rename(columns={year:'refining_tonnes'}, inplace=True)


# HS revision 1992
trade_data = pd.read_csv("data/BACI_HS92_V202301/BACI_HS92_Y"+str(year)+"_V202301.csv")
country_codes = pd.read_csv("data/BACI_HS92_V202301/country_codes_V202301.csv")
product_codes = pd.read_csv("data/BACI_HS92_V202301/product_codes_HS92_V202301.csv")

## HS revision 2017
# trade_data = pd.read_csv("data/BACI_HS17_V202301/BACI_HS17_Y"+str(year)+"_V202301.csv")
# country_codes = pd.read_csv("data/BACI_HS17_V202301/country_codes_V202301.csv")
# product_codes = pd.read_csv("data/BACI_HS17_V202301/product_codes_HS17_V202301.csv")

# renaming columns
trade_data.rename(columns={
                    't': 'year', 
                    'i': 'exporter_code', 
                    'j': 'importer_code', 
                    'k': 'hscode', 
                    'v': 'kUSD_current', 
                    'q': 'tonnes'},
                    inplace = True)


# Manual input of stages, hscodes to filter for and copper content of the products
copper_stages = pd.DataFrame({
                            'hscode': ['2603', '2620', '7401', '7402'],
                            'stage': ['mined', 'mined', 'smelted', 'smelted'],
                            'content': [0.3, 0.1, 0.6, 0.95]
                            })

# Changing the hscodes for merging later
trade_data['hscode'] = trade_data['hscode'].astype(str)
trade_data['hscode_short'] = trade_data['hscode'].str[:4]
copper_stages['hscode'] = copper_stages['hscode'].astype(str)

# Cleaning product dataframe for merging
product_codes = product_codes.drop(product_codes[product_codes['code'] == '9999AA'].index)

#%% Filtering for hscodes
copper_trade = trade_data[trade_data['hscode_short'].isin(copper_stages['hscode'])]

#%% Cleaning the resulting dataframe
copper_trade.reset_index(drop=True, inplace = True)
copper_trade.drop('year', axis = 1, inplace = True)
copper_trade = copper_trade[copper_trade['tonnes'] != '           NA']

#%% Adding country names, ISO3 codes and product names
copper_trade = pd.merge(copper_trade, country_codes[['country_code', 'country_name_full', 'iso_3digit_alpha']], left_on='exporter_code', right_on='country_code', how='left')
copper_trade = pd.merge(copper_trade, country_codes[['country_code', 'country_name_full', 'iso_3digit_alpha']], left_on='importer_code', right_on='country_code', how='left')
copper_trade = pd.merge(copper_trade, product_codes, left_on='hscode', right_on='code', how='left')

# Cleaning and renaming
copper_trade.drop(['exporter_code', 'importer_code', 'country_code_x', 'country_code_y', 'code'], axis = 1, inplace = True)

copper_trade.rename(columns={                
                    'iso_3digit_alpha_x': 'exporter_ISO3', 
                     'country_name_full_x': 'exporter',
                     'iso_3digit_alpha_y': 'importer_ISO3', 
                     'country_name_full_y': 'importer',
                     'description': 'product'},
                     inplace = True)


#%% Adding stages and copper content
copper_trade = pd.merge(copper_trade, copper_stages, left_on='hscode_short', right_on='hscode', how='left')

# Calculating the copper content of each flow
copper_trade['tonnes_copper'] = copper_trade['tonnes'].astype(float) * copper_trade['content']

# Cleaning and renaming
copper_trade.drop(['hscode_y', 'content'], axis = 1, inplace = True)
copper_trade.rename(columns={'hscode_x': 'hscode'}, inplace = True)

# Changing order of columns
copper_trade = copper_trade[['exporter_ISO3', 'exporter', 'importer_ISO3', 'importer', 'stage', 'hscode', 'hscode_short', 'product', 'kUSD_current', 'tonnes', 'tonnes_copper']]


#%% ---------------------------------------- USGS -------------------------------------

"""
countries only exporting / importing secondary production are filtered out 
sometimes not differentiated in USGS data ..> assumed that it is primary then
"""

usgs_data = pd.merge(usgs_mining, usgs_smelting, on='country', how='outer').merge(usgs_refining, on='country', how='outer')
usgs_data = usgs_data.sort_values(by='country', ascending= True)
usgs_data = usgs_data.fillna(0)

usgs_data['mining_share'] = usgs_data['mining_tonnes'] / usgs_data['mining_tonnes'].sum()
usgs_data['smelting_share'] = usgs_data['smelting_tonnes'] / usgs_data['smelting_tonnes'].sum()
usgs_data['refining_share'] = usgs_data['refining_tonnes'] / usgs_data['refining_tonnes'].sum()

# Harmonising names for countries in country_list (from USGS) and copper trade data
usgs_data = usgs_data.replace({'Democratic Republic of the Congo': 'DRC', 
                                     'Korea, Republic of': 'Republic of Korea', 
                                     'United States': 'USA'})

# Applying threshold from above to filter the USGS data for relevance
node_size = usgs_data[usgs_data[['mining_share', 'smelting_share', 'refining_share']].max(axis=1) >= usgs_threshold]

# Aggregating countries below the threshold to "Other"
node_size_below = usgs_data[usgs_data[['mining_share', 'smelting_share', 'refining_share']].max(axis=1) < usgs_threshold]
node_size_below = node_size_below.sum(axis=0)  # axis=0 sums along columns, axis=1 would sum along rows
node_size_below = node_size_below.to_frame().T
node_size_below.iloc[0,0] = 'a_Other' # named with a_ so that it is sorted after all other values but above the black boxes
# black boxes are sorted to the end because of the _ in their name + start with b for balance -> a_ is in above them but below all other values

# Adding the "Other" category to node_size
node_size = pd.concat([node_size,node_size_below])
node_size.reset_index(drop=True, inplace=True)







#%% Calculating the domestic flows from USGS data

# building dataframe in sankey format for  domestic flows
flows_domestic = node_size.copy()
flows_domestic['mining_to_smelting_domestic'] = flows_domestic[['mining_tonnes', 'smelting_tonnes']].min(axis=1)
flows_domestic['smelting_to_refining_domestic'] = flows_domestic[['smelting_tonnes', 'refining_tonnes']].min(axis=1)
flows_domestic = flows_domestic[['country', 'mining_to_smelting_domestic', 'smelting_to_refining_domestic']]

# Mined copper
flows_domestic_mined = flows_domestic[['country', 'mining_to_smelting_domestic']]
flows_domestic_mined['target_country'] = flows_domestic_mined['country']
flows_domestic_mined['source_stage'] = 'mining'
flows_domestic_mined['target_stage'] = 'smelting'
flows_domestic_mined.rename(columns={'country': 'source_country', 'mining_to_smelting_domestic': 'tonnes_copper'}, inplace=True)
flows_domestic_mined = flows_domestic_mined[['source_stage', 'source_country', 'target_stage', 'target_country', 'tonnes_copper']]

# Smelted copper
flows_domestic_smelted = flows_domestic[['country', 'smelting_to_refining_domestic']]
flows_domestic_smelted['target_country'] = flows_domestic_smelted['country']
flows_domestic_smelted['source_stage'] = 'smelting'
flows_domestic_smelted['target_stage'] = 'refining'
flows_domestic_smelted.rename(columns={'country': 'source_country', 'smelting_to_refining_domestic': 'tonnes_copper'}, inplace=True)
flows_domestic_smelted = flows_domestic_smelted[['source_stage', 'source_country', 'target_stage', 'target_country', 'tonnes_copper']]

# Mined and smelted copper
flows_domestic = pd.concat([flows_domestic_mined,flows_domestic_smelted])
flows_domestic = flows_domestic[(flows_domestic['tonnes_copper'] != 0)]

#%% Calculating the necessary foreign flows
flows_foreign = node_size.copy()
flows_foreign['mining_to_smelting_balance'] = flows_foreign['smelting_tonnes'] - flows_foreign['mining_tonnes']
flows_foreign['smelting_to_refining_balance'] = flows_foreign['refining_tonnes'] - flows_foreign['smelting_tonnes']
flows_foreign = flows_foreign[['country', 'mining_to_smelting_balance', 'smelting_to_refining_balance']]

# Mined copper
flows_foreign_mined = flows_foreign[['country', 'mining_to_smelting_balance']]
flows_foreign_mined.rename(columns={'mining_to_smelting_balance':'balance'}, inplace=True)
flows_foreign_mined['source_stage'] = 'mining'
flows_foreign_mined['target_stage'] = 'smelting'

# Smelted copper
flows_foreign_smelted = flows_foreign[['country', 'smelting_to_refining_balance']]
flows_foreign_smelted.rename(columns={'smelting_to_refining_balance':'balance'}, inplace=True)
flows_foreign_smelted['source_stage'] = 'smelting'
flows_foreign_smelted['target_stage'] = 'refining'

# Mined and smelted copper
flows_foreign = pd.concat([flows_foreign_mined,flows_foreign_smelted])
flows_foreign.reset_index(drop=True, inplace=True)


#%% Filtering trade dataset for chosen countries
# Filtering for countries being either exporter or importer (include both)
copper_trade_filtered = copper_trade.copy()
copper_trade_filtered = copper_trade_filtered.replace({'Democratic Republic of the Congo': 'DRC', 
                                                       'Russian Federation': 'Russia', 
                                                       'USA, Puerto Rico and US Virgin Islands': 'USA'})

# Getting list of all countries in the copper trade data
exporters = pd.DataFrame(copper_trade_filtered['exporter']).rename(columns={'exporter': 'country'})
importers = pd.DataFrame(copper_trade_filtered['importer']).rename(columns={'importer': 'country'})
countries = pd.merge(exporters, importers, on='country', how='left').drop_duplicates()
countries.reset_index(drop=True, inplace=True)

# Filtering the DataFrame
copper_trade_filtered = copper_trade_filtered[copper_trade_filtered['exporter'].isin(node_size['country']) & copper_trade_filtered['importer'].isin(node_size['country'])]
copper_trade_filtered = copper_trade_filtered.sort_values(by=['stage', 'exporter', 'importer'], ascending= True)
copper_trade_filtered.reset_index(drop=True, inplace=True)







#%% distribute the balances to the trade flows

# Initiating dataframe for Sankey with relevant columns from the trade data
copper_trade_cleaned = copper_trade_filtered[['stage', 'exporter', 'importer', 'tonnes_copper']]

# Adding stages describing the level of the sankey node
copper_trade_cleaned.loc[copper_trade_cleaned["stage"] == "mined", "exporter_stage"] = 'mining'
copper_trade_cleaned.loc[copper_trade_cleaned["stage"] == "smelted", "exporter_stage"] = 'smelting'

copper_trade_cleaned.loc[copper_trade_cleaned["stage"] == "mined", "importer_stage"] = 'smelting'
copper_trade_cleaned.loc[copper_trade_cleaned["stage"] == "smelted", "importer_stage"] = 'refining'

# Renaming columns for sankey 
copper_trade_cleaned.rename(columns={'exporter': 'source_country', 
                                     'importer': 'target_country', 
                                     'exporter_stage': 'source_stage',
                                     'importer_stage': 'target_stage'}, inplace=True)
copper_trade_cleaned = copper_trade_cleaned[['source_stage', 'source_country', 'target_stage', 'target_country', 'tonnes_copper']]

# Getting the share countries have of imports/exports of other countries
copper_trade_cleaned['share_exports_by_stage'] = copper_trade_cleaned['tonnes_copper'] / copper_trade_cleaned.groupby(['source_stage', 'source_country'])['tonnes_copper'].transform('sum')
copper_trade_cleaned['share_imports_by_stage'] = copper_trade_cleaned['tonnes_copper'] / copper_trade_cleaned.groupby(['target_stage', 'target_country'])['tonnes_copper'].transform('sum')

# Removing 0 values (nothing to allocate) and differentiating positive (more import necessary) and negative (more export necessary) flows to allocated
flows_foreign_pos = flows_foreign[flows_foreign['balance'] > 0]
flows_foreign_pos.reset_index(drop=True, inplace=True)

flows_foreign_neg = flows_foreign[flows_foreign['balance'] < 0]
flows_foreign_neg.reset_index(drop=True, inplace=True)

"""
4 cases: 
    1. import of mining necessary because not enough in smelting - positive value
    2. export of mining necessary because too much in smelting - negative value
    
    3. import of smelted necessary because not enough in refining - positive value
    4. export of smelted necessary because too much in refining - negative value
"""


#%% Merging dataframe to have the necessary allocation amounts in a column
copper_trade_allocated = pd.merge(copper_trade_cleaned, flows_foreign_pos,
                                  left_on=['target_stage', 'target_country'],
                                  right_on=['target_stage', 'country'], 
                                  how='left', suffixes=('', '_y'))

copper_trade_allocated = pd.merge(copper_trade_allocated, flows_foreign_neg,
                                  left_on=['source_stage', 'source_country'],
                                  right_on=['source_stage', 'country'], 
                                  how='left', suffixes=('', '_y'))


copper_trade_allocated = copper_trade_allocated[['source_stage', 'source_country', 'target_stage', 'target_country', 
                                                 'tonnes_copper', 'share_exports_by_stage', 'share_imports_by_stage', 
                                                 'balance', 'balance_y']]
copper_trade_allocated.rename(columns={'balance':'imports_to_allocate', 'balance_y':'exports_to_allocate'}, inplace=True)

# Filling NaNs (nothing to allocate there) with 0
copper_trade_allocated[['imports_to_allocate', 'exports_to_allocate']] = copper_trade_allocated[['imports_to_allocate', 'exports_to_allocate']].fillna(value=0)

#%% Allocating the values by multiplying with import and export shares
copper_trade_allocated['tonnes_copper_allocated_by_imports'] = copper_trade_allocated['imports_to_allocate'] * copper_trade_allocated['share_imports_by_stage']
copper_trade_allocated['tonnes_copper_allocated_by_exports'] = copper_trade_allocated['exports_to_allocate'] * -1 * copper_trade_allocated['share_exports_by_stage']
copper_trade_allocated[['tonnes_copper_allocated_by_imports', 'tonnes_copper_allocated_by_exports']] = copper_trade_allocated[['tonnes_copper_allocated_by_imports', 'tonnes_copper_allocated_by_exports']].fillna(value=0)
# nan in both -> nothing needs to be allocated

# Calculating what volume of flows that need to go to black box
copper_trade_allocated['to_black_box_source'] = copper_trade_allocated['tonnes_copper_allocated_by_exports'] - copper_trade_allocated['tonnes_copper_allocated_by_imports']
copper_trade_allocated['to_black_box_source'] = copper_trade_allocated['to_black_box_source'].apply(lambda x: max(0, x))

copper_trade_allocated['from_black_box_target'] = copper_trade_allocated['tonnes_copper_allocated_by_imports'] - copper_trade_allocated['tonnes_copper_allocated_by_exports']
copper_trade_allocated['from_black_box_target'] = copper_trade_allocated['from_black_box_target'].apply(lambda x: max(0, x))

# Calculating the volume of flows that has been successfully allocated with the trade data
copper_trade_allocated['tonnes_copper_allocated'] = copper_trade_allocated[['tonnes_copper_allocated_by_exports', 'tonnes_copper_allocated_by_imports']].min(axis=1)

#%% Setting up the dataframes for flows that do not need black boxes
copper_trade_no_black_boxes = copper_trade_allocated[['source_stage', 'source_country', 'target_stage', 'target_country', 
                                                 'tonnes_copper_allocated']]
copper_trade_no_black_boxes.rename(columns={'tonnes_copper_allocated':'tonnes_copper'}, inplace=True)

copper_trade_no_black_boxes = copper_trade_no_black_boxes[copper_trade_no_black_boxes['tonnes_copper'] != 0]
copper_trade_no_black_boxes.reset_index(inplace=True, drop=True)

#%% Setting up the dataframes for flows that need black boxes
copper_trade_black_boxes = copper_trade_allocated[['source_stage', 'source_country', 'target_stage', 'target_country', 'from_black_box_target', 'to_black_box_source']]
copper_trade_black_boxes = copper_trade_black_boxes[(copper_trade_black_boxes['from_black_box_target'] != 0) | (copper_trade_black_boxes['to_black_box_source'] != 0)]

# Renaming source and target columns to black boxes (4 cases)
copper_trade_black_boxes.loc[(copper_trade_black_boxes['to_black_box_source'] > 0) & (copper_trade_black_boxes['source_stage'] == 'mining'), 'target_country'] = 'balance_smelting'
copper_trade_black_boxes.loc[(copper_trade_black_boxes['from_black_box_target'] > 0) & (copper_trade_black_boxes['target_stage'] == 'smelting'), 'source_country'] = 'balance_mining'
copper_trade_black_boxes.loc[(copper_trade_black_boxes['to_black_box_source'] > 0) & (copper_trade_black_boxes['source_stage'] == 'smelting'), 'target_country'] = 'balance_refining'
copper_trade_black_boxes.loc[(copper_trade_black_boxes['from_black_box_target'] > 0) & (copper_trade_black_boxes['target_stage'] == 'refining'), 'source_country'] = 'balance_smelting'

# Transforming to dataframe in sankey format
copper_trade_black_boxes_from = copper_trade_black_boxes[['source_stage', 'source_country', 'target_stage', 'target_country', 'from_black_box_target']]
copper_trade_black_boxes_from.rename(columns={'from_black_box_target': 'tonnes_copper'}, inplace=True)
copper_trade_black_boxes_to = copper_trade_black_boxes[['source_stage', 'source_country', 'target_stage', 'target_country', 'to_black_box_source']]
copper_trade_black_boxes_to.rename(columns={'to_black_box_source':'tonnes_copper'}, inplace=True)
copper_trade_black_boxes = pd.concat([copper_trade_black_boxes_from, copper_trade_black_boxes_to])
copper_trade_black_boxes = copper_trade_black_boxes[(copper_trade_black_boxes['tonnes_copper'] != 0)]
copper_trade_black_boxes = copper_trade_black_boxes.sort_values(by=['source_stage', 'source_country', 'target_country']).reset_index(drop=True)
# Sorting does not seem to see balance_mining or balance_smelting as normal strings and thus sorts them to the end (as intended)

# Summing up values that are double because of renaming to black boxes ()
copper_trade_black_boxes = copper_trade_black_boxes.groupby(['source_stage', 'source_country', 'target_stage', 'target_country'], as_index=False)['tonnes_copper'].sum()


#%% # for differences of USGS stages that have to be allocated, but for which no flows are in the trade data 
    # meaning the specific stage, e.g. Mongolia mining and smelting are missing

# Getting all country/stage combinations in the countries considered after filtering the USGS data
countries_stages = node_size.copy()
countries_stages['mining_tonnes'] = 'mining'
countries_stages['smelting_tonnes'] = 'smelting'
countries_stages['refining_tonnes'] = 'refining'
countries_stages = pd.melt(countries_stages, id_vars='country')
countries_stages.rename(columns={'value':'stage'}, inplace = True)
countries_stages.drop(['variable'], axis=1, inplace=True)
countries_stages.reset_index(drop=True, inplace=True)

# Getting all country/stage combinations that are in the trade data for the allocation
countries_stages_allocated1 = copper_trade_allocated[['source_stage', 'source_country']].drop_duplicates()
countries_stages_allocated1.rename(columns={'source_stage':'stage', 'source_country':'country'}, inplace = True)
countries_stages_allocated2 = copper_trade_allocated[['target_stage', 'target_country']].drop_duplicates()
countries_stages_allocated2.rename(columns={'target_stage':'stage', 'target_country':'country'}, inplace = True)
countries_stages_allocated = pd.concat([countries_stages_allocated1, countries_stages_allocated2], ignore_index=True).drop_duplicates()

#%%

# Getting the difference to know what country / stage combinations were not available for allocation
df1_common = pd.merge(countries_stages, countries_stages_allocated, how='inner')
countries_stages_not_allocated = pd.concat([countries_stages, df1_common, df1_common]).drop_duplicates(keep=False)
countries_stages_not_allocated.reset_index(inplace=True)

#%%
# Creating dummy combinations for those country/stage combinations missing
# the stages must be created precisely for what is missing, otherwise double values are generated
new_rows = []

for index in countries_stages_not_allocated.index:
    
    # Mining stage missing --> flow from mining stage of missing country to smelting black box must be added
    if countries_stages_not_allocated.loc[index, 'stage'] == 'mining':
        new_rows.extend([['mining', countries_stages_not_allocated.loc[index, 'country'], 'smelting', 'balance_smelting']])
    
    # Smelting stage missing --> flow from mining stage black box to smelting stage (missing country) and to refining stage (black box) must be added
    elif countries_stages_not_allocated.loc[index, 'stage'] == 'smelting':
        new_rows.extend([
            ['mining', 'balance_mining', 'smelting', countries_stages_not_allocated.loc[index, 'country']],
            ['smelting', countries_stages_not_allocated.loc[index, 'country'], 'refining', 'balance_refining'],
        ])
    
    # Refining stage missing --> flow from smelting (black box) to refining stage of missing country must be added
    elif countries_stages_not_allocated.loc[index, 'stage'] == 'refining':
        new_rows.extend([['smelting', 'balance_smelting', 'refining', countries_stages_not_allocated.loc[index, 'country']]])

USGS_values_not_allocated = pd.DataFrame(new_rows, columns=['source_stage', 'source_country', 'target_stage', 'target_country'])

#%% # Allocating the remainder of flows calculated from USGS
USGS_values_not_allocated = pd.merge(USGS_values_not_allocated, flows_foreign_pos,
                                  left_on=['target_stage', 'target_country'],
                                  right_on=['target_stage', 'country'], 
                                  how='left', suffixes=('', '_y'))

USGS_values_not_allocated = pd.merge(USGS_values_not_allocated, flows_foreign_neg,
                                  left_on=['source_stage', 'source_country'],
                                  right_on=['source_stage', 'country'], 
                                  how='left', suffixes=('', '_y'))

# Cleaning the dataframe from those rows without any allocated copper flows
USGS_values_not_allocated.drop(['country', 'source_stage_y', 'country_y', 'target_stage_y'], axis=1, inplace=True)
USGS_values_not_allocated.rename(columns={'balance':'imports_to_allocate', 'balance_y':'exports_to_allocate'}, inplace=True)
USGS_values_not_allocated = USGS_values_not_allocated.dropna(subset=['imports_to_allocate', 'exports_to_allocate'], how='all')
USGS_values_not_allocated = USGS_values_not_allocated.drop_duplicates()
USGS_values_not_allocated = USGS_values_not_allocated.fillna(0)
USGS_values_not_allocated.reset_index(drop=True, inplace=True)

# Merging the two columns describing exports to allocated and imports to allocate as no further allocation is required
# Due to structure of dummy dataframe these already represent flows
USGS_values_not_allocated['exports_to_allocate'] = USGS_values_not_allocated['exports_to_allocate'] * -1
USGS_values_not_allocated['tonnes_copper'] = USGS_values_not_allocated[['exports_to_allocate', 'imports_to_allocate']].max(axis=1)
USGS_values_not_allocated.drop(['exports_to_allocate', 'imports_to_allocate'], axis=1, inplace=True)


#%% Building the final dataframe with all flows for the Sankey
copper_flows_sankey = pd.concat([flows_domestic, copper_trade_no_black_boxes, copper_trade_black_boxes, USGS_values_not_allocated])
copper_flows_sankey = copper_flows_sankey.sort_values(by=['source_stage', 'source_country', 'target_country']).reset_index(drop=True)

#%% Testing the results for mass balance
# The absolute value of the foreign flows and flows in the copper_flows_sankey are not the same by definition. 
# Flows_foreign contains imports/exports required for each country --> double-counting
# e.g. Australia needs to export mining & China needs to import mined material --> both in foreign_flows separately, although physically overlap
# after harmonisation with trade data only overlap remains --> copper_flows_sankey by definition less than flows_foreign
# Important is that values of each country node size (sum of flow values) are the same as in USGS

# Extracting values for all stages without black boxes
sum_source_stages = copper_flows_sankey.groupby(['source_stage', 'source_country'])['tonnes_copper'].sum().reset_index()
sum_source_stages = sum_source_stages[~sum_source_stages['source_country'].isin(['balance_mining', 'balance_smelting', 'balance_refining'])]

sum_mining = sum_source_stages[sum_source_stages['source_stage'] == 'mining']
sum_mining.rename(columns={'tonnes_copper': 'mining_tonnes', 'source_country': 'country'}, inplace = True)

sum_smelting = sum_source_stages[sum_source_stages['source_stage'] == 'smelting']
sum_smelting.rename(columns={'tonnes_copper': 'smelting_tonnes', 'source_country': 'country'}, inplace = True)

sum_target_stages = copper_flows_sankey.groupby(['target_stage', 'target_country'])['tonnes_copper'].sum().reset_index()
sum_target_stages = sum_target_stages[~sum_target_stages['target_country'].isin(['balance_mining', 'balance_smelting', 'balance_refining'])]

sum_refining = sum_target_stages[sum_target_stages['target_stage'] == 'refining']
sum_refining.rename(columns={'tonnes_copper': 'refining_tonnes', 'target_country': 'country'}, inplace = True)

# Building dataframe for all stages
check_df = pd.merge(pd.merge(sum_mining, sum_smelting, on='country', how='outer'), sum_refining, on='country', how='outer').sort_values(by='country')
check_df.drop(columns=['source_stage_x','source_stage_y','target_stage'], inplace=True)
check_df = check_df.reset_index(drop=True)
check_df.fillna(0, inplace=True)

merged_df = pd.merge(check_df, node_size, on='country', suffixes=('_df1', '_df2'))

# Check if values are the same for both DataFrames
are_values_equal = merged_df['mining_tonnes_df1'].equals(merged_df['mining_tonnes_df2'])

are_values_equal = all(merged_df[col1].equals(merged_df[col2]) for col1, col2 in [('mining_tonnes_df1', 'mining_tonnes_df2'), ('smelting_tonnes_df1', 'smelting_tonnes_df2'), ('refining_tonnes_df1', 'refining_tonnes_df2')])

if are_values_equal:
    print("The values for the final sankey dataframe are the same as in USGS. The allocation is complete.")
else:
    print("The values for the final sankey dataframe are not the same as in USGS. The allocation is incomplete.")


#%% Scaling to NL
if scale_to_NL == True: 
    copper_flows_sankey['tonnes_copper'] = copper_flows_sankey['tonnes_copper'] * NL_share

    refining_df = copper_flows_sankey[copper_flows_sankey['target_stage'] == 'refining'].drop_duplicates()
    refining_df = refining_df.groupby(['target_stage', 'target_country'])['tonnes_copper'].sum().reset_index()
    
    use_rows = []

    for index in refining_df.index:
    
        use_rows.extend([
            ['refining', refining_df.loc[index, 'target_country'], 'use', 'Energy', refining_df.loc[index, 'tonnes_copper'] * NL_energy_share],
            ['refining', refining_df.loc[index, 'target_country'], 'use', 'Other', refining_df.loc[index, 'tonnes_copper'] * (1 - NL_energy_share)],
        ])
    
    use_rows = pd.DataFrame(use_rows, columns=['source_stage', 'source_country', 'target_stage', 'target_country', 'tonnes_copper'])

    copper_flows_sankey = pd.concat([copper_flows_sankey, use_rows], ignore_index=True)




#%% ------------------------------------------------------------------ 
# ---------------------- LCA -----------------------------------------
# --------------------------------------------------------------------
# 
lca_data = pd.read_excel("data/compilation_ecoinvent.xlsx", sheet_name= "Impacts")
lca_data.drop(["Region", "climate change, specific for country", "water depletion, specific for country", "natural land transformation, specific for country"], axis=1, inplace=True)


#%%

# # Data import
# lca_ghg = pd.read_excel("compilation_ecoinvent.xlsx", sheet_name= "GHG - IA").fillna("RoW") 
# lca_ghg = lca_ghg.rename(columns = {"Average": "GHG_average (kg CO2-eq/kg Cu)", "Amount": "GHG (kg CO2-eq/kg Cu)"})
# lca_biodiversity = pd.read_excel("compilation_ecoinvent.xlsx", sheet_name= "Biodiversity - IA").fillna("RoW")
# lca_biodiversity = lca_biodiversity.rename(columns = {"Average": "Biodiversity_average (UBP/kg Cu)", "Amount": "Biodiversity (UBP/kg Cu)"})
# lca_landuse = pd.read_excel("compilation_ecoinvent.xlsx", sheet_name= "Land use - Input").fillna("RoW")
# lca_landuse = lca_landuse.rename(columns = {"Amount": "Land use_average (m2/kg Cu)"})
# lca_water = pd.read_excel("compilation_ecoinvent.xlsx", sheet_name= "Water - Input").fillna("RoW")
# lca_water = lca_water.rename(columns = {"Average": "Water_average (m3/kg Cu)", "Total": "Water (m3/kg Cu)"})
# country_regions = pd.read_excel("compilation_ecoinvent.xlsx", sheet_name= "Country classification", usecols = [0,2]).drop_duplicates().reset_index(drop=True)


# # %% Concat
# ghg_bio_country = pd.merge(lca_ghg[["Stage", "Geography", "GHG (kg CO2-eq/kg Cu)"]],lca_biodiversity[["Stage", "Geography", "Biodiversity (UBP/kg Cu)"]], on = ["Stage", "Geography"], how = "outer")
# lu_water_country = pd.merge(lca_landuse[["Stage", "Geography", "Land use_average (m2/kg Cu)"]],lca_water[["Stage", "Geography", "Water (m3/kg Cu)"]], on = ["Stage", "Geography"], how = "outer")

# impacts_country = pd.merge(ghg_bio_country, lu_water_country, on = ["Stage", "Geography"], how = "outer").drop_duplicates().reset_index(drop=True)

# ghg_bio_region = pd.merge(lca_ghg[["Stage", "Region", "GHG_average (kg CO2-eq/kg Cu)"]],lca_biodiversity[["Stage", "Region", "Biodiversity_average (UBP/kg Cu)"]], on = ["Stage", "Region"], how = "outer")
# lu_water_region = pd.merge(lca_landuse[["Stage", "Region", "Land use_average (m2/kg Cu)"]],lca_water[["Stage", "Region", "Water_average (m3/kg Cu)"]], on = ["Stage", "Region"], how = "outer")

# impacts_regions = pd.merge(ghg_bio_region, lu_water_region, on = ["Stage", "Region"], how = "outer").drop_duplicates().reset_index(drop=True)

# combinations = list(product(impacts_regions['Stage'].drop_duplicates(), country_regions['Region']))
# combinations = pd.DataFrame(combinations, columns = ["Stage", "Region"])

# impacts_regions2 = pd.merge(combinations, impacts_regions, on = ["Stage", "Region"], how = "outer").drop_duplicates().reset_index(drop=True)

# for index, row in impacts_regions2.iterrows():
#     # Check if all columns except 'Stage' and 'Region' are NaN
#     if row.drop(['Stage', 'Region']).isna().all():
#         # Select the 'RoW' row for the current stage
#         mask = (impacts_regions2['Stage'] == row['Stage']) & (impacts_regions2['Region'] == 'RoW')
#         fill_row = impacts_regions2[mask].iloc[0]
#         # Fill NaN values in the current row with the corresponding values from fill_row
#         impacts_regions2.loc[index] = row.fillna(fill_row)
# impacts_regions2 = impacts_regions2.fillna(0)


# # %% Calculate the impacts per kg of copper
# impact_sources = pd.merge(copper_flows_sankey, country_regions, left_on='source_country', right_on='Economy', how='left').fillna("RoW")
# impact_sources = impact_sources.rename(columns = {"Region": "source_region"}).drop(columns = ["Economy"])

# impact_flows_ = pd.merge(impact_sources, country_regions, left_on='target_country', right_on='Economy', how='left').fillna("RoW")
# impact_flows_ = impact_flows_.rename(columns = {"Region": "target_region"}).drop(columns = ["Economy"])

# # %% Calculate the impacts per country based on region

# impact_flows = pd.merge(impact_flows_, impacts_regions2, left_on=['source_stage', 'source_region'], right_on=['Stage', 'Region'], how='left').drop(columns = ["Stage", "Region"]).fillna(0)
# impact_flows["GHG (kg CO2-eq)"] = impact_flows["GHG_average (kg CO2-eq/kg Cu)"] * impact_flows["tonnes_copper"]*1000
# impact_flows["Biodiversity (UBP)"] = impact_flows["Biodiversity_average (UBP/kg Cu)"] * impact_flows["tonnes_copper"]*1000
# impact_flows["Land use (m2)"] = impact_flows["Land use_average (m2/kg Cu)"] * impact_flows["tonnes_copper"]*1000
# impact_flows["Water (m3)"] = impact_flows["Water_average (m3/kg Cu)"] * impact_flows["tonnes_copper"]*1000

# impact_flows_region = impact_flows[["source_stage", "source_country", "target_stage", "target_country", "tonnes_copper", "GHG (kg CO2-eq)", "Biodiversity (UBP)", "Land use (m2)", "Water (m3)"]]

# #%% Calculate the impacts per country based on country

# impact_flows2 = pd.merge(impact_flows_, impacts_country, left_on=['source_stage', 'source_country'], right_on=['Stage', 'Geography'], how='left').drop(columns = ["Stage", "Geography"]).fillna(0)
# impact_flows2["GHG (kg CO2-eq)"] = impact_flows2["GHG (kg CO2-eq/kg Cu)"] * impact_flows2["tonnes_copper"]*1000
# impact_flows2["Biodiversity (UBP)"] = impact_flows2["Biodiversity (UBP/kg Cu)"] * impact_flows2["tonnes_copper"]*1000 
# impact_flows2["Land use (m2)"] = impact_flows2["Land use_average (m2/kg Cu)"] * impact_flows2["tonnes_copper"]*1000
# impact_flows2["Water (m3)"] = impact_flows2["Water (m3/kg Cu)"] * impact_flows2["tonnes_copper"]*1000

# impact_flows_country = impact_flows2[["source_stage", "source_country", "target_stage", "target_country", "tonnes_copper", "GHG (kg CO2-eq)", "Biodiversity (UBP)", "Land use (m2)", "Water (m3)"]]

#%% Combine two impact datasets

# impacts_flows_complete = impact_flows_country.where(impact_flows_country != 0, impact_flows_region)


#%%


# Merging with copper flows
impact_flows = pd.merge(copper_flows_sankey, lca_data, left_on=['source_stage', 'source_country'], right_on=['Stage', 'Geography'], how='left').fillna("RoW")

# Transforming units to impact/tonne not per kg as in the LCA data
impact_flows['GHG_emissions'] = impact_flows['GHG_emissions'] * 1000
impact_flows['water_depletion'] = impact_flows['water_depletion'] * 1000
impact_flows['natural_land_transformation'] = impact_flows['natural_land_transformation'] * 1000


# Calculating absolute impacts per flow
impact_flows['GHG (tCO₂-eq.)'] = impact_flows['tonnes_copper'] * impact_flows['GHG_emissions'] / 1000 # conversion from kg
impact_flows['Natural land transformation (m2)'] = impact_flows['tonnes_copper'] * impact_flows['water_depletion']
impact_flows['Water depletion (m3)'] = impact_flows['tonnes_copper'] * impact_flows['natural_land_transformation']

impact_flows = impact_flows.drop(['Stage', 'Geography', 'GHG_emissions', 'water_depletion', 'natural_land_transformation'], axis=1)






#%% # theshold for the flows
# not the most elegant solution!
# flow threshold does not make sense as it allocated flows from countries that are significant to "Others" -> filter must be based on list of countries




filter_DF = usgs_data[usgs_data[['mining_share', 'smelting_share', 'refining_share']].max(axis=1) >= second_threshold]
filter_countries = filter_DF['country'].to_list()
filter_countries.append('balance_mining')
filter_countries.append('balance_smelting')
filter_countries.append('balance_refining')
filter_countries.append('Energy')
filter_countries.append('Other')

impact_flows_final = impact_flows.copy()
impact_flows_final['source_country'] = impact_flows_final['source_country'].apply(lambda x: x if x in filter_countries else 'a_Other')
impact_flows_final['target_country'] = impact_flows_final['target_country'].apply(lambda x: x if x in filter_countries else 'a_Other')

impact_flows_final = impact_flows_final.groupby(['source_stage', 'source_country', 'target_stage', 'target_country']).agg({
    'tonnes_copper': 'sum',
    'GHG (tCO₂-eq.)': 'sum',
    'Natural land transformation (m2)': 'sum',
    'Water depletion (m3)': 'sum'
}).reset_index()

# Sorting by stage and country
sort1 = impact_flows_final[(impact_flows_final['source_stage'] == 'mining') | (impact_flows_final['source_stage'] == 'smelting')]
sort1 = sort1.sort_values(by=['source_stage', 'source_country'])

sort2 = impact_flows_final[(impact_flows_final['source_stage'] == 'refining')]
sort2 = sort2.sort_values(by=['source_country'])

impact_flows_final = pd.concat([sort1, sort2])
impact_flows_final.reset_index(inplace=True, drop=True)


#%% Deciding which impact to show and changing the title


if display == 'copper': 
    sankey_flows = impact_flows_final[['source_stage', 'source_country', 'target_stage', 'target_country', 'tonnes_copper']]
    title_text_NL = "Dutch copper supply chain in tonnes copper content, " + str(year)
    title_text_world = "World copper supply chain in tonnes copper content, " + str(year)
    sankey_flows.rename(columns={'tonnes_copper':'value'}, inplace=True)
    
elif display == 'ghg': 
    sankey_flows = impact_flows_final[['source_stage', 'source_country', 'target_stage', 'target_country', 'GHG (tCO₂-eq.)']]
    title_text_NL = "Dutch copper supply chain - Greenhouse gas emissions in tCO₂-eq., " + str(year)
    title_text_world = "Global copper supply chain - Greenhouse gas emissions in tCO₂-eq., " + str(year)
    sankey_flows.rename(columns={'GHG (tCO₂-eq.)':'value'}, inplace=True)
    
elif display == 'land_use':
    sankey_flows = impact_flows_final[['source_stage', 'source_country', 'target_stage', 'target_country', 'Natural land transformation (m2)']]
    title_text_NL = "Dutch copper supply chain - Natural land transformation in m², " + str(year)
    title_text_world = "Global copper supply chain - Natural land transformation in m², " + str(year)
    sankey_flows.rename(columns={'Natural land transformation (m2)':'value'}, inplace=True)
    
elif display == 'water':    
    sankey_flows = impact_flows_final[['source_stage', 'source_country', 'target_stage', 'target_country', 'Water depletion (m3)']]  
    title_text_NL = "Dutch copper supply chain - Water depletion in m³, " + str(year)
    title_text_world = "Global copper supply chain - Water depletion in m³, " + str(year)	 
    sankey_flows.rename(columns={'Water depletion (m3)':'value'}, inplace=True)
    
else:
    print('The choice of what to display in the Sankey is invalid')



#%% ---------------------- Building dataframe for sankey ------------------------------





#%% adding the nodes

# Mining stage
mining_codes = sankey_flows[['source_stage', 'source_country']].drop_duplicates()
mining_codes = mining_codes[mining_codes['source_stage'] == 'mining']
mining_codes.rename(columns={'source_stage': 'stage', 'source_country': 'country'}, inplace = True)
mining_codes.reset_index(drop=True, inplace=True)

# Smelting stage
######### nto necessary because of the two balance things
smelting_codes_source = sankey_flows[['source_stage', 'source_country']].drop_duplicates()
smelting_codes_source = smelting_codes_source[smelting_codes_source['source_stage'] == 'smelting']
smelting_codes_source.rename(columns={'source_stage': 'stage', 'source_country': 'country'}, inplace = True)

smelting_codes_target = sankey_flows[['target_stage', 'target_country']].drop_duplicates()
smelting_codes_target = smelting_codes_target[smelting_codes_target['target_stage'] == 'smelting']
smelting_codes_target.rename(columns={'target_stage': 'stage', 'target_country': 'country'}, inplace = True)

smelting_codes = pd.concat([smelting_codes_source, smelting_codes_target]).drop_duplicates()
smelting_codes = smelting_codes.sort_values(by='country', ascending= True)
smelting_codes.reset_index(drop=True, inplace=True)

# Refining stage
refining_codes_source = sankey_flows[["source_stage", "source_country"]].drop_duplicates()
refining_codes_source = refining_codes_source[refining_codes_source["source_stage"] == 'refining']
refining_codes_source.rename(
    columns={"source_stage": "stage", "source_country": "country"}, inplace=True
)

refining_codes_target = sankey_flows[["target_stage", "target_country"]].drop_duplicates()
refining_codes_target = refining_codes_target[refining_codes_target["target_stage"] == 'refining']
refining_codes_target.rename(
    columns={"target_stage": "stage", "target_country": "country"}, inplace=True
)

refining_codes = pd.concat([refining_codes_source, refining_codes_target]).drop_duplicates()
refining_codes = refining_codes.sort_values(by="country", ascending=True)
refining_codes.reset_index(drop=True, inplace=True)


if scale_to_NL == True:
    # Use stage
    use_codes = sankey_flows[['target_stage', 'target_country']].drop_duplicates()
    use_codes = use_codes[use_codes['target_stage'] == 'use']
    use_codes.rename(columns={'target_stage': 'stage', 'target_country': 'country'}, inplace = True)
    use_codes = use_codes.sort_values(by='country', ascending= True)
    use_codes.reset_index(drop=True, inplace=True)

# Building total dataframe and resetting index to get a column with a unique number per node, sorted by stage and then country
if scale_to_NL == True:
    sankey_nodes = pd.concat([mining_codes, smelting_codes, refining_codes, use_codes])
else:
    sankey_nodes = pd.concat([mining_codes, smelting_codes, refining_codes])
sankey_nodes = sankey_nodes.reset_index(drop=True)
sankey_nodes = sankey_nodes.reset_index(drop=False)
sankey_nodes.rename(columns={'index': 'node_number'}, inplace = True)


#%% Adding the node numbes to the trade flows as input for the sankey

# Adding exporter nodes
sankey_flows_final = pd.merge(sankey_flows, sankey_nodes, 
                                     left_on=['source_stage', 'source_country'], 
                                     right_on=['stage', 'country'], 
                                     how='left')


sankey_flows_final.drop(['stage', 'country'], axis = 1, inplace = True)

# Adding importer nodes
sankey_flows_final = pd.merge(sankey_flows_final, sankey_nodes, 
                                     left_on=['target_stage', 'target_country'], 
                                     right_on=['stage', 'country'], 
                                     how='left')

sankey_flows_final.drop(['stage', 'country'], axis = 1, inplace = True)

# Renaming columns
sankey_flows_final.rename(columns={'node_number_x': 'source', 
                                'node_number_y': 'target'}, 
                                 inplace = True)




#%% Data export
# sankey_flows_final.to_excel("sankey_data.xlsx")


#%% ------------------------------------------------------------------ 
# ---------------------- SANKEY --------------------------------------
# --------------------------------------------------------------------

#%% ----------------- X and Y positions ------------------------

# Getting the total size of each stage as a reference for the diagram (max stage size <-> 1)
export_sums = sankey_flows_final.groupby(['source_stage', 'source_country'])['value'].sum().reset_index()
export_sums.rename(columns={'source_stage':'stage','source_country':'country'}, inplace=True)
import_sums = sankey_flows_final.groupby(['target_stage', 'target_country'])['value'].sum().reset_index()
import_sums.rename(columns={'target_stage':'stage','target_country':'country'}, inplace=True)

#%% getting node sizes from export/import values

# mining
sizes_mining = pd.merge(sankey_nodes[sankey_nodes['stage'] == 'mining'], export_sums[export_sums['stage'] == 'mining'], 
                     on='country', how='outer', suffixes=('', '_y'))
sizes_mining = sizes_mining.drop(['node_number', 'stage_y'], axis = 1,)

# smelting
sizes_smelting_exports = pd.merge(sankey_nodes[sankey_nodes['stage'] == 'smelting'], export_sums[export_sums['stage'] == 'smelting'], 
                     on='country', how='outer', suffixes=('', '_y'))
sizes_smelting_exports = sizes_smelting_exports.drop(['node_number', 'stage_y'], axis = 1,)

sizes_smelting_imports = pd.merge(sankey_nodes[sankey_nodes['stage'] == 'smelting'], import_sums[import_sums['stage'] == 'smelting'], 
                     on='country', how='outer', suffixes=('', '_y'))
sizes_smelting_imports = sizes_smelting_imports.drop(['node_number', 'stage_y'], axis = 1,)

# when calculating the impacts, the inflows and outflows are not always the same --> need to take the maximum of both to calculate the node size for the positions
sizes_smelting = pd.merge(sizes_smelting_exports, sizes_smelting_imports, on=['stage', 'country']).assign(value=lambda x: x[['value_x', 'value_y']].max(axis=1))
sizes_smelting = sizes_smelting[['stage', 'country', 'value']]

if scale_to_NL == True:

    sizes_refining_exports = pd.merge(sankey_nodes[sankey_nodes['stage'] == 'refining'], export_sums[export_sums['stage'] == 'refining'], 
                          on='country', how='outer', suffixes=('', '_y'))
    sizes_refining_exports = sizes_refining_exports.drop(['node_number', 'stage_y'], axis = 1,)

    sizes_refining_imports = pd.merge(sankey_nodes[sankey_nodes['stage'] == 'refining'], import_sums[import_sums['stage'] == 'refining'], 
                          on='country', how='outer', suffixes=('', '_y'))
    sizes_refining_imports = sizes_refining_imports.drop(['node_number', 'stage_y'], axis = 1,)

    # when calculating the impacts, the inflows and outflows are not always the same --> need to take the maximum of both to calculate the node size for the positions
    sizes_refining = pd.merge(sizes_refining_exports, sizes_refining_imports, on=['stage', 'country']).assign(value=lambda x: x[['value_x', 'value_y']].max(axis=1))
    sizes_refining = sizes_refining[['stage', 'country', 'value']]
    
    sizes_use = pd.merge(sankey_nodes[sankey_nodes['stage'] == 'use'], import_sums[import_sums['stage'] == 'use'], 
                          on='country', how='outer', suffixes=('', '_y'))
    sizes_use = sizes_use.drop(['node_number', 'stage_y'], axis = 1,)
else:    
    # refining only has exports if allocating to NL/use
    sizes_refining = pd.merge(sankey_nodes[sankey_nodes['stage'] == 'refining'], import_sums[import_sums['stage'] == 'refining'], 
                          on='country', how='outer', suffixes=('', '_y'))
    sizes_refining = sizes_refining.drop(['node_number', 'stage_y'], axis = 1,)


#%%
# scale factor to normalise node size to scale 0 to 1
if scale_to_NL == True:
    total_scale = 1 / max(sizes_mining['value'].sum(), sizes_smelting['value'].sum(), sizes_refining['value'].sum(), sizes_use['value'].sum())
else: 
    total_scale = 1 / max(sizes_mining['value'].sum(), sizes_smelting['value'].sum(), sizes_refining['value'].sum())

# need to be done per level as each has "1" place on the sankey (y-size)
# Mining nodes
sizes_mining['x_pos'] = 0.005
sizes_mining['y_size'] = sizes_mining['value'] * total_scale
sizes_mining.loc[0, 'y_pos'] = sizes_mining.loc[0, 'y_size']/2
for i in range(1, len(sizes_mining)):
    sizes_mining.loc[i, 'y_pos'] = sizes_mining.loc[i, 'y_size']/2 + sizes_mining.loc[i-1, 'y_size']/2 + sizes_mining.loc[i-1, 'y_pos']

# Smelting nodes
if scale_to_NL == True:
    sizes_smelting['x_pos'] = 0.335
else:
    sizes_smelting['x_pos'] = 0.5
sizes_smelting['y_size'] = sizes_smelting['value'] * total_scale
sizes_smelting.loc[0, 'y_pos'] = sizes_smelting.loc[0, 'y_size']/2

for i in range(1, len(sizes_smelting)):
    sizes_smelting.loc[i, 'y_pos'] = sizes_smelting.loc[i, 'y_size']/2 + sizes_smelting.loc[i-1, 'y_size']/2 + sizes_smelting.loc[i-1, 'y_pos']

# Refining nodes
if scale_to_NL == True:
    sizes_refining['x_pos'] = 0.665
else:
    sizes_refining['x_pos'] = 0.995
sizes_refining['y_size'] = sizes_refining['value'] * total_scale
sizes_refining.loc[0, 'y_pos'] = sizes_refining.loc[0, 'y_size']/2

for i in range(1, len(sizes_refining)):
    sizes_refining.loc[i, 'y_pos'] = sizes_refining.loc[i, 'y_size']/2 + sizes_refining.loc[i-1, 'y_size']/2 + sizes_refining.loc[i-1, 'y_pos']
#%%
# sizes use
if scale_to_NL == True:
    sizes_use['x_pos'] = 0.995
    sizes_use['y_size'] = sizes_use['value'] * total_scale
    sizes_use.loc[0, 'y_pos'] = sizes_use.loc[0, 'y_size']/2

    for i in range(1, len(sizes_use)):
        sizes_use.loc[i, 'y_pos'] = sizes_use.loc[i, 'y_size']/2 + sizes_use.loc[i-1, 'y_size']/2 + sizes_use.loc[i-1, 'y_pos']


#%%
# assembling all sizes and positions
if scale_to_NL == True:
    sizes = pd.concat([sizes_mining, sizes_smelting, sizes_refining, sizes_use]).reset_index(drop = True)
else: 
    sizes = pd.concat([sizes_mining, sizes_smelting, sizes_refining]).reset_index(drop = True)
sizes.reset_index(drop =True, inplace=True)

# Getting the share of the country for the specific stage
sizes['share_by_stage'] = sizes['value'] / sizes.groupby('stage')['value'].transform('sum')

# extracing positional values for sankey
y_position = sizes['y_pos'].tolist()
x_position = sizes['x_pos'].tolist()




#%% ---------------------- Node colours -----------------------------
# Importing node colours
if highlight_LMIC == True: 
    country_colours = pd.read_excel("data/colours.xlsx", sheet_name='grouped') # grouped by industrial, LMIC and black boxes
else:
    country_colours = pd.read_excel("data/colours.xlsx", sheet_name='unique') # unique for each country

sizes = pd.merge(left=sizes, right=country_colours, on='country', how='left')

# Extracting the list of node colours for the Sankey
colours_nodes = sizes['colour'].tolist()



#%% ---------------------- Flow colours -----------------------------

# Assigning flow colours so that the colour is the same as for the exporter node
flow_colours = pd.merge(sankey_flows_final[['source_country']], country_colours, 
                        left_on='source_country', right_on='country', how='left')

# Extracting the list of flow colours for the Sankey
colours_links = flow_colours['colour'].tolist() 

# Changing opacity of flow colours
opacity_links = '0.5)'
for i in range(len(colours_links)):
    colours_links[i] = colours_links[i].replace("1)", opacity_links)





#%% ---------------------- Labels -----------------------------

# Country names
names = sankey_nodes['country'].tolist()

# Changing the names for the black boxes and "Other" category for the visualization
for i in range(len(names)):
    if names[i] == 'balance_mining':
        names[i] = 'Black Box'
    elif names[i] == 'balance_smelting':
        names[i] = 'Black Box'
    elif names[i] == 'balance_refining':
        names[i] = 'Black Box'
    elif names[i] == 'a_Other':
        names[i] = 'Other'
    elif names[i] == 'Energy':
        names[i] = 'Renewables' 
        

if sankey_labels_absolute == True: 
    numbers = sizes['value'].tolist()
    formatted_numbers = ["{:,.0f}".format(num) for num in numbers]
    labels = [str(x) + ' ' + str(y) for x, y in zip(names, formatted_numbers)]
else: 
    numbers = sizes['share_by_stage'].tolist()
    formatted_percentages = ["{:.0%}".format(num) for num in numbers]
    labels = [str(x) + ' ' + str(y) for x, y in zip(names, formatted_percentages)]    

#%% ---------------------- Values ----------------------

# Extract source, target, and value columns
source = sankey_flows_final['source'].tolist()
target = sankey_flows_final['target'].tolist()
value = sankey_flows_final['value'].tolist()


# Define link and node dictionaries for the Sankey diagram
link = dict(
    source=source, 
    target=target, 
    value=value, 
    color=colours_links
    )

node = {"label": labels, 
        'pad': 0, 
        'thickness': 30,
        "x": x_position,  
        "y": y_position, 
        "color": colours_nodes
        }


#%% ---------------------- Plotting ---------------------------

width = (36.1 / 2.54) * 96
height = (20.1 / 2.54) * 96

fig = go.Figure(go.Sankey(
    arrangement='perpendicular',
    link=link, 
    node=node
    )) 

if scale_to_NL == True: 
    title_text = title_text_NL
else: 
    title_text = title_text_world

fig.update_layout(
    hovermode='x',
    font_size=20, 
    margin=dict(l=20, r=20, b=10, t=65),
    title_text=title_text,
    title_x=0.015,
    height = height,    
    width = width
)



# Adding headers for mining, smelting and refining
if scale_to_NL == True: 
    annotations = ["Mining", "Smelting", "Refining", "Use"]
    annotation_positions = [-0.01, 0.31, 0.69, 1.005]
else: 
    annotations = ["Mining", "Smelting", "Refining"]
    annotation_positions = [-0.01, 0.5, 1.01]

for i in range(len(annotations)): 
    fig.add_annotation(x=annotation_positions[i], 
                   y=1.04, 
                   text=annotations[i],
                   showarrow=False,
                   font=dict(size=20),
                   )

fig.show(renderer="browser")
fig.write_image("sankey.svg", engine="kaleido")
fig.write_html("sankey.html")




