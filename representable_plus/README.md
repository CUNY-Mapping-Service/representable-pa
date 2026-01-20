Make sure you in the docker container `docker compose exec app-plus /bin/bash`

For testing use any of the following:

```bash
uv run python app.py # user will default to the guest user 

# visit http://127.0.0.1:8001/api/ for the api
# visit http://127.0.0.1:8001/ for the built vue app


cd vue-project
bun install
bun run dev --port 8888 --host 0.0.0.0
```

### Populate the database

```bash

uv run jupyter notebook --ip=0.0.0.0 --no-browser --allow-root
# open populate_db.ipynb

```


### Tips

- `chmod -R 777 /app`