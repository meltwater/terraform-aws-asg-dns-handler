# Contributing

When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the owners of this repository before making a change.

Please note we have a [code of conduct](CODE_OF_CONDUCT.md) that we ask you to follow in all your interactions with the project.

**IMPORTANT: Please do not create a Pull Request without creating an issue first.**

*Any change needs to be discussed before proceeding. Failure to do so may result in the rejection of the pull request.*

Thank you for your pull request. Please provide a description above and review
the requirements below.

## Pull Request Process

0. Check out [Pull Request Checklist](#pull-request-checklist), ensure you have fulfilled each step.
1. Check out guidelines below, the project tries to follow these, ensure you have fulfilled them as much as possible.
    * [Effective Go](https://golang.org/doc/effective_go.html)
    * [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)
2. Please ensure the [README](README.md) and [DOCS](./DOCS.md) are up-to-date with details of changes to the command-line interface,
    this includes new environment variables, exposed ports, used file locations, and container parameters.
3. **PLEASE ENSURE YOU DO NOT INTRODUCE BREAKING CHANGES.**
4. **PLEASE ENSURE BUG FIXES AND NEW FEATURES INCLUDE TESTS.**
5. Pull requests will be reviewd and merged by the maintainer/code owner.

## Pull Request Checklist

- [x] Read the **CONTRIBUTING** document. (It's checked since you are already here.)
- [ ] Read the [**CODE OF CONDUCT**](CODE_OF_CONDUCT.md) document.
- [ ] Add offline Lambda regression tests under `tests/` for handler changes.
- [ ] Ensure your code follows the code style of this project.
- [ ] Ensure CI and all other PR checks are green OR
    - [ ] Code compiles correctly.
    - [ ] Created tests which fail without the change (if possible).
    - [ ] All new and existing tests passed.
- [ ] Improve and update the [README](README.md) (if necessary).

## Local validation

Use Python 3.14, matching the Lambda runtime, and install the pinned development
dependencies in a virtual environment:

```sh
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate -no-color
```

Run `python -m ruff check --fix .` and `python -m ruff format .` to fix Python
style issues; use `terraform fmt -recursive` to format Terraform files.

The unit tests use botocore Stubber with dummy credentials, block socket
connections, and require no AWS credentials or resources. They cover atomic
A/TXT ownership writes, stale/retried DELETE events (including reused IPs),
legacy records protected by live instances, exact record matching, pagination,
and lifecycle completion/error handling. Pytest enforces at least 95% coverage
with branch measurement enabled.

The Validation GitHub Actions workflow runs these checks for pushes and pull
requests. Terraform initialization downloads providers with backend access
disabled; validation checks the root shared module without planning or applying.
Recursive formatting also checks the examples.

The legacy Go tests under `terratest/` **apply and destroy AWS infrastructure**.
They are excluded from this workflow and the local checks above. Run them only
as a separately authorized integration test in a suitable AWS environment.


## Release Process

*Only concerns maintainers/code owners*

0. **PLEASE DO NOT INTRODUCE BREAKING CHANGES**
1. Update `README.md`with the latest changes.
2. Increase the version numbers in any examples files and the README.md to the new version that this
   the release would represent. The versioning scheme we use is [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/meltwater/terraform-aws-asg-dns-handler/tags).
3. Ensure [CHANGELOG](CHANGELOG.md) is up-to-date with new version changes.
4. Update version references.



## Response Times

**Please note the below timeframes are response windows we strive to meet. Please understand we may not always be able to respond in the exact timeframes outlined below**
- New issues will be reviewed and acknowledged with a message sent to the submitter within two business days
    - ***Please ensure all of your pull requests have an associated issue.***
- The ticket will then be groomed and planned as regular sprint work and an estimated timeframe of completion will be communicated to the submitter.
- Once the ticket is complete, a final message will be sent to the submitter letting them know work is complete.

***Please feel free to ping us if you have not received a response after one week***
