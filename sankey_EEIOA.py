# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 15:29:23 2024

@author: aaron
"""

import pandas as pd
import plotly.graph_objects as go

# %%

sankey_labels_absolute = (
    True  # if True, absolute numbers are shown in the sankey, otherwise percent
)
highlight_LMIC = True

# Choice of threshold
flow_threshold = 2000

stage_1 = "mining"
stage_2 = "smelting"
stage_3 = "refining"
stage_4 = "use"

title_text = "Impacts of the Dutch copper supply chain - Greenhouse gas emissions in tCO₂-eq., 2019"
# "Impacts of the Dutch copper supply chain - Biodiversity loss in eco-points (UBP), "
# "Impacts of the Dutch copper supply chain - Land use in m², "
# "Impacts of the Dutch copper supply chain - Water use in m³, "

# elif display == 'ghg':
#     sankey_flows = impacts_flows_complete[['source_stage', 'source_country', 'target_stage', 'target_country', 'GHG (tCO₂-eq.)']]
#     title_text_NL = "Impacts of the Dutch copper supply chain - Greenhouse gas emissions in tCO₂-eq., " + str(year)
#     title_text_world = "Impacts of the global copper supply chain - Greenhouse gas emissions in tCO₂-eq., " + str(year)
#     sankey_flows.rename(columns={'GHG (tCO₂-eq.)':'value'}, inplace=True)

# elif display == 'biodiversity':
#     sankey_flows = impacts_flows_complete[['source_stage', 'source_country', 'target_stage', 'target_country', 'Biodiversity (UBP)']]
#     title_text_NL = "Impacts of the Dutch copper supply chain - Biodiversity loss in eco-points (UBP), " + str(year)
#     title_text_world = "Impacts of the global copper supply chain - Biodiversity loss in eco-points (UBP), " + str(year)
#     sankey_flows.rename(columns={'Biodiversity (UBP)':'value'}, inplace=True)

# elif display == 'land_use':
#     sankey_flows = impacts_flows_complete[['source_stage', 'source_country', 'target_stage', 'target_country', 'Land use (m2)']]
#     title_text_NL = "Impacts of the Dutch copper supply chain - Land use in m², " + str(year)
#     title_text_world = "Impacts of the global copper supply chain - Land use in m², " + str(year)
#     sankey_flows.rename(columns={'Land use (m2)':'value'}, inplace=True)

# elif display == 'water':
#     sankey_flows = impacts_flows_complete[['source_stage', 'source_country', 'target_stage', 'target_country', 'Water (m3)']]
#     title_text_NL = "Impacts of the Dutch copper supply chain - Water use in m³, " + str(year)
#     title_text_world = "Impacts of the global copper supply chain - Water use in m³, " + str(year)
#     sankey_flows.rename(columns={'Water (m3)':'value'}, inplace=True)


# %%

sankey_flows = pd.read_excel("test_data.xlsx")
# sankey_flows = pd.read_csv(".csv")


#%% Applying the threshold
sankey_flows = sankey_flows[sankey_flows['value'] >= flow_threshold]
sankey_flows.reset_index(drop=True, inplace=True)

# %% adding the nodes

# Mining stage
mining_codes = sankey_flows[["source_stage", "source_country"]].drop_duplicates()
mining_codes = mining_codes[mining_codes["source_stage"] == stage_1]
mining_codes.rename(columns={"source_stage": "stage", "source_country": "country"}, inplace=True)
mining_codes.reset_index(drop=True, inplace=True)

# Smelting stage
######### not necessary because of the two balance things
smelting_codes_source = sankey_flows[["source_stage", "source_country"]].drop_duplicates()
smelting_codes_source = smelting_codes_source[smelting_codes_source["source_stage"] == stage_2]
smelting_codes_source.rename(
    columns={"source_stage": "stage", "source_country": "country"}, inplace=True
)

smelting_codes_target = sankey_flows[["target_stage", "target_country"]].drop_duplicates()
smelting_codes_target = smelting_codes_target[smelting_codes_target["target_stage"] == stage_2]
smelting_codes_target.rename(
    columns={"target_stage": "stage", "target_country": "country"}, inplace=True
)

smelting_codes = pd.concat([smelting_codes_source, smelting_codes_target]).drop_duplicates()
smelting_codes = smelting_codes.sort_values(by="country", ascending=True)
smelting_codes.reset_index(drop=True, inplace=True)

# Refining stage
refining_codes_source = sankey_flows[["source_stage", "source_country"]].drop_duplicates()
refining_codes_source = refining_codes_source[refining_codes_source["source_stage"] == stage_3]
refining_codes_source.rename(
    columns={"source_stage": "stage", "source_country": "country"}, inplace=True
)

refining_codes_target = sankey_flows[["target_stage", "target_country"]].drop_duplicates()
refining_codes_target = refining_codes_target[refining_codes_target["target_stage"] == stage_3]
refining_codes_target.rename(
    columns={"target_stage": "stage", "target_country": "country"}, inplace=True
)

refining_codes = pd.concat([refining_codes_source, refining_codes_target]).drop_duplicates()
refining_codes = refining_codes.sort_values(by="country", ascending=True)
refining_codes.reset_index(drop=True, inplace=True)

# Use stage
use_codes = sankey_flows[["target_stage", "target_country"]].drop_duplicates()
use_codes = use_codes[use_codes["target_stage"] == stage_4]
use_codes.rename(columns={"target_stage": "stage", "target_country": "country"}, inplace=True)
use_codes = use_codes.sort_values(by="country", ascending=True)
use_codes.reset_index(drop=True, inplace=True)

# Building total dataframe and resetting index to get a column with a unique number per node, sorted by stage and then country
sankey_nodes = pd.concat([mining_codes, smelting_codes, refining_codes, use_codes])
sankey_nodes = sankey_nodes.reset_index(drop=True)
sankey_nodes = sankey_nodes.reset_index(drop=False)
sankey_nodes.rename(columns={"index": "node_number"}, inplace=True)


# %% Adding the node numbes to the trade flows as input for the sankey

# Adding exporter nodes
sankey_flows_final = pd.merge(
    sankey_flows,
    sankey_nodes,
    left_on=["source_stage", "source_country"],
    right_on=["stage", "country"],
    how="left",
)


sankey_flows_final.drop(["stage", "country"], axis=1, inplace=True)

# Adding importer nodes
sankey_flows_final = pd.merge(
    sankey_flows_final,
    sankey_nodes,
    left_on=["target_stage", "target_country"],
    right_on=["stage", "country"],
    how="left",
)

sankey_flows_final.drop(["stage", "country"], axis=1, inplace=True)

# Renaming columns
sankey_flows_final.rename(
    columns={"node_number_x": "source", "node_number_y": "target"}, inplace=True
)


# %% ------------------------------------------------------------------
# ---------------------- SANKEY --------------------------------------
# --------------------------------------------------------------------

# %% ----------------- X and Y positions ------------------------

# Getting the total size of each stage as a reference for the diagram (max stage size <-> 1)
export_sums = (
    sankey_flows_final.groupby(["source_stage", "source_country"])["value"].sum().reset_index()
)
export_sums.rename(columns={"source_stage": "stage", "source_country": "country"}, inplace=True)

import_sums = (
    sankey_flows_final.groupby(["target_stage", "target_country"])["value"].sum().reset_index()
)
import_sums.rename(columns={"target_stage": "stage", "target_country": "country"}, inplace=True)

# %% getting node sizes from export/import values

# mining
sizes_mining = pd.merge(
    sankey_nodes[sankey_nodes["stage"] == stage_1],
    export_sums[export_sums["stage"] == stage_1],
    on="country",
    how="outer",
    suffixes=("", "_y"),
)
sizes_mining = sizes_mining.drop(
    ["node_number", "stage_y"],
    axis=1,
)

# smelting
sizes_smelting_exports = pd.merge(
    sankey_nodes[sankey_nodes["stage"] == stage_2],
    export_sums[export_sums["stage"] == stage_2],
    on="country",
    how="outer",
    suffixes=("", "_y"),
)
sizes_smelting_exports = sizes_smelting_exports.drop(
    ["node_number", "stage_y"],
    axis=1,
)

sizes_smelting_imports = pd.merge(
    sankey_nodes[sankey_nodes["stage"] == stage_2],
    import_sums[import_sums["stage"] == stage_2],
    on="country",
    how="outer",
    suffixes=("", "_y"),
)
sizes_smelting_imports = sizes_smelting_imports.drop(
    ["node_number", "stage_y"],
    axis=1,
)

# when calculating the impacts, the inflows and outflows are not always the same --> need to take the maximum of both to calculate the node size for the positions
sizes_smelting = pd.merge(
    sizes_smelting_exports, sizes_smelting_imports, on=["stage", "country"]
).assign(value=lambda x: x[["value_x", "value_y"]].max(axis=1))
sizes_smelting = sizes_smelting[["stage", "country", "value"]]


sizes_refining_exports = pd.merge(
    sankey_nodes[sankey_nodes["stage"] == stage_3],
    export_sums[export_sums["stage"] == stage_3],
    on="country",
    how="outer",
    suffixes=("", "_y"),
)
sizes_refining_exports = sizes_refining_exports.drop(
    ["node_number", "stage_y"],
    axis=1,
)

sizes_refining_imports = pd.merge(
    sankey_nodes[sankey_nodes["stage"] == stage_3],
    import_sums[import_sums["stage"] == stage_3],
    on="country",
    how="outer",
    suffixes=("", "_y"),
)
sizes_refining_imports = sizes_refining_imports.drop(
    ["node_number", "stage_y"],
    axis=1,
)

# when calculating the impacts, the inflows and outflows are not always the same --> need to take the maximum of both to calculate the node size for the positions
sizes_refining = pd.merge(
    sizes_refining_exports, sizes_refining_imports, on=["stage", "country"]
).assign(value=lambda x: x[["value_x", "value_y"]].max(axis=1))
sizes_refining = sizes_refining[["stage", "country", "value"]]

# %%
sizes_use = pd.merge(
    sankey_nodes[sankey_nodes["stage"] == stage_4],
    import_sums[import_sums["stage"] == stage_4],
    on="country",
    how="outer",
    suffixes=("", "_y"),
)
sizes_use = sizes_use.drop(
    ["node_number", "stage_y"],
    axis=1,
)


# %%
# scale factor to normalise node size to scale 0 to 1

total_scale = 1 / max(
    sizes_mining["value"].sum(),
    sizes_smelting["value"].sum(),
    sizes_refining["value"].sum(),
    sizes_use["value"].sum(),
)

# need to be done per level as each has "1" place on the sankey (y-size)
# Mining nodes
sizes_mining["x_pos"] = 0.005
sizes_mining["y_size"] = sizes_mining["value"] * total_scale
sizes_mining.loc[0, "y_pos"] = sizes_mining.loc[0, "y_size"] / 2
for i in range(1, len(sizes_mining)):
    sizes_mining.loc[i, "y_pos"] = (
        sizes_mining.loc[i, "y_size"] / 2
        + sizes_mining.loc[i - 1, "y_size"] / 2
        + sizes_mining.loc[i - 1, "y_pos"]
    )

# Smelting nodes
sizes_smelting["x_pos"] = 0.335
sizes_smelting["y_size"] = sizes_smelting["value"] * total_scale
sizes_smelting.loc[0, "y_pos"] = sizes_smelting.loc[0, "y_size"] / 2

for i in range(1, len(sizes_smelting)):
    sizes_smelting.loc[i, "y_pos"] = (
        sizes_smelting.loc[i, "y_size"] / 2
        + sizes_smelting.loc[i - 1, "y_size"] / 2
        + sizes_smelting.loc[i - 1, "y_pos"]
    )

# Refining nodes
sizes_refining["x_pos"] = 0.665
sizes_refining["y_size"] = sizes_refining["value"] * total_scale
sizes_refining.loc[0, "y_pos"] = sizes_refining.loc[0, "y_size"] / 2

for i in range(1, len(sizes_refining)):
    sizes_refining.loc[i, "y_pos"] = (
        sizes_refining.loc[i, "y_size"] / 2
        + sizes_refining.loc[i - 1, "y_size"] / 2
        + sizes_refining.loc[i - 1, "y_pos"]
    )
# %%
# sizes use
sizes_use["x_pos"] = 0.995
sizes_use["y_size"] = sizes_use["value"] * total_scale
sizes_use.loc[0, "y_pos"] = sizes_use.loc[0, "y_size"] / 2

for i in range(1, len(sizes_use)):
    sizes_use.loc[i, "y_pos"] = (
        sizes_use.loc[i, "y_size"] / 2
        + sizes_use.loc[i - 1, "y_size"] / 2
        + sizes_use.loc[i - 1, "y_pos"]
    )


# %%
# assembling all sizes and positions
sizes = pd.concat([sizes_mining, sizes_smelting, sizes_refining, sizes_use]).reset_index(drop=True)
sizes.reset_index(drop=True, inplace=True)

# Getting the share of the country for the specific stage
sizes["share_by_stage"] = sizes["value"] / sizes.groupby("stage")["value"].transform("sum")

# extracing positional values for sankey
y_position = sizes["y_pos"].tolist()
x_position = sizes["x_pos"].tolist()


# %% ---------------------- Node colours -----------------------------
# Importing node colours
if highlight_LMIC == True:
    country_colours = pd.read_excel(
        "colours.xlsx", sheet_name="grouped"
    )  # grouped by industrial, LMIC and black boxes
else:
    country_colours = pd.read_excel("colours.xlsx", sheet_name="unique")  # unique for each country

sizes = pd.merge(left=sizes, right=country_colours, on="country", how="left")

# Extracting the list of node colours for the Sankey
colours_nodes = sizes["colour"].tolist()


# %% ---------------------- Flow colours -----------------------------

# Assigning flow colours so that the colour is the same as for the exporter node
flow_colours = pd.merge(
    sankey_flows_final[["source_country"]],
    country_colours,
    left_on="source_country",
    right_on="country",
    how="left",
)

# Extracting the list of flow colours for the Sankey
colours_links = flow_colours["colour"].tolist()

# Changing opacity of flow colours
opacity_links = "0.5)"
for i in range(len(colours_links)):
    colours_links[i] = colours_links[i].replace("1)", opacity_links)


# %% ---------------------- Labels -----------------------------

# Country names
names = sankey_nodes["country"].tolist()

# Changing the names for the black boxes for the visualization
for i in range(len(names)):
    if names[i] == f"balance_{stage_1}":
        names[i] = "Black Box"
    elif names[i] == f"balance_{stage_2}":
        names[i] = "Black Box"
    elif names[i] == f"balance_{stage_3}":
        names[i] = "Black Box"

if sankey_labels_absolute == True:
    numbers = sizes["value"].tolist()
    formatted_numbers = ["{:,.0f}".format(num) for num in numbers]
    labels = [str(x) + " " + str(y) for x, y in zip(names, formatted_numbers)]
else:
    numbers = sizes["share_by_stage"].tolist()
    formatted_percentages = ["{:.0%}".format(num) for num in numbers]
    labels = [str(x) + " " + str(y) for x, y in zip(names, formatted_percentages)]

# %% ---------------------- Values ----------------------

# Extract source, target, and value columns
source = sankey_flows_final["source"].tolist()
target = sankey_flows_final["target"].tolist()
value = sankey_flows_final["value"].tolist()


# Define link and node dictionaries for the Sankey diagram
link = dict(source=source, target=target, value=value, color=colours_links)

node = {
    "label": labels,
    "pad": 0,
    "thickness": 30,
    "x": x_position,
    "y": y_position,
    "color": colours_nodes,
}


# %% ---------------------- Plotting ---------------------------

width = (30 / 2.54) * 96
height = (18 / 2.54) * 96

fig = go.Figure(go.Sankey(arrangement="perpendicular", link=link, node=node))

fig.update_layout(
    hovermode="x",
    font=dict(size=10),
    margin=dict(l=20, r=20, b=10, t=65),
    title_text=title_text,
    title_x=0.015,
    height=height,
    width=width,
)

# Adding headers for mining, smelting and refining
annotations = [stage_1, stage_2, stage_3, stage_4]
annotation_positions = [-0.01, 0.31, 0.69, 1.005]

for i in range(len(annotations)):
    fig.add_annotation(
        x=annotation_positions[i],
        y=1.04,
        text=annotations[i],
        showarrow=False,
        font=dict(size=12),
    )

fig.show(renderer="browser")
fig.write_image("sankey.svg", engine="kaleido")
fig.write_html("sankey.html")
