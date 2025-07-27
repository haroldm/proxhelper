## What is `proxhelper`?

This is a collection of scripts that help me manage my Proxmox host and guests in a simple way.
Some values may be hardcoded and you probably shouldn't use this project as is.

## Dependencies

```bash
sudo apt install pipx
pipx install uv
```

## Run the tool with `uv`

```bash
uv run -m proxhelper.cli create-nixos-container --config-path ./config.toml
```

## Install the tool with `pipx`

```bash
pipx install -e ./ # Install as editabled
sudo $(which proxhelper) get-image --type lxc --os nixos --version 25.05
```
