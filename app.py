"""
CodeAlpha Data Analytics - Task 1: Web Scraping Interactive Dashboard
Enterprise Streamlit Web Application featuring interactive Plotly charts,
dynamic KPI metrics, full catalog filtering, and multi-format data export.
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.config import CONFIG

# Page Configuration
st.set_page_config(
    page_title="CodeAlpha | Web Scraping & Data Analytics",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Theme and Styling
st.markdown("""
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4b5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 1px solid #bae6fd;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0369a1;
    }
    .metric-lbl {
        font-size: 0.9rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Loads and caches cleaned book dataset."""
    cleaned_path = CONFIG.paths.cleaned_csv_path
    raw_path = CONFIG.paths.raw_csv_path

    if os.path.exists(cleaned_path):
        df = pd.read_csv(cleaned_path)
    elif os.path.exists(raw_path):
        from src.data_cleaner import DataCleaner
        cleaner = DataCleaner()
        df = cleaner.clean_and_save()
    else:
        return pd.DataFrame()

    df["price_gbp"] = pd.to_numeric(df["price_gbp"], errors="coerce").fillna(0.0)
    df["rating_num"] = pd.to_numeric(df["rating_num"], errors="coerce").fillna(0).astype(int)
    df["stock_quantity"] = pd.to_numeric(df["stock_quantity"], errors="coerce").fillna(0).astype(int)
    if "inventory_value_gbp" in df.columns:
        df["inventory_value_gbp"] = pd.to_numeric(df["inventory_value_gbp"], errors="coerce").fillna(0.0)
    return df


def main():
    st.markdown('<div class="main-title">📚 CodeAlpha Data Analytics: Web Scraping Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Interactive exploration and exploratory data analysis of scraped book catalog data from <i>Books to Scrape</i>.</div>', unsafe_allow_html=True)

    df = load_data()
    if df.empty:
        st.warning("⚠️ No dataset found. Please execute `python main.py` in the terminal to generate the initial dataset.")
        return

    # Sidebar Controls
    st.sidebar.image("https://images.unsplash.com/photo-1507842229452-77292210a40f?w=400&q=80", use_container_width=True)
    st.sidebar.header("🔍 Filter Catalog")

    search_query = st.sidebar.text_input("Search Title", placeholder="e.g. Secret, Light, Love...")

    all_categories = sorted(df["category"].dropna().unique().tolist())
    selected_categories = st.sidebar.multiselect(
        "Select Categories",
        options=all_categories,
        default=all_categories[:8] if len(all_categories) > 8 else all_categories
    )

    min_price = float(df["price_gbp"].min())
    max_price = float(df["price_gbp"].max())
    price_range = st.sidebar.slider(
        "Price Range (£)",
        min_value=min_price,
        max_value=max_price,
        value=(min_price, max_price),
        step=1.0
    )

    min_rating = st.sidebar.slider("Minimum Rating (Stars)", min_value=1, max_value=5, value=1, step=1)
    in_stock_only = st.sidebar.checkbox("In-Stock Only", value=True)

    # Filter Data
    filtered_df = df.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df["title"].str.contains(search_query, case=False, na=False)]
    if selected_categories:
        filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]
    filtered_df = filtered_df[
        (filtered_df["price_gbp"] >= price_range[0]) &
        (filtered_df["price_gbp"] <= price_range[1]) &
        (filtered_df["rating_num"] >= min_rating)
    ]
    if in_stock_only and "in_stock" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["in_stock"] == True]

    # KPI Metrics Row
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Total Titles</div>
            <div class="metric-val">{len(filtered_df):,}</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        avg_p = filtered_df["price_gbp"].mean() if not filtered_df.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Avg Price</div>
            <div class="metric-val">£{avg_p:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        avg_r = filtered_df["rating_num"].mean() if not filtered_df.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Avg Rating</div>
            <div class="metric-val">{avg_r:.2f} / 5</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        tot_units = filtered_df["stock_quantity"].sum() if not filtered_df.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Units in Stock</div>
            <div class="metric-val">{int(tot_units):,}</div>
        </div>
        """, unsafe_allow_html=True)
    with k5:
        tot_val = filtered_df["inventory_value_gbp"].sum() if "inventory_value_gbp" in filtered_df.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Stock Value</div>
            <div class="metric-val">£{tot_val:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main Tabs
    tab_analytics, tab_catalog, tab_methodology = st.tabs([
        "📊 Interactive Visual Analytics",
        "📋 Book Catalog Table",
        "🛠️ Architecture & Methodology"
    ])

    with tab_analytics:
        col_left, col_right = st.columns(2)

        with col_left:
            # 1. Price Distribution (Plotly)
            st.subheader("Price Distribution (£)")
            if not filtered_df.empty:
                fig_p = px.histogram(
                    filtered_df,
                    x="price_gbp",
                    nbins=25,
                    color_discrete_sequence=["#2563eb"],
                    marginal="box",
                    hover_data=["title", "category", "rating_num"],
                    labels={"price_gbp": "Price in GBP (£)"}
                )
                fig_p.update_layout(bargap=0.05, template="plotly_white", margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_p, use_container_width=True)
            else:
                st.info("No records matching current filters.")

            # 2. Price vs Rating Box Plot (Plotly)
            st.subheader("Price Distribution across Star Ratings")
            if not filtered_df.empty:
                plot_df = filtered_df.copy()
                plot_df["rating_label"] = plot_df["rating_num"].apply(lambda x: f"{int(x)} Star" if int(x) == 1 else f"{int(x)} Stars")
                order = [f"{i} Star" if i == 1 else f"{i} Stars" for i in sorted(plot_df["rating_num"].unique())]

                fig_box = px.box(
                    plot_df,
                    x="rating_label",
                    y="price_gbp",
                    color="rating_label",
                    category_orders={"rating_label": order},
                    labels={"rating_label": "Star Rating", "price_gbp": "Price (£)"},
                    hover_data=["title", "category"]
                )
                fig_box.update_layout(showlegend=False, template="plotly_white", margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_box, use_container_width=True)

        with col_right:
            # 3. Star Ratings Breakdown (Plotly)
            st.subheader("Book Count by Star Rating")
            if not filtered_df.empty:
                rc = filtered_df["rating_num"].value_counts().sort_index().reset_index()
                rc.columns = ["rating", "count"]
                rc["rating_label"] = rc["rating"].apply(lambda x: f"{int(x)} Star" if int(x) == 1 else f"{int(x)} Stars")

                fig_r = px.bar(
                    rc,
                    x="rating_label",
                    y="count",
                    color="rating_label",
                    text="count",
                    labels={"rating_label": "Star Rating", "count": "Book Count"}
                )
                fig_r.update_layout(showlegend=False, template="plotly_white", margin=dict(l=20, r=20, t=30, b=20))
                fig_r.update_traces(textposition="outside")
                st.plotly_chart(fig_r, use_container_width=True)

            # 4. Top Categories by Average Price (Plotly)
            st.subheader("Top Categories Ranked by Avg Price (£)")
            if not filtered_df.empty:
                cat_avg = filtered_df.groupby("category")["price_gbp"].agg(["mean", "count"]).reset_index()
                cat_avg = cat_avg.sort_values(by="mean", ascending=True).tail(10)

                fig_cat = px.bar(
                    cat_avg,
                    y="category",
                    x="mean",
                    orientation="h",
                    color="mean",
                    color_continuous_scale="Viridis",
                    labels={"mean": "Average Price (£)", "category": "Category"},
                    text_auto=".2f"
                )
                fig_cat.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_cat, use_container_width=True)

    with tab_catalog:
        st.subheader(f"Filtered Results ({len(filtered_df)} titles)")
        display_cols = ["title", "category", "price_gbp", "rating_num", "stock_quantity", "inventory_value_gbp", "book_url"]
        avail_cols = [c for c in display_cols if c in filtered_df.columns]

        st.dataframe(
            filtered_df[avail_cols].rename(columns={
                "title": "Title",
                "category": "Category",
                "price_gbp": "Price (£)",
                "rating_num": "Rating",
                "stock_quantity": "Stock",
                "inventory_value_gbp": "Stock Value (£)",
                "book_url": "Product URL"
            }),
            use_container_width=True,
            height=450
        )

        c1, c2, _ = st.columns([1, 1, 2])
        with c1:
            csv_data = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Filtered CSV",
                data=csv_data,
                file_name="books_scraped_filtered.csv",
                mime="text/csv"
            )
        with c2:
            json_data = filtered_df.to_json(orient="records", indent=2).encode("utf-8")
            st.download_button(
                label="📥 Download Filtered JSON",
                data=json_data,
                file_name="books_scraped_filtered.json",
                mime="application/json"
            )

    with tab_methodology:
        st.markdown("""
        ### Web Scraping Pipeline Architecture
        This project was developed for the **CodeAlpha Data Analytics Internship (Task 1)**.
        
        #### 1. Target Public Source
        - **Source**: [Books to Scrape](http://books.toscrape.com/)
        - **Scale**: 1,000 book titles across 50 categories and 50 pages.
        - **Ethics**: Hosted specifically for legal, ethical scraping practice with zero terms-of-service violations.
        
        #### 2. Technology Stack & Design Patterns
        - **Requests & BeautifulSoup4**: Traverses pagination DOM hierarchy, parsing tags, classes, and nested links.
        - **ThreadPoolExecutor**: Concurrent HTTP requests with connection pooling and exponential backoff.
        - **Pandas**: Automated currency normalization, regex pattern extraction, star mapping, and price tier binning.
        - **Plotly & Seaborn**: Interactive and publication-ready statistical visualizations.
        - **Streamlit**: Responsive business intelligence dashboard.
        """)


if __name__ == "__main__":
    main()
