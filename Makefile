poetry-freeze:
	poetry export --without-hashes --with=db -o db/requirements.txt
	poetry export --without-hashes --with=web -o web/requirements.txt