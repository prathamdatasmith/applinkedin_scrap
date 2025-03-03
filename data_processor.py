import pandas as pd
import numpy as np
from collections import Counter
import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
import os
from llm_analyzer import LLMAnalyzer

class DataProcessor:
    CITY_COORDINATES = {
        'Bangalore': {'lat': 12.9716, 'lon': 77.5946},
        'Mumbai': {'lat': 19.0760, 'lon': 72.8777},
        'Hyderabad': {'lat': 17.3850, 'lon': 78.4867},
        'Delhi': {'lat': 28.6139, 'lon': 77.2090},
        'Pune': {'lat': 18.5204, 'lon': 73.8567},
        'Chennai': {'lat': 13.0827, 'lon': 80.2707},
        'Gurgaon': {'lat': 28.4595, 'lon': 77.0266},
        'Noida': {'lat': 28.5355, 'lon': 77.3910},
        'Kolkata': {'lat': 22.5726, 'lon': 88.3639},
        'Ahmedabad': {'lat': 23.0225, 'lon': 72.5714}
    }

    @staticmethod
    def load_data(file):
        """Load and validate data from CSV file"""
        try:
            df = pd.read_csv(file)
            
            # Standardize column names
            column_mappings = {
                # Map various possible input column names to our standard names
                'Job Title': 'job_title',
                'Title': 'job_title',
                'Position': 'job_title',
                'Role': 'job_title',
                
                'Company Name': 'company',
                'Company': 'company',
                'Employer': 'company',
                'Organization': 'company',
                
                'Location': 'location',
                'Place': 'location',
                'City': 'location',
                
                'Tech Stack': 'tech_stack',
                'Technologies': 'tech_stack',
                'Skills': 'tech_stack',
                'Requirements': 'tech_stack'
            }
            
            # Rename columns if they exist in the mapping
            df = df.rename(columns=lambda x: column_mappings.get(x, x))
            
            # Ensure required columns exist
            required_columns = ['job_title', 'company', 'location', 'tech_stack']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = 'Not specified'
            
            # Clean and standardize the data
            df['job_title'] = df['job_title'].fillna('Not specified').astype(str).str.strip()
            df['company'] = df['company'].fillna('Not specified').astype(str).str.strip()
            df['location'] = df['location'].fillna('Not specified').astype(str).str.strip()
            df['tech_stack'] = df['tech_stack'].fillna('Not specified').astype(str).str.strip()
            
            # Create technologies list
            df['technologies'] = df['tech_stack'].apply(lambda x: 
                [item.strip() for item in str(x).split(',') if item.strip()] if pd.notna(x) else []
            )
            
            return df
            
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return pd.DataFrame(columns=['job_title', 'company', 'location', 'tech_stack'])

    @staticmethod
    def calculate_kpis(df):
        kpis = {
            'tech_demand': DataProcessor._calculate_tech_demand(df),
            'company_hiring_velocity': DataProcessor._calculate_hiring_velocity(df),
            'location_concentration': DataProcessor._calculate_location_concentration(df),
            'skill_correlation': DataProcessor._calculate_skill_correlation(df),
            'rare_skills': DataProcessor._find_rare_skills(df),
            'tech_clustering': DataProcessor._cluster_technologies(df)
        }
        return kpis

    @staticmethod
    def _calculate_tech_demand(df):
        all_tech = [tech for techs in df['technologies'] for tech in techs]
        return pd.Series(Counter(all_tech)).sort_values(ascending=False)

    @staticmethod
    def _calculate_hiring_velocity(df):
        return df.groupby('company').agg({
            'job_title': 'count',
            'location': lambda x: len(set(x)),
            'tech_stack': lambda x: len(set(','.join(x).split(',')))
        }).rename(columns={
            'job_title': 'job_count',
            'location': 'locations_count',
            'tech_stack': 'unique_technologies'
        })

    @staticmethod
    def _calculate_location_concentration(df):
        location_stats = df.groupby('location').agg({
            'job_title': 'count',
            'company': 'nunique',
            'tech_stack': lambda x: len(set(','.join(x).split(',')))
        })
        location_stats['tech_diversity'] = location_stats['tech_stack'] / location_stats['job_title']
        return location_stats

    @staticmethod
    def _calculate_skill_correlation(df):
        tech_pairs = []
        for techs in df['technologies']:
            for i in range(len(techs)):
                for j in range(i+1, len(techs)):
                    tech_pairs.append(tuple(sorted([techs[i], techs[j]])))
        return pd.Series(Counter(tech_pairs))

    @staticmethod
    def _find_rare_skills(df):
        all_tech = [tech for techs in df['technologies'] for tech in techs]
        tech_counts = Counter(all_tech)
        return {tech: count for tech, count in tech_counts.items() if count <= 3}

    @staticmethod
    def _cluster_technologies(df):
        G = nx.Graph()
        for techs in df['technologies']:
            for i in range(len(techs)):
                for j in range(i+1, len(techs)):
                    if not G.has_edge(techs[i], techs[j]):
                        G.add_edge(techs[i], techs[j], weight=1)
                    else:
                        G[techs[i]][techs[j]]['weight'] += 1
        return list(nx.community.greedy_modularity_communities(G))

    @staticmethod
    def generate_visualizations(df: pd.DataFrame) -> dict:
        plots = {}
        
        # 1. Job Distribution by City
        city_counts = df['city'].value_counts().head(10)
        plots['city_distribution'] = px.bar(
            x=city_counts.index,
            y=city_counts.values,
            title='Top 10 Cities by Job Postings',
            labels={'x': 'City', 'y': 'Number of Jobs'},
            template='plotly_white'
        )

        # 2. Technology Distribution
        tech_counts = Counter([tech for techs in df['technologies'] for tech in techs]).most_common(15)
        tech_df = pd.DataFrame(tech_counts, columns=['Technology', 'Count'])
        plots['tech_distribution'] = px.bar(
            tech_df,
            x='Technology',
            y='Count',
            title='Top 15 Most In-Demand Technologies',
            template='plotly_white'
        )

        # 3. Company Analysis
        company_counts = df['company'].value_counts().head(10)
        plots['company_distribution'] = px.pie(
            values=company_counts.values,
            names=company_counts.index,
            title='Top 10 Companies by Job Postings',
            hole=0.4,
            template='plotly_white'
        )

        # 4. Technology Trends Over Time (if date column exists)
        if 'date_posted' in df.columns:
            df['date_posted'] = pd.to_datetime(df['date_posted'])
            tech_trends = df.groupby('date_posted')['technologies'].agg(lambda x: len([item for sublist in x for item in sublist]))
            plots['tech_trends'] = px.line(
                x=tech_trends.index,
                y=tech_trends.values,
                title='Technology Demand Trends',
                labels={'x': 'Date', 'y': 'Number of Technology Mentions'},
                template='plotly_white'
            )

        return plots

    @staticmethod
    def extract_advanced_insights(df: pd.DataFrame) -> dict:
        """Extract detailed insights for AI analysis"""
        insights = {
            'market_overview': {
                'total_jobs': len(df),
                'unique_companies': df['company'].nunique(),
                'locations': df['location'].nunique(),
                'avg_tech_per_job': df['tech_stack'].str.count(',').mean() + 1
            },
            'tech_trends': {
                'top_technologies': Counter(
                    tech.strip() 
                    for techs in df['tech_stack'].str.split(',') 
                    for tech in techs
                ).most_common(15),
                'emerging_tech': [
                    tech for tech, count in Counter(
                        tech.strip() 
                        for techs in df['tech_stack'].str.split(',') 
                        for tech in techs
                    ).items() 
                    if count <= 3
                ]
            },
            'location_insights': {
                'top_cities': df['city'].value_counts().head(10).to_dict(),
                'remote_jobs': len(df[df['location'].str.contains('Remote', case=False)])
            },
            'company_insights': {
                'top_hiring': df['company'].value_counts().head(10).to_dict(),
                'tech_diversity': df.groupby('company')['tech_stack'].apply(
                    lambda x: len(set(','.join(x).split(',')))
                ).sort_values(ascending=False).head(10).to_dict()
            }
        }
        return insights

    @staticmethod
    def get_summary_stats(df: pd.DataFrame) -> dict:
        return {
            'total_jobs': len(df),
            'unique_companies': df['company'].nunique(),
            'unique_cities': df['city'].nunique(),
            'top_technologies': Counter([tech for techs in df['technologies'] for tech in techs]).most_common(5),
            'avg_tech_per_job': sum(len(techs) for techs in df['technologies']) / len(df)
        }

    @staticmethod
    def analyze_tech_combinations(df: pd.DataFrame) -> pd.DataFrame:
        """Analyze which technologies are commonly used together"""
        tech_combinations = []
        for techs in df['technologies']:
            if len(techs) > 1:
                for i in range(len(techs)):
                    for j in range(i+1, len(techs)):
                        tech_combinations.append(tuple(sorted([techs[i], techs[j]])))
        
        combo_df = pd.DataFrame(
            pd.Series(tech_combinations).value_counts().head(20)
        ).reset_index()
        combo_df.columns = ['Technology Pair', 'Count']
        return combo_df

    @staticmethod
    def analyze_time_trends(df: pd.DataFrame) -> dict:
        """Analyze posting trends over time"""
        if 'date_posted' not in df.columns:
            return {}
        
        df['date_posted'] = pd.to_datetime(df['date_posted'])
        daily_posts = df.groupby('date_posted').size()
        tech_trends = df.groupby('date_posted')['technologies'].agg(
            lambda x: len([item for sublist in x for item in sublist])
        )
        
        return {
            'daily_posts': daily_posts,
            'tech_trends': tech_trends
        }

    @staticmethod
    def create_tech_network(df: pd.DataFrame) -> dict:
        """Create network data for technology relationships"""
        tech_links = []
        for techs in df['technologies']:
            if len(techs) > 1:
                for i in range(len(techs)):
                    for j in range(i+1, len(techs)):
                        tech_links.append((techs[i], techs[j]))
        
        # Convert to network format
        nodes = list(set([tech for techs in df['technologies'] for tech in techs]))
        edges = pd.DataFrame(tech_links, columns=['source', 'target'])
        edges['value'] = 1
        edges = edges.groupby(['source', 'target'])['value'].sum().reset_index()
        
        return {
            'nodes': nodes,
            'edges': edges.to_dict('records')
        }

    @staticmethod
    def generate_ai_insights(df: pd.DataFrame) -> dict:
        """Generate AI-powered insights using LLM"""
        llm = LLMAnalyzer()
        insights = llm.generate_insights(df)
        return insights

    @staticmethod
    def create_improved_tech_city_viz(df: pd.DataFrame) -> go.Figure:
        """Create a better visualization for technology distribution by city"""
        # Create a matrix of technologies per city
        tech_city_matrix = {}
        for _, row in df.iterrows():
            city = row['city']
            if city not in tech_city_matrix:
                tech_city_matrix[city] = {}
            
            for tech in row['technologies']:
                tech_city_matrix[city][tech] = tech_city_matrix[city].get(tech, 0) + 1
        
        # Convert to heatmap data
        cities = list(tech_city_matrix.keys())
        all_techs = set()
        for city_data in tech_city_matrix.values():
            all_techs.update(city_data.keys())
        techs = sorted(list(all_techs))
        
        z_data = []
        for city in cities:
            row = []
            for tech in techs:
                row.append(tech_city_matrix[city].get(tech, 0))
            z_data.append(row)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=techs,
            y=cities,
            colorscale='Viridis'
        ))
        
        fig.update_layout(
            title='Technology Distribution by City (Heatmap)',
            xaxis_title='Technologies',
            yaxis_title='Cities',
            height=800
        )
        
        return fig
