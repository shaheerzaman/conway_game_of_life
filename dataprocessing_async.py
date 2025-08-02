from abc import abstractmethod, ABC
import asyncio
from typing import AsyncGenerator, Any
import random
from collections import deque


class Source(ABC):
    @abstractmethod
    async def stream(self) -> AsyncGenerator[dict]:
        raise NotImplementedError


class Processor(ABC):
    @abstractmethod
    async def process(self, data_chunk: Any) -> dict:
        raise NotImplementedError


class Sink(ABC):
    @abstractmethod
    async def write(self, processed_chunk: Any) -> None:
        raise NotImplementedError


class MockSensorSource(Source):
    async def stream(self) -> AsyncGenerator[dict]:
        for i in range(5):
            await asyncio.sleep(random.uniform(0.1, 0.5))
            yield {"sensor_id": "temp_a", "value": 20}


class MovingAverageProcessor(Processor):
    def __init__(self, window_size: int = 3):
        self.window = deque(maxlen=window_size)

    async def process(self, data_chunk: dict) -> dict:
        self.window.append(data_chunk["value"])
        moving_avg = sum(self.window) / len(self.window)

        await asyncio.sleep(0.1)

        data_chunk["moving_average"] = f"{moving_avg:.2f}"
        return data_chunk


class ConsoleSink(Sink):
    async def write(self, processed_chunk: dict) -> None:
        print(f"sink {processed_chunk}")
        await asyncio.sleep(0.05)


class Pipeline:
    def __init__(self, source: Source, processor: Processor, sink: ConsoleSink) -> None:
        self.source = source
        self.processor = processor
        self.sink = sink

    async def run(self):
        print("starting pipeline")
        async for data_chunk in self.source.stream():
            processed_chunk = await self.processor.process(data_chunk)
            await self.sink.write(processed_chunk)

        print("pipeline finished")


async def main():
    pipeline = Pipeline(
        source=MockSensorSource(), processor=MovingAverageProcessor(), sink=ConsoleSink
    )
    await pipeline.run()


if __name__ == "__main__":
    asyncio.run(main())
