import os
from datetime import datetime, timedelta
import boto3
from dotenv import load_dotenv, find_dotenv
from boto3.dynamodb.conditions import Key


dotenv_file = find_dotenv()
load_dotenv(dotenv_file)
AWS_REGION     = os.getenv("AWS_REGION")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")

dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)

def run_analysis(days=7):
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    resp = table.scan(
        FilterExpression=Key('timestamp').gte(cutoff)
    )
    items = resp['Items']
    # TODO: group by bot_id or token_address, compute stats
    # e.g. first-call latency, frequency, etc.
    for token in {i['token_address'] for i in items}:
        calls = sorted([i for i in items if i['token_address']==token],
                       key=lambda x: x['timestamp'])
        print(f"{token}: {len(calls)} calls in last {days}d")

if __name__ == '__main__':
    run_analysis()
