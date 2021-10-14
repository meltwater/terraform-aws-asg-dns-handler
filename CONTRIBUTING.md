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
- [ ] Add tests to cover changes under terratest directory.
- [ ] Ensure your code follows the code style of this project.
- [ ] Ensure CI and all other PR checks are green OR
    - [ ] Code compiles correctly.
    - [ ] Created tests which fail without the change (if possible).
    - [ ] All new and existing tests passed.
- [ ] Add your changes to `Unreleased` section of [CHANGELOG](CHANGELOG.md).
- [ ] Improve and update the [README](README.md) (if necessary).


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
