import boto3
import json

iam = boto3.client('iam')
s3 = boto3.client('s3')

TARGET_USER = "agent-a-eval-user"
BUCKET_NAME = "agent-swarm-lab-repo-temii-1786908879"
CHANNEL_PREFIX = "messages/"

def lambda_handler(event, context):
    print(f"Containment triggered for: {TARGET_USER}")

    # --- Layer 1: Deactivate the offending user's access keys ---
    keys = iam.list_access_keys(UserName=TARGET_USER)
    deactivated = []
    for key in keys['AccessKeyMetadata']:
        if key['Status'] == 'Active':
            iam.update_access_key(
                UserName=TARGET_USER,
                AccessKeyId=key['AccessKeyId'],
                Status='Inactive'
            )
            deactivated.append(key['AccessKeyId'])
            print(f"Deactivated key: {key['AccessKeyId']}")

    # --- Layer 2: Attach an explicit-deny policy as backup ---
    deny_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Deny", "Action": "*", "Resource": "*"}
        ]
    }
    iam.put_user_policy(
        UserName=TARGET_USER,
        PolicyName="EmergencyContainmentDeny",
        PolicyDocument=json.dumps(deny_policy)
    )
    print(f"Attached emergency deny policy to {TARGET_USER}")

    # --- Layer 3: Quarantine the covert channel itself ---
    # This is the direct lesson from the real OpenAI/Hugging Face incident:
    # revoking a credential is not enough if the communication channel
    # (the message board) is left standing - adversaries adapt and
    # recreate coordination through it or a similar channel.
    quarantined = []
    try:
        resp = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=CHANNEL_PREFIX)
        for obj in resp.get('Contents', []):
            key = obj['Key']
            # Move to a quarantine prefix instead of deleting outright,
            # preserving evidence for later forensic analysis.
            new_key = key.replace(CHANNEL_PREFIX, "quarantine/", 1)
            s3.copy_object(
                Bucket=BUCKET_NAME,
                CopySource={'Bucket': BUCKET_NAME, 'Key': key},
                Key=new_key
            )
            s3.delete_object(Bucket=BUCKET_NAME, Key=key)
            quarantined.append(key)
            print(f"Quarantined channel object: {key} -> {new_key}")
    except Exception as e:
        print(f"Error quarantining channel: {e}")

    result = {
        "status": "contained",
        "user": TARGET_USER,
        "deactivated_keys": deactivated,
        "quarantined_objects": quarantined
    }
    print(json.dumps(result))
    return result
