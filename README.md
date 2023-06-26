# Warren

Warren is a visualization platform for learning analytics.

⚠️ This project is a Proof Of Concept not suitable for production yet. ⚠️


## Quick start guide (for developers)

Once you've cloned the project, it can be bootstrapped using the eponym GNU
Make target:

```
$ make bootstrap
```

Once frontend and API backend Docker images have been built, you can start the
API backend and frontend development servers using:

```
$ make run
```

You may now take a look at the frontend development server at:
[http://localhost:3000](http://localhost:3000)

To run tests and linters, there are commands for that! You can list them using:

```
$ make help
```


## Contributing

This project is intended to be community-driven, so please, do not hesitate to
get in touch if you have any question related to our implementation or design
decisions.

We try to raise our code quality standards and expect contributors to follow
the recommandations from our
[handbook](https://handbook.openfun.fr).

You can ensure your code is compliant by running the following commands:

- `make lint` to run the linters
- `make test` to run the tests

Note that we also provide a git pre-commit hook to ease your life:
```
make git-hook-pre-commit
```

## License

This work is released under the MIT License (see [LICENSE](./LICENSE.md)).
