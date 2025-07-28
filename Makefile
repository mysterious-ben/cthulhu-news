poetry-freeze:
	poetry export --without-hashes --with=db -o db/requirements.txt
	poetry export --without-hashes --with=web -o web/requirements.txt

uv-freeze:
	uv export --no-hashes --extra db --output-file db/requirements.txt
	uv export --no-hashes --extra web --output-file web/requirements.txt