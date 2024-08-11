import json
import boto3
import os
from datetime import datetime
from kafka import KafkaConsumer


def calculate_population_density(population, area):
    return population / area if area > 0 else 0


def is_large_country(area):
    return area > 1000000


def lambda_handler(event, context):
    kafka_brokers = os.environ['KAFKA_BROKERS'].split(',')
    topic = 'countries_data'

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=kafka_brokers,
        group_id='country-data-consumer-group',
        auto_offset_reset='earliest',  # Start from the earliest message if no offset is stored
        enable_auto_commit=True,  # Automatically commit offsets
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    processed_data = []
    for message in consumer:
        country_data = message.value
        area = country_data.get('area', 0)
        population = country_data.get('population', 0)
        processed_country = {
            'name': country_data['name']['common'],
            'capital': country_data['capital'][0] if country_data.get('capital') else 'N/A',
            'population': population,
            'area': area,
            'region': country_data['region'],
            'subregion': country_data.get('subregion', 'N/A'),
            'languages': list(country_data.get('languages', {}).values()),
            'currencies': list(country_data.get('currencies', {}).keys()),
            'flag_url': country_data['flags']['png'],
            'population_density': calculate_population_density(population, area),
            'is_large_country': is_large_country(area)
        }
        processed_data.append(processed_country)

        if len(processed_data) >= 10:  # Process up to 10 messages per invocation
            break

    if processed_data:
        json_data = '\n'.join(json.dumps(country) for country in processed_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"countries_data_{timestamp}.json"

        s3 = boto3.client('s3')
        bucket_name = os.environ['S3_BUCKET']
        try:
            s3.put_object(Bucket=bucket_name, Key=filename, Body=json_data)
            print(f"Successfully uploaded {filename} to S3")
        except Exception as e:
            print(f"Error uploading to S3: {str(e)}")
    else:
        print("No new data to process")

    consumer.close()

    return {
        'statusCode': 200,
        'body': json.dumps(f"Processed {len(processed_data)} countries and uploaded to S3")
    }