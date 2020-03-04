serve:
	python3 -m aiohttp.web -H 0.0.0.0 -P 8080 app:make_app
