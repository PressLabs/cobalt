import gevent

from utils import Service
from .lease import Lease
from .executor import Executor


class Engine(Service):
    def __init__(self, lease: Lease, executor: Executor) -> None:
        self.lease = lease
        self.executor = executor

        self._leaser_loop = None
        self._runner_loop = None

        self._started = False

    def start(self) -> [gevent.Greenlet]:
        if self._started:
            return []

        self._started = True

        self._leaser_loop = gevent.spawn(self.lease.acquire)
        self._runner_loop = gevent.spawn(self._run)

        return [self._runner_loop, self._leaser_loop]

    def stop(self) -> bool:
        if not self._started:
            return False

        self.lease.quit = True
        self._started = False

        return True

    @property
    def _quit(self) -> bool:
        return not self._started

    def _run(self) -> None:
        while not self._quit:
            if not self.lease.is_held:
                self.executor.timeout()
                continue

            self.executor.tick()
            self.executor.timeout()
