"""Base Agent class for all supply chain agents"""
import boto3
import json
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime

class BaseAgent(ABC):
    """Base class for all agents in the supply chain system"""
    
    def __init__(self, agent_name: str, persona: str, region: str = "us-east-1"):
        self.agent_name = agent_name
        self.persona = persona
        self.region = region
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return the tools available to this agent"""
        pass
    
    @abstractmethod
    def process_query(self, query: str, session_id: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process a user query and return response"""
        pass
    
    def save_session_state(self, session_id: str, state: Dict[str, Any]):
        """Save session state to DynamoDB"""
        from config import DYNAMODB_SESSION_TABLE
        table = self.dynamodb.Table(DYNAMODB_SESSION_TABLE)
        table.put_item(
            Item={
                'session_id': session_id,
                'persona': self.persona,
                'agent_name': self.agent_name,
                'state': json.dumps(state),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def load_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session state from DynamoDB"""
        from config import DYNAMODB_SESSION_TABLE
        table = self.dynamodb.Table(DYNAMODB_SESSION_TABLE)
        response = table.get_item(Key={'session_id': session_id})
        if 'Item' in response:
            return json.loads(response['Item']['state'])
        return None
    
    def invoke_bedrock_model(self, prompt: str, system_prompt: str = "") -> str:
        """Invoke Bedrock Claude model"""
        from config import BEDROCK_MODEL_ID
        
        messages = [{"role": "user", "content": prompt}]
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": messages,
            "temperature": 0.0
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        response = self.bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
