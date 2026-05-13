import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Literacy Landscape Research Tool")

# Upload files
survey_file = st.file_uploader("Upload Survey File", type=["xlsx"])
map_file = st.file_uploader("Upload Item Map", type=["xlsx"])

if survey_file and map_file:

    # Load data
    df = pd.read_excel(survey_file, sheet_name="Sheet0")
    df = df.iloc[1:].reset_index(drop=True)

    item_map = pd.read_excel(map_file, sheet_name=0)
    map_df = item_map.dropna(subset=["Question$"]).copy()
    map_df = map_df.set_index("Question$")

    # -----------------------
    # CREATE BLOCK TABS
    # -----------------------
    blocks = map_df["Block"].dropna().unique().tolist()
    tabs = st.tabs(blocks)

    # -----------------------
    # LOOP THROUGH BLOCKS
    # -----------------------
    for i, block in enumerate(blocks):

        with tabs[i].header(block):

            # Filter items for this block
            block_items = map_df[map_df["Block"] == block]
            questions = [q for q in block_items.index if q in df.columns]

            # ✅ AUTO-FILTER RESPONDENTS BY STAKEHOLDER
            stakeholders_for_block = block_items["Stakeholder"].dropna().unique()

            df_block = df.copy()

            if "Q1.2" in df.columns:
                df_block = df_block[df_block["Q1.2"].isin(stakeholders_for_block)]

            st.write(f"Responses in this block: {len(df_block)}")
            st.write(f"Items in this block: {len(questions)}")

            # -----------------------
            # SUB-TABS
            # -----------------------
            subtab1, subtab2, subtab3 = st.tabs([
                "Explore",
                "Cross-Tabs",
                "Descriptives"
            ])

            # =======================
            # EXPLORE TAB
            # =======================
            with subtab1:
                st.subheader("Explore Item")

                question_labels = {
                    q: map_df.loc[q, "Question or prompt"]
                    for q in questions
                }

                selected_q = st.selectbox(
                    "Select Question",
                    options=questions,
                    format_func=lambda x: question_labels[x],
                    key=f"explore_q_{i}"
                )

                base = selected_q.split("_")[0]
                multi_cols = [c for c in questions if c.startswith(base + "_")]

                st.write(question_labels[selected_q])

                if len(multi_cols) <= 1:
                    counts = df_block[selected_q].value_counts().reset_index()
                    counts.columns = ["Response", "Count"]

                    fig = px.bar(counts, x="Response", y="Count")
                    st.plotly_chart(fig, use_container_width=True)

                else:
                    counts = {c: df_block[c].notna().sum() for c in multi_cols}

                    plot_df = pd.DataFrame({
                        "Option": list(counts.keys()),
                        "Count": list(counts.values())
                    })

                    fig = px.bar(plot_df, x="Option", y="Count")
                    st.plotly_chart(fig, use_container_width=True)

            # =======================
            # CROSS-TABS
            # =======================
            with subtab2:
                st.subheader("Cross-Tab Builder")

                df_filtered = df_block.copy()

                # MULTI FILTERS
                num_filters = st.number_input(
                    "How many filters?",
                    min_value=1,
                    max_value=5,
                    value=2,
                    key=f"ct_filters_{i}"
                )

                selected_filters = []

                for j in range(num_filters):
                    st.markdown(f"**Filter {j+1}**")

                    col1, col2 = st.columns(2)

                    with col1:
                        filter_var = st.selectbox(
                            f"Variable {j+1}",
                            df_block.columns,
                            key=f"ct_var_{i}_{j}"
                        )

                    with col2:
                        filter_vals = st.multiselect(
                            f"Values {j+1}",
                            df_block[filter_var].dropna().unique(),
                            key=f"ct_val_{i}_{j}"
                        )

                    selected_filters.append((filter_var, filter_vals))

                # Apply filters
                for var, vals in selected_filters:
                    if vals:
                        df_filtered = df_filtered[df_filtered[var].isin(vals)]

                st.write(f"Filtered N = {len(df_filtered)}")

                # Crosstab
                var1 = st.selectbox(
                    "Row Variable",
                    questions,
                    key=f"row_{i}"
                )

                var2 = st.selectbox(
                    "Column Variable",
                    questions,
                    key=f"col_{i}"
                )

                normalize = st.selectbox(
                    "Normalize",
                    ["None", "Row", "Column"],
                    key=f"norm_{i}"
                )

                if normalize == "Row":
                    ct = pd.crosstab(df_filtered[var1], df_filtered[var2], normalize="index")
                elif normalize == "Column":
                    ct = pd.crosstab(df_filtered[var1], df_filtered[var2], normalize="columns")
                else:
                    ct = pd.crosstab(df_filtered[var1], df_filtered[var2])

                st.dataframe(ct)

                fig = px.imshow(ct, text_auto=True, aspect="auto")
                st.plotly_chart(fig)

            # =======================
            # DESCRIPTIVES
            # =======================
            with subtab3:
                st.subheader("Descriptives Engine")

                df_filtered = df_block.copy()

                # MULTI FILTERS
                num_filters = st.number_input(
                    "How many filters?",
                    min_value=1,
                    max_value=5,
                    value=2,
                    key=f"desc_filters_{i}"
                )

                selected_filters = []

                for j in range(num_filters):
                    st.markdown(f"**Filter {j+1}**")

                    col1, col2 = st.columns(2)

                    with col1:
                        filter_var = st.selectbox(
                            f"Variable {j+1}",
                            df_block.columns,
                            key=f"desc_var_{i}_{j}"
                        )

                    with col2:
                        filter_vals = st.multiselect(
                            f"Values {j+1}",
                            df_block[filter_var].dropna().unique(),
                            key=f"desc_val_{i}_{j}"
                        )

                    selected_filters.append((filter_var, filter_vals))

                # Apply filters
                for var, vals in selected_filters:
                    if vals:
                        df_filtered = df_filtered[df_filtered[var].isin(vals)]

                st.write(f"Filtered N = {len(df_filtered)}")

                # Pillar filter
                pillars = [
                    "General","Educator Prep","Leadership","HQIM",
                    "Effective Instruction","Professional Learning",
                    "Families","Assessment"
                ]

                sel_pillar = st.selectbox(
                    "Select Pillar",
                    ["All"] + pillars,
                    key=f"pillar_{i}"
                )

                subset = block_items.copy()

                if sel_pillar != "All":
                    subset = subset[subset[sel_pillar].notna()]

                questions_subset = [
                    q for q in subset.index if q in df_filtered.columns
                ]

                st.write(f"{len(questions_subset)} items selected")

                # Results
                results = []

                for q in questions_subset:
                    vc = df_filtered[q].value_counts(normalize=True)

                    for resp, val in vc.items():
                        results.append({
                            "Question": map_df.loc[q, "Question or prompt"],
                            "Response": resp,
                            "Percent": round(val, 3)
                        })

                res_df = pd.DataFrame(results)
                st.dataframe(res_df)
