

For testing use any of the following:

```bash
uv run python app.py # user will default to the guest user 

uv run jupyter notebook --ip=0.0.0.0 --no-browser --allow-root


cd vue-project
bun install
bun run dev --port 8888 --host 0.0.0.0
```