import asyncio
import random
from collections.abc import Callable
from dataclasses import dataclass, field

from pipeline import PipelineBuilder, PipelineCtx
from pipeline.aio import AsyncPipelineBuilder


@dataclass(slots=True)
class MainCtx(PipelineCtx):
    value: int = field(default=0, init=False)


def print_hello(ctx: MainCtx) -> None:
    print("Hello from auth-service!")


def increment(ctx: MainCtx) -> None:
    cache = ctx.value
    ctx.value += 1

    def rollback(ctx: MainCtx) -> None:
        ctx.value = cache

    return rollback


def decrement(ctx: MainCtx) -> None:
    cache = ctx.value
    ctx.value -= 1

    def rollback(ctx: MainCtx) -> None:
        ctx.value = cache

    return rollback


def set_value(value: int) -> Callable[[MainCtx], None]:
    def factory(ctx: MainCtx) -> None:
        cache = ctx.value
        ctx.value = value

        def rollback(ctx: MainCtx) -> None:
            ctx.value = cache

        return rollback

    return factory


def print_value(ctx: MainCtx) -> None:
    print(ctx.value)


def sleep(seconds: int) -> Callable[[MainCtx], None]:
    async def factory(ctx: MainCtx) -> None:
        await asyncio.sleep(seconds)
        print(f"Sleeping for {seconds} seconds")

    return factory


async def main():
    pipe = AsyncPipelineBuilder.from_factories(
        lambda b: b.do(print_hello),
        lambda b: b.lock(asyncio.Lock()),
        lambda b: b.unlock(defer=True),
        lambda b: b.do(increment),
        lambda b: b.do(print_value),
        lambda b: b.do(decrement),
        lambda b: b.do(print_value),
        lambda b: b.do(set_value(random.randint(0, 10))),
        lambda b: b.do(
            PipelineBuilder()
            .do(print_value, defer=True)
            .do_while(
                lambda ctx: ctx.value < 10,
                body=PipelineBuilder().do(print_value).do(increment).build(),
            )
            .build()
        ),
        lambda b: b.do_gather(
            [sleep(1), sleep(2), sleep(3), sleep(1), sleep(2), sleep(3)]
        ),
        lambda b: b.do_if(
            lambda ctx: ctx.value > 5,
            true=increment,
            false=decrement,
        ),
        lambda b: b.do(print_value),
    ).build()
    await pipe(MainCtx())


if __name__ == "__main__":
    asyncio.run(main())
