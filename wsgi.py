import uvicorn

from musigree.app.fastapi_prod_app import app

if __name__ == "__main__":
    # Run the application using uvicorn
    # For running behind a proxy, use the --root-path parameter as needed
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=4)
