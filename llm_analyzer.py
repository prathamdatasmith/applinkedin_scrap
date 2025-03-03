import os
from groq import Groq
from dotenv import load_dotenv
import pandas as pd
import json

load_dotenv()

class DataProcessor:
    @staticmethod
    def extract_advanced_insights(df: pd.DataFrame) -> dict:
        # Create tech_stack list if not already done
        if 'technologies' not in df.columns:
            df['technologies'] = df['tech_stack'].str.split(',').apply(lambda x: [t.strip() for t in x] if isinstance(x, list) else [])
        
        # Advanced insights
        return {
            'skill_combinations': DataProcessor._analyze_skill_combinations(df),
            'company_insights': DataProcessor._analyze_companies(df),
            'location_analysis': DataProcessor._analyze_locations(df)
        }
    
    @staticmethod
    def _analyze_skill_combinations(df: pd.DataFrame) -> dict:
        # Analyze common skill combinations
        skill_pairs = []
        for tech_list in df['technologies']:
            if len(tech_list) > 1:
                for i in range(len(tech_list)):
                    for j in range(i+1, len(tech_list)):
                        # Convert tuple to string to use as dictionary key
                        skill_pairs.append(f"{tech_list[i]} + {tech_list[j]}")
        
        skill_pair_counts = pd.Series(skill_pairs).value_counts().head(10).to_dict()
        return {'common_pairs': skill_pair_counts}
    
    @staticmethod
    def _analyze_companies(df: pd.DataFrame) -> dict:
        return {
            'top_employers': df['company'].value_counts().head(10).to_dict(),
            'company_size_dist': df['company_size'].value_counts().to_dict() if 'company_size' in df.columns else {}
        }
    
    @staticmethod
    def _analyze_locations(df: pd.DataFrame) -> dict:
        return {
            'city_distribution': df['location'].str.split(',').str[0].value_counts().to_dict(),
            'remote_jobs': len(df[df['location'].str.contains('remote', case=False, na=False)])
        }

class LLMAnalyzer:
    def __init__(self):
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.model = os.getenv('MODEL_NAME')

    def generate_insights(self, df: pd.DataFrame) -> dict:
        insights = self._prepare_data_summary(df)
        advanced_insights = DataProcessor.extract_advanced_insights(df)
        
        prompt = f"""
        As an expert market analyst, provide a comprehensive analysis of the Indian tech job market based on this data. 
        Include detailed insights in these key areas:

        1. Market Overview & Trends:
        - Current state of the tech job market
        - Key trends in hiring patterns
        - Industry growth indicators
        - Impact of emerging technologies

        2. Geographical Analysis:
        - Deep dive into regional tech hubs
        - Remote work trends and implications
        - City-wise opportunities and specializations
        - Regional salary variations (if available)

        3. Technology Landscape:
        - Most in-demand technical skills and their significance
        - Emerging technology trends and their impact
        - Technology combinations frequently requested together
        - Skills that command premium compensation

        4. Company Analysis:
        - Types of companies hiring (startups vs enterprises)
        - Industries driving tech employment
        - Company-specific technology preferences
        - Hiring patterns and job diversity

        5. Career Opportunities & Recommendations:
        - High-growth career paths
        - Skills worth investing in
        - Industry-specific opportunities
        - Strategic career planning advice

        Base your analysis on these insights:
        {json.dumps(advanced_insights, indent=2)}

        Format your response in markdown with clear sections, bullet points, and emphasis on key findings.
        Focus on actionable insights for both job seekers and employers in India's tech industry.
        Include specific numbers and percentages where relevant.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return {
                'status': 'success',
                'insights': response.choices[0].message.content
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error generating insights: {str(e)}"
            }

    def _prepare_data_summary(self, df: pd.DataFrame) -> str:
        # Create tech_stack list from comma-separated values
        df['technologies'] = df['tech_stack'].str.split(',').apply(lambda x: [t.strip() for t in x] if isinstance(x, list) else [])
        
        stats = {
            'total_jobs': len(df),
            'unique_companies': df['company'].nunique(),
            'major_cities': df['location'].str.split(',').str[0].nunique(),
            'avg_tech_per_job': df['technologies'].apply(len).mean(),
            'top_cities': dict(df['location'].str.split(',').str[0].value_counts().head(5)),
            'top_technologies': dict(pd.Series([tech for techs in df['technologies'] for tech in techs]).value_counts().head(10))
        }
        
        return f"""
        Job Market Overview:
        - Total Job Listings: {stats['total_jobs']}
        - Unique Companies Hiring: {stats['unique_companies']}
        - Major Cities: {stats['major_cities']}
        - Average Technologies per Job: {stats['avg_tech_per_job']:.1f}

        Top Hiring Cities:
        {self._format_dict(stats['top_cities'])}

        Most In-Demand Technologies:
        {self._format_dict(stats['top_technologies'])}
        """

    def _format_dict(self, d: dict) -> str:
        return '\n'.join([f"- {k}: {v}" for k, v in d.items()])
