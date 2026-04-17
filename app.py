import streamlit as st
import pandas as pd
import plotly.express as px
import re

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="Swiggy Analytics", layout="wide", page_icon="🍔")

# -------------------------------
# CUSTOM CSS
# -------------------------------
st.markdown("""
    <style>
    .metric-card {
        background-color: var(--secondary-background-color);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ff5200;
    }
    .metric-label {
        font-size: 1.1rem;
        color: var(--text-color);
        opacity: 0.8;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# LOAD AND PREPROCESS DATA
# -------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("D:\Swiggy_Data_Analytics_Python_Project\data\swiggy_file.csv")
    
    # 1. Clean Price
    def extract_price(text):
        if pd.isna(text): return None
        match = re.search(r'\d+', str(text))
        return int(match.group()) if match else None
        
    df['Price'] = df['Average Price'].apply(extract_price)
    
    # 2. Clean Ratings
    df['Rating_Num'] = pd.to_numeric(df['Rating'], errors='coerce')
    
    # 3. Clean Number of Ratings
    def extract_rating_count(text):
        if pd.isna(text): return None
        text = str(text).lower().replace('ratings', '').replace('+', '').strip()
        if text in ["too few", "new", "--", ""]: return None
        if 'k' in text:
            try: return int(float(text.replace('k', '')) * 1000)
            except: return None
        try: return int(text)
        except: return None
        
    df['Ratings_Count'] = df['Number of Ratings'].apply(extract_rating_count)
    return df

with st.spinner("Loading and Cleaning Data..."):
    df = load_data()

# -------------------------------
# APP HEADER
# -------------------------------
st.title("🍔 Swiggy Restaurant Insights Dashboard")
st.markdown("An interactive, professional dashboard analyzing Swiggy's restaurant listings, pricing, and ratings across locations.")

# -------------------------------
# SIDEBAR FILTERS
# -------------------------------
st.sidebar.header("🔍 Filters")

# Location Filter
locations = sorted(df['Location'].dropna().unique().tolist())
default_locs = locations[:5] if len(locations) > 5 else locations
selected_locs = st.sidebar.multiselect("📍 Select Location(s)", locations, default=default_locs)

# Dietary Filter
veg_options = ["All", "Pure Veg", "Non Veg"]
selected_veg = st.sidebar.selectbox("🥗 Dietary Preference", veg_options)

# Cuisine Filter
all_cuisines = sorted(list(set(df['Cuisine'].dropna().str.split(',').explode().str.strip())))
selected_cuisines = st.sidebar.multiselect("🍕 Select Cuisine(s)", all_cuisines, default=[])

# Price Range Filter
# Provide fallback logic if the column is entirely empty
if not df['Price'].dropna().empty:
    min_price = int(df['Price'].dropna().min())
    max_price = int(df['Price'].dropna().max())
else:
    min_price, max_price = 0, 1000

selected_price = st.sidebar.slider("💰 Price Range (Cost for Two)", min_price, max_price, (min_price, max_price))

# Minimum Rating Filter
if not df['Rating_Num'].dropna().empty:
    min_rating_val = float(df['Rating_Num'].dropna().min())
    max_rating_val = float(df['Rating_Num'].dropna().max())
else:
    min_rating_val, max_rating_val = 0.0, 5.0

selected_rating = st.sidebar.slider("⭐ Minimum Rating", min_rating_val, max_rating_val, min_rating_val, 0.1)

st.sidebar.markdown("---")
st.sidebar.info("💡 Tip: Use these filters to find the perfect restaurant for you!")

# Filter Dataset based on selections
filtered_df = df.copy()

if selected_locs:
    filtered_df = filtered_df[filtered_df['Location'].isin(selected_locs)]
    
if selected_veg == "Pure Veg":
    filtered_df = filtered_df[filtered_df['Pure Veg'] == 'Yes']
elif selected_veg == "Non Veg":
    filtered_df = filtered_df[filtered_df['Pure Veg'] == 'No']

if selected_cuisines:
    # Use regex to match any of the selected cuisines
    pattern = '|'.join([re.escape(c) for c in selected_cuisines])
    filtered_df = filtered_df[filtered_df['Cuisine'].str.contains(pattern, case=False, na=False)]

# Keep NaNs or those that fall in the range
filtered_df = filtered_df[filtered_df['Price'].isna() | (filtered_df['Price'].between(selected_price[0], selected_price[1]))]
filtered_df = filtered_df[filtered_df['Rating_Num'].isna() | (filtered_df['Rating_Num'] >= selected_rating)]

# Output a warning if no data is left
if filtered_df.empty:
    st.warning("No restaurants found matching the selected filters.")
    st.stop()

# -------------------------------
# TOP KPIs
# -------------------------------
col1, col2, col3, col4, col5 = st.columns(5)

total_restaurants = len(filtered_df)
avg_cost = filtered_df['Price'].mean()
avg_rating = filtered_df['Rating_Num'].mean()
pure_veg_total = len(filtered_df[filtered_df['Pure Veg'] == 'Yes'])
pure_veg_pct = (pure_veg_total / total_restaurants * 100) if total_restaurants > 0 else 0

# New metric: Percentage of restaurants with offers
offers_total = len(filtered_df.dropna(subset=['Offer Name']))
offers_pct = (offers_total / total_restaurants * 100) if total_restaurants > 0 else 0

with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{total_restaurants:,}</div><div class="metric-label">Total Restaurants</div></div>', unsafe_allow_html=True)
with col2:
    val = f"₹{avg_cost:,.0f}" if pd.notna(avg_cost) else "N/A"
    st.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">Avg Cost for Two</div></div>', unsafe_allow_html=True)
with col3:
    val = f"{avg_rating:.1f} ★" if pd.notna(avg_rating) else "N/A"
    st.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">Average Rating</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{pure_veg_pct:.1f}%</div><div class="metric-label">Pure Veg</div></div>', unsafe_allow_html=True)
with col5:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{offers_pct:.1f}%</div><div class="metric-label">Active Offers</div></div>', unsafe_allow_html=True)

st.markdown("---")

# -------------------------------
# TABS CONTENT LAYOUT
# -------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Overview & Cuisines", "📍 Locations & Pricing", "📋 Data Explorer"])

with tab1:
    # Row 1 inside Tab 1
    t1_col1, t1_col2 = st.columns(2)
    with t1_col1:
        st.subheader("🍕 Most Popular Cuisines")
        cuisines = filtered_df['Cuisine'].dropna().str.split(',').explode().str.strip()
        cuisine_counts = cuisines.value_counts().nlargest(10).reset_index()
        cuisine_counts.columns = ['Cuisine', 'Count']
        fig1 = px.pie(
            cuisine_counts, 
            names='Cuisine', 
            values='Count', 
            hole=0.4, 
            color_discrete_sequence=px.colors.sequential.Oranges_r
        )
        fig1.update_traces(textposition='inside', textinfo='percent+label')
        fig1.update_layout(margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

    with t1_col2:
        st.subheader("⭐ Top 10 Rated Restaurants")
        top_rated = filtered_df[filtered_df['Ratings_Count'] > 50].sort_values(by='Rating_Num', ascending=False)
        top_rated = top_rated.drop_duplicates(subset=['Restaurant Name']).head(10)
        
        if not top_rated.empty:
            fig2 = px.bar(
                top_rated, 
                x='Rating_Num', 
                y='Restaurant Name', 
                orientation='h', 
                color='Rating_Num', 
                color_continuous_scale='Greens', 
                labels={'Rating_Num': 'Rating', 'Restaurant Name': 'Restaurant'},
                text='Rating_Num'
            )
            fig2.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Not enough restaurants with 50+ ratings to show top rated.")

with tab2:
    # Row 1 inside Tab 2
    t2_col1, t2_col2 = st.columns(2)
    with t2_col1:
        st.subheader("🏆 Top Locations by Restaurant Count")
        loc_counts = filtered_df['Location'].value_counts().nlargest(10).reset_index()
        loc_counts.columns = ['Location', 'Restaurant Count']
        fig3 = px.bar(
            loc_counts, 
            x='Location', 
            y='Restaurant Count', 
            color='Restaurant Count', 
            color_continuous_scale='Oranges',
            text='Restaurant Count'
        )
        fig3.update_traces(textposition='outside')
        fig3.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig3, use_container_width=True)

    with t2_col2:
        st.subheader("💰 Price vs Rating Correlation")
        samp = filtered_df.dropna(subset=['Price', 'Rating_Num']).sample(n=min(1000, len(filtered_df)), random_state=42)
        if not samp.empty:
            fig4 = px.scatter(
                samp, 
                x='Price', 
                y='Rating_Num', 
                color='Pure Veg', 
                hover_name='Restaurant Name',
                labels={'Rating_Num': 'Rating (out of 5)', 'Price': 'Price for Two (₹)'},
                color_discrete_map={'Yes': '#2ca02c', 'No': '#d62728'},
                opacity=0.7
            )
            fig4.update_layout(margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Not enough data to plot Price vs Rating.")

with tab3:
    st.subheader("📋 Explore Filtered Data")
    st.markdown("Here is the raw data matching your filters. You can sort and search through columns directly.")
    st.dataframe(
        filtered_df[['Restaurant Name', 'Cuisine', 'Location', 'Rating', 'Average Price', 'Number of Ratings', 'Pure Veg', 'Offer Name']].head(100),
        use_container_width=True
    )
    st.caption(f"Showing up to 100 records out of {total_restaurants} matching restaurants.")
    
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download Filtered Data as CSV",
        data=csv,
        file_name='swiggy_filtered.csv',
        mime='text/csv',
    )