import urllib.request

# Called by docker to check the health of the container
urllib.request.urlopen("http://localhost:5000/health")
