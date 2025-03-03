import streamlit as st
import pandas as pd
from data_processor import DataProcessor
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="Tech Job Market Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with improved styling
st.markdown("""
<style>
    .main-title {
        color: #1E88E5;
        text-align: center;
        padding: 1.5rem;
        margin-bottom: 2rem;
        background: linear-gradient(to right, #1E88E5, #5E35B1);
        color: white;
        border-radius: 10px;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .stPlotlyChart {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    .section-title {
        color: #1E88E5;
        padding: 0.5rem 0;
        border-bottom: 2px solid #1E88E5;
        margin-bottom: 1rem;
    }
    .custom-info-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

def check_required_columns(df):
    required_columns = ['job_title', 'company', 'location', 'tech_stack']
    missing_columns = [col for col in required_columns if col not in df.columns]
    return missing_columns

def validate_data(df):
    """Validate uploaded data with improved column name matching"""
    required_columns = ['job_title', 'company', 'location', 'tech_stack']
    
    # Convert column names to lowercase and remove spaces/special characters
    df.columns = df.columns.str.lower().str.strip().str.replace('[^a-z0-9]', '_')
    
    # Specific mapping for the provided CSV columns
    column_mapping = {
        'job_title': 'job_title',
        'company_name': 'company',
        'location': 'location',
        'tech_stack': 'tech_stack'
    }
    
    # Apply the mapping
    try:
        df.rename(columns=column_mapping, inplace=True)
    except KeyError as e:
        return False, f"Column mapping failed: {str(e)}"
    
    # Verify required columns are present
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        error_message = "\n".join([
            "Missing required columns: " + ", ".join(missing_columns),
            "\nAvailable columns in your file: " + ", ".join(df.columns),
            "\nPlease check column names and ensure they match the required format."
        ])
        return False, error_message
    
    if df.empty:
        return False, "Uploaded file is empty"
        
    return True, ""

def main():
    st.markdown("<h1 class='main-title'>Tech Job Market Analytics Dashboard</h1>", unsafe_allow_html=True)

    # Sidebar configuration
    with st.sidebar:
        st.header("📊 Dashboard Controls")
        uploaded_file = st.file_uploader("Upload LinkedIn Jobs Data (CSV)", type=['csv'])
        
        st.markdown("---")
        st.markdown("### 🔍 Filters")
        if 'df' in locals():
            city_filter = st.multiselect("Filter by City", df['city'].unique())
            tech_filter = st.multiselect("Filter by Technology", sorted(list(set([tech for techs in df['technologies'] for tech in techs]))))
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.info("This dashboard provides real-time analytics of the tech job market based on LinkedIn data.")

    if uploaded_file:
        try:
            # Load CSV with all string columns to avoid type inference issues
            raw_df = pd.read_csv(uploaded_file, dtype=str)
            
            # Validate data
            is_valid, error_message = validate_data(raw_df)
            if not is_valid:
                st.error(error_message)
                return
            
            # Process data if valid
            df = raw_df.copy()
            # Add city extraction from location
            df['city'] = df['location'].str.split(',').str[0]
            # Convert tech_stack to list if it's not already
            if 'technologies' not in df.columns:
                df['technologies'] = df['tech_stack'].str.split(',').apply(lambda x: [t.strip() for t in x] if isinstance(x, list) else [])
            
            kpis = DataProcessor.calculate_kpis(df)
            
            # Market Insights Section
            st.markdown("<h2 class='section-title'>Advanced Market Insights</h2>", unsafe_allow_html=True)
            
            # KPI Dashboard
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Job Postings", len(df))
                st.metric("Unique Companies", df['company'].nunique())
            with col2:
                st.metric("Unique Technologies", len(kpis['tech_demand']))
                st.metric("Rare Skills Found", len(kpis['rare_skills']))
            with col3:
                st.metric("Technology Clusters", len(kpis['tech_clustering']))
                st.metric("Locations", df['location'].nunique())

            # Improved Tabs Structure
            tab1, tab2, tab3 = st.tabs([
                "🔍 Deep Insights", 
                "📊 Technology Analysis", 
                "🌍 Market Distribution"
            ])

            with tab1:
                # Technology Correlation Analysis
                st.subheader("Technology Correlation Analysis")
                top_correlations = kpis['skill_correlation'].nlargest(10)
                correlation_fig = px.bar(
                    x=[f"{pair[0]} - {pair[1]}" for pair in top_correlations.index],
                    y=top_correlations.values,
                    title="Most Common Technology Pairs"
                )
                st.plotly_chart(correlation_fig)

                # Rare Skills Analysis
                st.subheader("Rare Skills in Demand")
                st.write(kpis['rare_skills'])

            with tab2:
                # Technology Demand Trends
                st.subheader("Technology Demand Distribution")
                tech_demand_fig = px.bar(
                    x=kpis['tech_demand'].index[:15],
                    y=kpis['tech_demand'].values[:15],
                    title="Top 15 Technologies in Demand"
                )
                st.plotly_chart(tech_demand_fig)

                # Technology Clusters
                st.subheader("Technology Clusters")
                for i, cluster in enumerate(kpis['tech_clustering'], 1):
                    st.write(f"Cluster {i}:", ", ".join(sorted(cluster)))

            with tab3:
                # Company Hiring Analysis
                st.subheader("Company Hiring Patterns")
                hiring_velocity = kpis['company_hiring_velocity']
                hiring_fig = px.scatter(
                    hiring_velocity,
                    x='job_count',
                    y='unique_technologies',
                    size='locations_count',
                    hover_name=hiring_velocity.index,
                    title="Company Hiring Analysis"
                )
                st.plotly_chart(hiring_fig)

        except Exception as e:
            st.error(f"Error processing data: {str(e)}")
            st.info("Please ensure your CSV file contains the required columns: job_title, company, location, and tech_stack")

    else:
        st.markdown("""
        <div class='custom-info-box'>
            <h3>👋 Welcome to Tech Job Market Analytics!</h3>
            <p>To get started:</p>
            <ol>
                <li>Upload your LinkedIn jobs data CSV file using the sidebar</li>
                <li>Explore interactive visualizations and insights</li>
                <li>Use filters to drill down into specific areas of interest</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
