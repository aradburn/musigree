import uvicorn

if __name__ == "__main__":
    # Run the application using uvicorn
    # For running behind a proxy, use the --root-path parameter as needed
    uvicorn.run("musigree.app.fastapi_prod_app:app", host="0.0.0.0", port=8080, workers=1, access_log=False, log_level="debug")
