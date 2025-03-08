import uvicorn

if __name__ == "__main__":
    print("Starting Superego LangGraph API on http://0.0.0.0:8000")
    # Start the server
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
