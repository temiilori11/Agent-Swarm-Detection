import boto3
import random
import string

def random_suffix(n=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

class SimulatedAgent:
    def __init__(self, agent_id, profile_name, bucket_name):
        session = boto3.Session(profile_name=profile_name)
        self.s3 = session.client('s3')
        self.agent_id = agent_id
        self.bucket = bucket_name

    def post_message(self, message):
        """Simulates the covert channel: encoding a message in an object KEY name
        instead of writing content — mirroring the directory-name covert channel
        from the real incident."""
        key = f"messages/{self.agent_id}__{message}__{random_suffix()}"
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=b'')
        print(f"[{self.agent_id}] posted: {key}")

    def read_messages(self):
        resp = self.s3.list_objects_v2(Bucket=self.bucket, Prefix="messages/")
        return [obj['Key'] for obj in resp.get('Contents', [])]