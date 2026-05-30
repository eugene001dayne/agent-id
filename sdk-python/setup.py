from setuptools import setup

setup(
    name="threadagentid",
    version="0.6.0",
    description="Cryptographic identity and reputation for AI agents. Part of the Thread Suite.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Eugene Dayne Mawuli",
    author_email="bitelance.team@gmail.com",
    url="https://github.com/eugene001dayne/agent-id",
    py_modules=["agentid"],
    install_requires=["httpx"],
    python_requires=">=3.8",
    keywords=[
        "ai", "agents", "identity", "reputation", "trust",
        "cryptography", "multi-agent", "thread-suite",
        "agent-identity", "zero-trust", "credential"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ],
)