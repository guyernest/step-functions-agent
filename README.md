










## uv Set up

### For MacOS with Apple silicon

```shell
uv python install cpython-3.12.3-macos-aarch64-none
uv venv --python cpython-3.12.3-macos-aarch64-none 
source .venv/bin/activate 
uv pip compile requirements.in --output-file requirements.txt 
uv pip sync requirements.txt
```