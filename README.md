# LyraAI

LyraAI is a lightweight chatbot to interact with local content(RAG). The model service can be any OpenAI-compatible service(eg. [instructlab](https://github.com/instructlab/instructlab), [ollama](https://github.com/ollama/ollama/tree/main)).

## Installation

### LyraAI installation
```
$ python3 -m venv LyraAI_venv  
$ source LyraAI_venv/bin/activate
$ pip install openai
$ pip install gradio
$ pip install chromadb
```

### Local model service quick installation

We are using [instructlab](https://github.com/instructlab/instructlab) in the example:
```
$ sudo dnf install gcc gcc-c++ make git python3.11 python3.11-devel
$ mkdir instructlab
$ cd instructlab
$ python3 -m venv --upgrade-deps venv
$ source venv/bin/activate
$ pip cache remove llama_cpp_python
$ pip install instructlab \
    --extra-index-url=https://download.pytorch.org/whl/cpu \
    -C cmake.args="-DLLAMA_NATIVE=off"
$ ilab config init
$ ilab model download
```

## Run it

We are using instructlab as backend model service in the example:
```
$ ilab model serve
$ python load_data.py (only required when you have new local data)
$ python chat_front.py
```

Now, you have your chatbot available at http://xx.xx.xx.xx:7860.