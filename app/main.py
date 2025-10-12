from app.create_app import create_app


def main():
    app = create_app()
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
