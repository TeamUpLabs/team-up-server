from typing import List, Dict
import asyncio

class ProjectSSEManager:
    def __init__(self):
        self.connections: Dict[str, List[asyncio.Queue]] = {}
        
    def convert_to_dict(self, obj):
        if hasattr(obj, '__dict__'):
            return {
                key: self.convert_to_dict(value)
                for key, value in obj.__dict__.items()
                if not key.startswith('_')
            }
        elif isinstance(obj, (list, tuple)):
            return [self.convert_to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self.convert_to_dict(value) for key, value in obj.items()}
        else:
            return obj

    async def connect(self, project_id: str):
        queue = asyncio.Queue()
        self.connections.setdefault(project_id, []).append(queue)
        return queue

    async def disconnect(self, project_id: str, queue: asyncio.Queue):
        self.connections[project_id].remove(queue)
        if not self.connections[project_id]:
            del self.connections[project_id]

    async def send_event(self, project_id: str, data: str):
        for queue in self.connections.get(project_id, []):
            await queue.put(data)

    async def event_generator(self, project_id: str, queue: asyncio.Queue):
        try:
            while True:
                data = await queue.get()
                yield f"data: {self.convert_to_dict(data)}\n\n"
        except asyncio.CancelledError:
            await self.disconnect(project_id, queue)
            
project_sse_manager = ProjectSSEManager()