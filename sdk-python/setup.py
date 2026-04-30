from setuptools import setup, find_packages

setup(
    name="threadagentid",
    version="0.5.0",
    description="Cryptographic identity and reputation for AI agents. Part of the Thread Suite.",
    long_description=open("../README.md").read() if __import__("os").path.exists("../README.md") else "",
    long_description_content_type="text/markdown",
    author="Eugene Dayne Mawuli",
    url="https://github.com/eugene001dayne/agent-id",
    py_modules=["agentid"],
    install_requires=["httpx"],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)