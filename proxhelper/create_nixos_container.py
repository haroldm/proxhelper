import time
import typer
import subprocess
import toml
from proxmoxer import ProxmoxAPI
from typing_extensions import Annotated

app = typer.Typer()

def pct_exec(vmid, command, check=True):
    full_cmd = ['sudo', 'pct', 'exec', str(vmid), '--', 'sh', '-c', f'source /etc/set-environment; {command}']
    print(f"Executing in container: {command}")
    return subprocess.run(full_cmd, check=check)

def write_configuration_nix(vmid):
    config_nix = '''{ config, modulesPath, pkgs, lib, ... }:
{
  imports = [ (modulesPath + "/virtualisation/proxmox-lxc.nix") ];
  nix.settings = { sandbox = false; };
  proxmoxLXC = {
    manageNetwork = false;
    privileged = false;
  };
  security.pam.services.sshd.allowNullPassword = true;
  services.openssh = {
    enable = true;
    openFirewall = true;
    settings = {
      PermitRootLogin = "yes";
      PasswordAuthentication = true;
      PermitEmptyPasswords = "yes";
    };
  };
  system.stateVersion = "25.05";
}
'''
    subprocess.run(
        ['sudo', 'pct', 'exec', str(vmid), '--', 'sh', '-c', f'source /etc/set-environment; cat > /etc/nixos/configuration.nix'],
        input=config_nix.encode(), check=True)
    print("Wrote /etc/nixos/configuration.nix")

def configure_container(vmid):
    print("Deleting root password to allow empty login...")
    # pct_exec(vmid, ['passwd', '--delete', 'root'])
    pct_exec(vmid, "passwd --delete root")

    print("Writing NixOS configuration...")
    write_configuration_nix(vmid)

    print("Updating Nix channel...")
    # pct_exec(vmid, ['nix-channel', '--update'])
    pct_exec(vmid, "nix-channel --update")

    print("Running nixos-rebuild switch --upgrade...")
    # pct_exec(vmid, ['nixos-rebuild', 'switch', '--upgrade'])
    pct_exec(vmid, "nixos-rebuild switch --upgrade")

def wait_for_container(proxmox, node, vmid):
    print("Waiting for container to start...")
    while True:
        status = proxmox.nodes(node).lxc(vmid).status.current.get()
        if status.get('status') == 'running':
            break
        time.sleep(1)

@app.command()
def create_nixos_container(
    config_path: Annotated[str, typer.Option()]
):
    # Example config: https://gist.github.com/haroldm/8b38e9425869264d401b7fb443effe41
    config = toml.load(config_path)

    required_keys = [
        "vmid", "ctname", "template", "storage", "bridge", "ip", "gateway",
        "memory", "swap", "rootfs_increase", "node", "vlan_tag"
    ]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")

    proxmox = ProxmoxAPI(sudo=True, timeout=60, backend='local')

    print(f"Creating container {config['vmid']} on node {config['node']}")
    task_response = proxmox.nodes(config["node"]).lxc.create(
        vmid=config["vmid"],
        ostemplate=config["template"],
        hostname=config["ctname"],
        ostype='nixos',
        arch='amd64',
        unprivileged=1,
        features='nesting=1',
        net0=f"name=eth0,bridge={config['bridge']},tag={config['vlan_tag']},ip={config['ip']},gw={config['gateway']}",
        memory=int(config["memory"]),
        swap=int(config["swap"]),
        storage=config["storage"]
    )

    print(f"Resizing rootfs by {config['rootfs_increase']}")
    proxmox.nodes(config["node"]).lxc(config["vmid"]).resize.put(
        disk='rootfs',
        size='+' + config["rootfs_increase"]
    )

    print("Starting container...")
    proxmox.nodes(config["node"]).lxc(config["vmid"]).status.start.post()
    wait_for_container(proxmox, config["node"], config["vmid"])

    print("Container started. Proceeding with configuration...")
    configure_container(config["vmid"])
    print("Container is ready. You can now SSH into it.")

