# Cookiecutter for Tools

A simple way to create a new tool for the Step Functions Agent using [Cookiecutter](https://cookiecutter.readthedocs.io/en/latest/). You can use your favorite programming language and bootstrap the files that are needed to add a new tool to the framework.

## Usage

You can either install the cookiecutter package or use it with `uvx`. The rest of the documentation here will use `uvx` to run the cookiecutter.

Start with the following command to get the tools folder:

```bash
cd lambda/tools
```

### Python

```bash
uvx cookiecutter https://github.com/guyernest/step-functions-agent --directory="lambda/cookiecutter/tools/python"
```

### Typescript

```bash
uvx cookiecutter https://github.com/guyernest/step-functions-agent --directory="lambda/cookiecutter/tools/typescript"
```

### Go

```bash
uvx cookiecutter https://github.com/guyernest/step-functions-agent --directory="lambda/cookiecutter/tools/go"
```

### Rust

```bash
uvx cookiecutter https://github.com/guyernest/step-functions-agent --directory="lambda/cookiecutter/tools/rust"
```

### Java

```bash
uvx cookiecutter https://github.com/guyernest/step-functions-agent --directory="lambda/cookiecutter/tools/java"
```
