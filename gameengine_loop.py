from abc import abstractmethod, ABC
import time
from typing import List
from __future__ import annotations


# core behavioral contracts
class Updatable(ABC):
    @abstractmethod
    def update(self, delta_time: float) -> None:
        raise NotImplementedError


class Renderable(ABC):
    @abstractmethod
    def render(self, surface: Screen) -> None:
        raise NotImplementedError


class EventHandler(ABC):
    @abstractmethod
    def handle_event(self, event: str) -> None:
        raise NotImplementedError


class Screen:
    def draw(self, obj_repr: str, x: int, y: int):
        print(f"SCREEN: Drawing '{obj_repr}' at ({x}, {y})")


class Player(Updatable, Renderable, EventHandler):
    def __init__(self):
        self.x = 10
        self.y = 5
        self.vx, self.vy = 0, 0

    def update(self, delta_time: float) -> None:
        self.x += self.vx * delta_time
        self.vy += self.vy * delta_time

    def render(self, surface: Screen) -> None:
        surface.draw("👨", round(self.x), round(self.y))

    def handle_event(self, event: str) -> None:
        if event == "KEY_UP":
            self.vy = -10
        elif event == "KEY_DOWN":
            self.vy = 10
        elif event == "KEY_LEFT":
            self.vx = -10
        elif event == "KEY_RIGHT":
            self.vx = 10


class Cloud(Renderable):
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def render(self, surface: Screen) -> None:
        surface.draw("☁️", self.x, self.y)


class ProximityMine(Updatable, EventHandler):
    def __init__(self, trigger_x: int):
        self.trigger_x = trigger_x
        self.armed = True

    def update(self, delta_time: float) -> None:
        pass

    def handle_event(self, event: str) -> None:
        if self.armed and event.startswith("PLAYER_MOVED_TO"):
            player_x = int(event.split(":")[1])
            if abs(player_x - self.trigger_x) < 2:
                print("boom")
                self.armed = False


# engine main loop
class GameLoop:
    def __init__(self):
        self.all_objects = []
        self.updatables: list[Updatable] = []
        self.renderables: list[Renderable] = []
        self.event_handlers: list[EventHandler] = []
        self.screen = Screen()

    def regsiter(self, obj: object):
        self.all_objects.append(obj)
        if isinstance(obj, Updatable):
            self.updatables.append(obj)
        if isinstance(obj, Renderable):
            self.renderables.append(obj)
        if isinstance(obj, EventHandler):
            self.event_handlers.append(obj)

    def run(self):
        last_time = time.time()
        mock_events = ["KEY_RIGHT", "KEY_RIGHT", "NO_EVENT", "KEY_UP"]

        for i in range(4):
            current_time = time.time()
            delta_time = current_time - last_time
            last_time = current_time

            if mock_events:
                event = mock_events.pop(0)
                if event != "NO_EVENT":
                    for handler in self.event_handlers:
                        handler.handle_event(event)

            for updatable in self.updatables:
                updatable.update(delta_time)

            player = next((obj for obj in self.all_objects if isinstance(Player)), None)
            if player:
                for handler in self.event_handlers:
                    handler.handle_event(f"PLAYER_MOVED_TO:{round(player.x)}")

            for renderable in self.renderables:
                renderable.render(self.screen)

            time.sleep(0.5)


engine = GameLoop()
engine.register(Player())
engine.register(Cloud(x=20, y=3))
engine.register(ProximityMine(trigger_x=13))
engine.run()
