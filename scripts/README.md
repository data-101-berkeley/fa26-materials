# Keeping solutions out of this repo

Twice now a released blank notebook has been replaced on `main` by a solved
copy — fa25 Project 1 and 2, and fa26 Project 1. Both had the same cause.

## What happens

`nbgitpuller` auto-commits whatever is in your pulled directory before it
merges, so your local work is never lost. Those commits are authored by
`nbgitpuller <nbgitpuller@nbgitpuller.link>` and are meant to stay on your
machine. If you then `git push` from that same directory, your solved notebook
becomes the official one.

The fa26 incident published four otter `# BEGIN SOLUTION` blocks in
`proj1.ipynb`, plus 48 cells of saved output, for two weeks.

## The rule

**Never push from a directory you reached through an nbgitpuller link.**
Keep a separate clean clone for releases:

```bash
git clone https://github.com/data-101-berkeley/fa26-materials.git ~/fa26-materials-release
```

Do release work there. Use your DataHub copy only for testing the student
experience.

## Turn on the guard (once per clone)

```bash
git config core.hooksPath .githooks
```

`.githooks/pre-push` then refuses any push that contains otter solution markers
under `proj/` or `disc/`, or any commit authored by nbgitpuller. Git does not
share hooks on clone, so everyone with push access needs this one command.

The same check runs in CI (`.github/workflows/no-solutions.yml`) as a safety
net for anyone who has not enabled the hook.

Run it by hand any time:

```bash
python3 scripts/check_no_solutions.py            # working tree only
python3 scripts/check_no_solutions.py main..HEAD # plus commit authors
```

Genuine exception? `git push --no-verify`. Please be sure.
