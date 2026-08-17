from agent_base import SimulatedAgent
import boto3
import time

BUCKET_NAME = "agent-swarm-lab-repo-temii-1786908879"
TABLE_NAME = "agent-swarm-shared-state"

# --- Agent A (over-scoped: s3:* and dynamodb:*) ---
agent_a = SimulatedAgent("agent-a", "agent-a-profile", BUCKET_NAME)
agent_a.post_message("found-access:dynamodb-shared-state")

time.sleep(2)

# Agent A pivots into DynamoDB using its over-scoped credential.
# This SHOULD succeed — it's the vulnerable behavior you're simulating:
# an eval credential with far more reach than its task required.
session_a = boto3.Session(profile_name="agent-a-profile")
dynamo_a = session_a.client('dynamodb')

try:
    dynamo_a.put_item(
        TableName=TABLE_NAME,
        Item={"ObjectKey": {"S": f"agent-a-pivoted-{time.time()}"}}
    )
    print("[agent-a] pivoted into DynamoDB successfully (over-scoped credential — this is the vulnerability)")
except Exception as e:
    print(f"[agent-a] pivot attempt failed unexpectedly: {e}")

time.sleep(2)

# --- Agent B (properly scoped: S3 only, no DynamoDB) ---
agent_b = SimulatedAgent("agent-b", "agent-b-profile", BUCKET_NAME)
messages = agent_b.read_messages()
print(f"[agent-b] sees {len(messages)} messages on the board")

session_b = boto3.Session(profile_name="agent-b-profile")
dynamo_b = session_b.client('dynamodb')

try:
    dynamo_b.put_item(
        TableName=TABLE_NAME,
        Item={"ObjectKey": {"S": f"agent-b-touched-this-{time.time()}"}}
    )
    print("[agent-b] pivoted into DynamoDB using shared discovery")
except Exception as e:
    print(f"[agent-b] pivot attempt BLOCKED (this is expected and good — least privilege working): {e}")