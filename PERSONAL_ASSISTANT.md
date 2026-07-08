# Personal Assistant

The **Life Organizer / Personal Assistant** app no longer lives in this GitHub Pages repository.

## New home

**Repository:** [github.com/swimmerbilly/personalassistant](https://github.com/swimmerbilly/personalassistant)

A full copy of the app (backend + frontend at repo root) is on branch [`personalassistant-standalone`](https://github.com/swimmerbilly/swimmerbilly.github.io/tree/personalassistant-standalone) until the dedicated repo is created.

## Set up the new repo

1. On GitHub, create a new repository named **`personalassistant`** (public or private).
2. From your machine (or cloud agent), push the standalone branch:

```bash
git clone https://github.com/swimmerbilly/swimmerbilly.github.io.git
cd swimmerbilly.github.io
git checkout personalassistant-standalone
git remote set-url origin https://github.com/swimmerbilly/personalassistant.git
git push -u origin personalassistant-standalone:main
```

3. Clone and run:

```bash
git clone https://github.com/swimmerbilly/personalassistant.git
cd personalassistant
./start.sh
```

Configure credentials in `backend/.env` (see `backend/.env.example`).

This repo (`swimmerbilly.github.io`) remains your static website only.
