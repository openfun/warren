<div class="hero" markdown="1">
    [![Warren logo](./img/warren-color-light.png)](/ "Warren")

    _📊 A framework for your learning analytics (expect some xAPI ❤️)_

    [![CircleCI tests](https://img.shields.io/circleci/build/gh/openfun/warren/main?label=Tests&logo=circleci)](https://circleci.com/gh/openfun/warren/tree/main)
    [![PyPi version](https://img.shields.io/pypi/v/warren?label=PyPi+package&logo=PyPI)](https://pypi.org/project/warren)
    [![Python versions](https://img.shields.io/pypi/pyversions/warren?label=Python&logo=Python)](https://pypi.org/project/warren)
    [![Docker image versions](https://img.shields.io/docker/v/fundocker/warren/api-core-main?label=API+Docker+image&logo=Docker)](https://hub.docker.com/r/fundocker/warren/tags)
    [![Docker image versions](https://img.shields.io/docker/v/fundocker/warren/app-main?label=Django+Docker+image&logo=Docker)](https://hub.docker.com/r/fundocker/warren/tags)

</div>

[Warren](/) is a framework for your learning analytics. Its key features are:

1. a simple Python interface to define indicators,
2. cacheable indicators calculation,
3. pluggable execution engines,
4. calculated indicators exposed _via_ an HTTP API,
5. [LRS](https://en.wikipedia.org/wiki/Learning_Record_Store) as a primary data source,
6. high extensibility thanks to a plugin-architecture,
7. [LTI](https://en.wikipedia.org/wiki/Learning_Tools_Interoperability) dashboards integration.

Warren also provides:

1. a light-weight implementation of ADLNet's [Experience Index](https://github.com/adlnet/xi-lite) (_aka_ XI), a core-component of the recommended [Total Learning Architecture](https://adlnet.gov/news/2020/01/20/ADL-Initiative-established-a-TLA-Sandbox-project/),
2. extensible indexers for popular LMSes (Moodle, OpenEdx) to feed the XI.

And finally, Warren also provides **web component** to build reactive, beautiful dashboards :heart_eyes:.

![Video dashboard example](./img/dashboard-video-screen.png)
