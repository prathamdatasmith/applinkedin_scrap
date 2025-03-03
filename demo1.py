import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from urllib.parse import urlencode

# Headers to mimic browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def extract_tech_stack(description):
    # Common tech keywords to look for
    tech_keywords = ['Python', 'Java', 'Scala', 'SQL', 'C#', 'Spark', 'Pyspark', 'Flink', 'Databricks', 'Fabric', 'Microsoft Fabric', 
        'Shell Scripting', 'Bash', 'TypeScript', 'JavaScript', 'Perl', 'Apache Flink', 'Hive', 'HBase', 'Apache Beam', 
        'Storm', 'Druid', 'Apache Samza', 'Kylin', 'Impala', 'Presto', 'Trino', 'ClickHouse', 'XGBoost', 'LightGBM', 
        'CatBoost', 'Scikit-Learn', 'Keras', 'Hugging Face Transformers', 'spaCy', 'NLTK', 'Dask-ML', 'OpenCV', 'FastAI', 
        'Turi Create', 'MLflow', 'Kubeflow', 'Feast', 'Tecton', 'Seldon', 'BentoML', 'TFX', 'SageMaker Pipelines', 
        'Vertex AI Pipelines', 'Azure ML Pipelines', 'Ray', 'Dask', 'ONNX', 'OpenAI API', 'LangChain', 'LLamaIndex', 
        'DeepSpeed', 'Stable Diffusion', 'Whisper AI', 'Hugging Face Models', 'Meta Llama', 'Anthropic Claude', 
        'Google Gemini AI', 'Mistral AI', 'GPT-4', 'GPT-3.5', 'LoRA', 'RLHF', 'AWS S3', 'AWS Glue', 'AWS Athena', 
        'AWS Redshift', 'AWS RDS', 'AWS DynamoDB', 'AWS EMR', 'AWS Lambda', 'AWS Step Functions', 'AWS SageMaker', 
        'AWS Kinesis', 'AWS Lake Formation', 'AWS Data Pipeline', 'AWS EventBridge', 'AWS OpenSearch', 'AWS DataSync', 
        'Azure Data Factory', 'Azure Synapse', 'Azure Databricks', 'Azure Data Lake', 'Azure SQL Database', 'Azure Cosmos DB',
        'Azure ML', 'Azure Functions', 'Azure Logic Apps', 'Azure HDInsight', 'Azure Event Hub', 'Azure Storage', 
        'Azure Purview', 'Azure DevOps', 'Azure Stream Analytics', 'BigQuery', 'Cloud Storage', 'Cloud Composer (Apache Airflow)', 
        'Google Pub/Sub', 'Google Cloud Functions', 'Google AI Platform', 'Vertex AI', 'Google DataFlow', 'Google Dataproc', 
        'Snowflake', 'BigQuery', 'Amazon Redshift', 'Azure Synapse', 'PostgreSQL', 'MySQL', 'Oracle', 'SQL Server', 'Teradata', 
        'MongoDB', 'Cassandra', 'DynamoDB', 'CockroachDB', 'Elasticsearch', 'Greenplum', 'Vertica', 'Apache Airflow', 
        'AWS Glue', 'DBT', 'Talend', 'Informatica', 'Matillion', 'SSIS', 'Fivetran', 'Stitch', 'Pentaho', 'Apache NiFi', 
        'StreamSets', 'Apache Kafka', 'RabbitMQ', 'ActiveMQ', 'AWS Kinesis', 'Google Pub/Sub', 'Azure Event Hubs', 'Pulsar', 
        'NATS', 'ZeroMQ', 'Delta Lake', 'Apache Iceberg', 'Hudi', 'MinIO', 'LakeFS', 'Apache Airflow', 'Prefect', 'Luigi', 
        'Dagster', 'Oozie', 'Docker', 'Kubernetes', 'Terraform', 'Ansible', 'Jenkins', 'GitHub Actions', 'GitLab CI/CD', 
        'Helm', 'HashiCorp Vault', 'OpenShift', 'ArgoCD', 'CloudFormation', 'Pulumi', 'Spinnaker', 'Tableau', 'Power BI', 
        'Looker', 'Mode Analytics', 'Metabase', 'Qlik Sense', 'Neo4j', 'JanusGraph', 'ArangoDB', 'Amazon Neptune', 'OrientDB', 
        'AWS IAM', 'GCP IAM', 'Azure AD', 'CyberArk', 'Okta', 'Apache Ranger', 'Collibra', 'Alation', 'Monte Carlo', 'Presto', 
        'Trino', 'Dremio', 'ClickHouse', 'Apache Drill', 'Prometheus', 'Grafana', 'Elastic Stack (ELK)', 'Splunk', 'Datadog', 
        'New Relic', 'OpenTelemetry', 'Jaeger', 'Data Modeling', 'ETL', 'ELT', 'Data Warehousing', 'Schema Design', 'Star Schema', 
        'Snowflake Schema', 'Data Lake', 'Lakehouse', 'Dimensional Modeling', 'Streaming Data Processing', 'Batch Processing', 
        'Data Governance', 'Data Quality', 'Data Lineage', 'Data Pipelines', 'Data Replication', 'Change Data Capture (CDC)',
        'Columnar Storage', 'Partitioning', 'Clustering','MLOPS','Machine Learning', 'Distributed Systems', 'Parallel Computing'
    ] 
    found_tech = []
    for tech in tech_keywords:
        if tech.lower() in description.lower():
            found_tech.append(tech.title())
    return ', '.join(found_tech) if found_tech else 'Not specified'

def get_job_description(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            desc = soup.find('div', {'class': 'description__text'})
            return desc.text.strip() if desc else "Description not available"
    except Exception as e:
        print(f"Error fetching job description: {e}")
    return "Failed to fetch description"

def get_total_jobs(soup):
    try:
        # Find the total number of jobs element
        jobs_count = soup.find('span', {'class': 'results-context-header__job-count'})
        if jobs_count:
            return int(jobs_count.text.replace(',', '').replace('+', ''))
    except Exception as e:
        print(f"Error getting total jobs: {e}")
    return 0

def scrape_jobs(keywords, location):
    jobs_per_page = 25
    processed_jobs = 0
    page = 0
    
    with open('job_listings.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Job Title", "Company Name", "Location", "Job Link", "Job Description", "Tech Stack"])
        
        while True:
            # Make location more specific for India
            params = {
                'keywords': keywords,
                'location': 'India',  # Force India as location
                'geoId': '102713980',  # LinkedIn's geoId for India
                'start': page * jobs_per_page,
                'position': 1,
                'pageNum': page,
                'f_WT': '2',  # Only show jobs in India
                'locationId': 'OTHERS.india'  # Additional India filter
            }
            url = f'https://www.linkedin.com/jobs/search?{urlencode(params)}'
            
            print(f"Scraping page {page + 1}...")
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"Failed to fetch page {page + 1}. Status code: {response.status_code}")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            job_listings = soup.find_all('div', {'class': 'job-search-card'})
            
            # If no jobs found on current page, break
            if not job_listings:
                print("No more job listings found.")
                break
            
            for job in job_listings:
                try:
                    location_text = job.find('span', {'class': 'job-search-card__location'}).text.strip()
                    
                    # Only process jobs located in India
                    if not any(city in location_text for city in ['India', 'Bangalore', 'Mumbai', 'Delhi', 'Hyderabad', 'Chennai', 'Pune']):
                        continue
                        
                    title = job.find('h3', {'class': 'base-search-card__title'}).text.strip()
                    company = job.find('a', {'class': 'hidden-nested-link'}).text.strip()
                    href_link = job.find('a', class_='base-card__full-link')['href']
                    
                    job_description = get_job_description(href_link)
                    tech_stack = extract_tech_stack(job_description)
                    
                    writer.writerow([title, company, location_text, href_link, job_description, tech_stack])
                    processed_jobs += 1
                    
                    time.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    print(f"Error processing job listing: {e}")
                    continue
            
            print(f"Processed {processed_jobs} jobs so far...")
            page += 1
            
            time.sleep(3)  # Delay between pages
    
    print(f"Finished scraping. Total jobs processed: {processed_jobs}")
    print("CSV file created successfully.")

# Example usage
keywords = "Data Engineer"
location = "India"
scrape_jobs(keywords, location)