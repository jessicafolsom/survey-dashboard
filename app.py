import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Literacy Landscape Research Tool")

# Upload files
survey_file = st.file_uploader("Upload Survey File", type=["xlsx"])
map_file = st.file_uploader("Upload Item Map", type=["xlsx"])

if survey_file and map_file:

    df = pd.read_excel(survey_file, sheet_name="Sheet0")
    df = df.iloc[1:].reset_index(drop=True)

    item_map = pd.read_excel(map_file, sheet_name=0)
    map_df = item_map.dropna(subset=["Question$"]).copy()
    map_df = map_df.set_index("Question$")

    # Sidebar filters
    st.sidebar.header("Filters")

    stakeholder_col = "Q1.2"
    stakeholders = st.sidebar.multiselect(
        "Respondent Stakeholder",
        df[stakeholder_col].dropna().unique(),
        default=df[stakeholder_col].dropna().unique()
    )
    df = df[df[stakeholder_col].isin(stakeholders)]

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Explore Item",
        "Cross-Tabs",
        "Descriptives",
        "Stakeholder Comparison"
    ])

    # -----------------------
    # TAB 1: Explore Item
    # -----------------------
    with tab1:
        st.header("Explore Item")

        question_labels = {
            q: map_df.loc[q, "Question or prompt"]
            for q in map_df.index if q in df.columns
        }

        selected_q = st.selectbox(
            "Select Question",
            options=list(question_labels.keys()),
            format_func=lambda x: question_labels[x]
        )

        base = selected_q.split("_")[0]
        multi_cols = [c for c in df.columns if c.startswith(base + "_")]

        st.subheader(question_labels[selected_q])

        if len(multi_cols) <= 1:
            counts = df[selected_q].value_counts().reset_index()
            counts.columns = ["Response", "Count"]

            fig = px.bar(counts, x="Response", y="Count")
            st.plotly_chart(fig, use_container_width=True)

        else:
            counts = {c: df[c].notna().sum() for c in multi_cols}

            plot_df = pd.DataFrame({
                "Option": list(counts.keys()),
                "Count": list(counts.values())
            })

            fig = px.bar(plot_df, x="Option", y="Count")
            st.plotly_chart(fig, use_container_width=True)

    # -----------------------
    # TAB 2: Cross-Tabs
    # -----------------------
    with tab2:
        st.header("Cross-Tab Builder")

        st.subheader("Step 1: Apply Filters")

        df_filtered = df.copy()

        num_filters = st.number_input(
            "How many filters do you want?",
            min_value=1,
            max_value=5,
            value=2
        )

        selected_filters = []

        for i in range(num_filters):
            st.markdown(f"**Filter {i+1}**")

            col1, col2 = st.columns(2)

            with col1:
                filter_var = st.selectbox(
                    f"Variable {i+1}",
                    df.columns,
                    key=f"var_{i}"
                )

            with col2:
                filter_vals = st.multiselect(
                    f"Values {i+1}",
                    df[filter_var].dropna().unique(),
                    key=f"val_{i}"
                )

            selected_filters.append((filter_var, filter_vals))

        for var, vals in selected_filters:
            if vals:
                df_filtered = df_filtered[df_filtered[var].isin(vals)]

        st.write(f"Filtered N = {len(df_filtered)}")

        st.subheader("Step 2: Build Crosstab")

        var1 = st.selectbox("Row Variable", df.columns, key="row")
        var2 = st.selectbox("Column Variable", df.columns, key="col")

        normalize = st.selectbox("Normalize", ["None", "Row", "Column"])

        if normalize == "Row":
            ct = pd.crosstab(df_filtered[var1], df_filtered[var2], normalize="index")
        elif normalize == "Column":
            ct = pd.crosstab(df_filtered[var1], df_filtered[var2], normalize="columns")
        else:
            ct = pd.crosstab(df_filtered[var1], df_filtered[var2])

        st.dataframe(ct)

        fig = px.imshow(ct, text_auto=True, aspect="auto")
        st.plotly_chart(fig)


    # -----------------------
    # TAB 3: Descriptives
    # -----------------------
    with tab3:
        st.header("Descriptives Engine")

        sel_pillar = st.selectbox("Pillar", ["All"] + [
            "General","Educator Prep","Leadership","HQIM",
            "Effective Instruction","Professional Learning",
            "Families","Assessment"
        ])

        subset = map_df.copy()

        if sel_pillar != "All":
            subset = subset[subset[sel_pillar].notna()]

        questions = [q for q in subset.index if q in df.columns]

        st.write(f"{len(questions)} items")

        results = []

        for q in questions:
            vc = df[q].value_counts(normalize=True)
            for resp, val in vc.items():
                results.append({
                    "Question": map_df.loc[q, "Question or prompt"],
                    "Response": resp,
                    "Percent": val
                })

        res_df = pd.DataFrame(results)
        st.dataframe(res_df)

    # -----------------------
    # TAB 4: Stakeholder Comparison
    # -----------------------
    with tab4:
        st.header("Cross-Stakeholder Comparison")

        prompts = map_df["Question or prompt"].dropna().unique()

        selected_prompt = st.selectbox("Select Question Prompt", prompts)

        cols = map_df[
            map_df["Question or prompt"] == selected_prompt
        ].index.tolist()

        cols = [c for c in cols if c in df.columns]

        if len(cols) > 1:

            comp = {}

            for c in cols:
                label = map_df.loc[c, "Stakeholder"]
                comp[label] = df[c].value_counts(normalize=True)

            comp_df = pd.DataFrame(comp).fillna(0)

            st.dataframe(comp_df)

            fig = px.bar(comp_df, barmode="group")
            st.plotly_chart(fig)

        else:
            st.write("No comparable stakeholders.")
