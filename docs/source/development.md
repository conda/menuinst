# Development

## Local development setup

`menuinst` is a multiplatform tool with heavy reliance on OS-specific behaviour, APIs and tools.
Each platform requires its own setup.

> Since some tests might leave traces behind, we recommend running the tests from a VM (if you can).
For your own protection, some tests only run when the `CI` env var has been set to a non-empty value. If you do want to run these on your local machine, you can set the `CI` env var to `1` before running the tests; it better be on a VM though!

## Linux

We recommend using Docker to run the tests on Linux. However, some tasks require a graphical environment.

### Docker setup

1. We can leverage `conda/conda`'s conda-forge-based CI image for this. Make sure to mount the `menuinst` source to a known location in the container. In the example below, we are using `~/my/repos/menuinst`, mapped to `/opt/menuinst-src`.

```
$ docker run -it --rm --platform=linux/aarch64 \
    -v ~/my/repos/menuinst:/opt/menuinst-src \
    ghcr.io/conda/conda-ci:main-linux-python3.10-conda-forge bash
```

2. Create a new conda environment and install the dependencies:

```
$ conda create -n menuinst-dev \
    conda-canary/label/conda-conda-pr-11882::conda \
    pip \
    pytest \
    pytest-cov \
    pydantic \
    hypothesis \
    hypothesis-jsonschema
```

3. Activate the environment and install `menuinst`:

```
$ conda activate menuinst-dev
$ python -m pip install -vv /opt/menuinst-src
```

4. Run the tests:

```
$ cd /opt/menuinst-src
$ pytest
```

### VM setup

## macOS

Some of the tests involve modifying the system's menu. While we have added some teardown logic to
undo the modifications once done, it might still leave some artifacts behind. We recommend running
the tests from a VM (if you can).

### VM setup with UTM

This is recommended for Apple Silicon.

1. Download [UTM](https://mac.getutm.app/) and create a new VM for macOS using the default
   settings. The UI only requires a couple clicks, but the download and automated install will take a few hours, so be patient.

### Debug in CI

In extreme cases, you can edit the Github Actions workflow to add a step for [`mxschmitt/action-tmate`](https://github.com/marketplace/actions/debugging-with-tmate) and then connect to the VM via SSH. Please be mindful of the resources and only add it for the platforms and Python versions you need. For example:

```yaml
- name: Setup tmate session
  uses: mxschmitt/action-tmate@v3
  timeout-minutes: 60
  if: ${{ failure() && startsWith(matrix.os, 'macos') && matrix.python-version == '3.13' }}
```

## Windows

Some tests will add changes to your system configuration (Windows registry, new files added, etc). We try to clean up after ourselves, but it's not always possible. We recommend running the tests from a VM (if you can).
