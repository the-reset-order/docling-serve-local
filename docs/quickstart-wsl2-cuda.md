# Quickstart: Run Docling Serve on WSL2 with NVIDIA CUDA

This guide walks through setting up **Docling Serve** on a Windows machine using **WSL2** with an NVIDIA GPU. It assumes you want to run the Python package directly inside WSL while using CUDA acceleration exposed from Windows.

> [!TIP]
> If you already have Docker Desktop with GPU support configured, you can run one of the CUDA-enabled container images from the [main README](../README.md) instead of installing Python dependencies inside WSL.

## Prerequisites

- Windows 11 (23H2 or newer) or Windows 10 (22H2) with WSL2 support.
- An NVIDIA GPU with the latest Game Ready, Studio, or Data Center driver **with WSL2 support** (version 551+ recommended).
- Administrative access to enable Windows features and install drivers.
- At least 15 GB of free disk space inside your WSL distribution for Python, models, and temporary conversion artifacts.

## 1. Prepare Windows and WSL2

1. Enable WSL2 and install Ubuntu from an elevated PowerShell prompt:
   ```powershell
   wsl --install -d Ubuntu-22.04
   wsl --set-default-version 2
   ```
   Restart when prompted.
2. Install the latest NVIDIA driver that lists **WSL** support from [NVIDIA's driver downloads](https://www.nvidia.com/Download/index.aspx). Reboot after installation.
3. (Optional) Install [Windows Terminal](https://aka.ms/terminal) for an improved shell experience.

## 2. Update Ubuntu inside WSL

Launch Ubuntu from the Start menu and update the base system:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential curl git python3.11 python3.11-venv python3-pip
```

If you prefer to keep using `python3` instead of `python3.11`, create an alias by adding the following line to `~/.bashrc` and reloading your shell:

```bash
echo 'alias python3=python3.11' >> ~/.bashrc
source ~/.bashrc
```

## 3. (Optional) Install the CUDA Toolkit inside WSL

The Windows driver already exposes CUDA to WSL. Install the user-space CUDA Toolkit if you plan to compile custom GPU kernels or need developer tools:

```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/3bf863cc.pub
sudo install -m 644 3bf863cc.pub /usr/share/keyrings/cuda-wsl-ubuntu.gpg
sudo sh -c 'echo "deb [signed-by=/usr/share/keyrings/cuda-wsl-ubuntu.gpg] https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/ /" > /etc/apt/sources.list.d/cuda-wsl-ubuntu.list'
sudo apt update
sudo apt install -y cuda-toolkit-12-4
```

Verify CUDA access from WSL:

```bash
nvidia-smi
nvcc --version  # Only available if the toolkit is installed
```

## 4. Install Docling Serve with GPU-enabled PyTorch

1. Create an isolated Python environment and upgrade `pip`:
   ```bash
   python3.11 -m venv ~/docling-serve-venv
   source ~/docling-serve-venv/bin/activate
   python -m pip install --upgrade pip
   ```
2. Install the CUDA build of PyTorch that matches your driver (12.4 works well on modern drivers):
   ```bash
   pip install "torch==2.5.1" --index-url https://download.pytorch.org/whl/cu124
   ```
   Replace the version with the latest GPU-enabled release if needed. PyTorch should report `True` for CUDA availability:
   ```bash
   python - <<'PY'
   import torch
   print('CUDA available:', torch.cuda.is_available())
   print('Device name:', torch.cuda.get_device_name())
   PY
   ```
3. Install Docling Serve with the UI extras:
   ```bash
   pip install "docling-serve[ui]"
   ```

## 5. Launch Docling Serve

Start the API server (the UI is enabled for quick testing):

```bash
docling-serve run --enable-ui --host 0.0.0.0 --port 5001
```

Open <http://localhost:5001/ui> in your Windows browser. The traffic reaches WSL through the loopback address.

To confirm GPU utilization, trigger a conversion from the UI or with `curl`, then watch `nvidia-smi` in another WSL terminal.

## 6. Keep models and environment up to date

- Periodically upgrade Docling Serve and PyTorch:
  ```bash
  pip install --upgrade docling-serve torch --index-url https://download.pytorch.org/whl/cu124
  ```
- Clear cached models if you need to reclaim disk space: `rm -rf ~/.cache/docling`.
- Regularly update Ubuntu packages with `sudo apt update && sudo apt upgrade`.

You're ready to run Docling Serve on WSL2 with full CUDA acceleration!
