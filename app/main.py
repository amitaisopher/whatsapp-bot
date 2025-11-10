from app.create_app import create_app


def main():
    app = create_app()
    import uvloop
    import uvicorn
    import asyncio

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
