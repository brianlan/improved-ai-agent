---
name: new-machine-basic-setup
description: Set up a new Linux machine with essential development tools. Use this skill whenever the user mentions setting up a new machine, fresh install, new computer, or wants to install oh-my-zsh, zsh plugins, autojump, vim config, or sync environment variables from bashrc to zshrc. This skill handles the complete basic dev environment setup in one go.
---

# New Machine Basic Setup

This skill sets up a fresh Linux machine with essential development tools and configurations.

## Prerequisites

- Linux system with bash and zsh installed
- Git available
- User has sudo privileges (for package installation if needed)
- Home directory writable

## Setup Steps

Execute these steps in order. Each step is independent and should complete before moving to the next.

### Step 1: Install oh-my-zsh

Run the official oh-my-zsh installation script unattended:

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
```

This will:
- Clone oh-my-zsh to `~/.oh-my-zsh`
- Create a new `.zshrc` from template (backing up existing one if present)
- Set zsh as the default shell (optional, user can decide)

### Step 2: Install zsh-autosuggestions

Clone the zsh-autosuggestions plugin to the oh-my-zsh custom plugins directory:

```bash
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
```

Then edit `~/.zshrc` to add `zsh-autosuggestions` to the plugins array:

```bash
# Find the line: plugins=(git)
# Change to: plugins=(git zsh-autosuggestions)
```

### Step 3: Install autojump

Clone autojump from GitHub and run the Python installer:

```bash
git clone --depth 1 https://github.com/wting/autojump.git /tmp/autojump && cd /tmp/autojump && python install.py
```

After installation, add the source line to `~/.zshrc`:

```bash
# Add to end of ~/.zshrc:
[[ -s /home/rlan/.autojump/etc/profile.d/autojump.sh ]] && source /home/rlan/.autojump/etc/profile.d/autojump.sh
```

Note: Adjust the path if the home directory is different - use the actual home path from the install output.

### Step 4: Install amix/vimrc

Clone the vimrc repository directly to `~/.vim_runtime` and run the installer:

```bash
git clone --depth=1 https://github.com/amix/vimrc.git ~/.vim_runtime
sh ~/.vim_runtime/install_awesome_vimrc.sh
```

This installs the "Awesome Vim Configuration" with many plugins and sensible defaults.

### Step 5: Sync nvm from .bashrc to .zshrc

Check if nvm is already in `~/.zshrc`:

```bash
grep -q "NVM_DIR" ~/.zshrc && echo "exists" || echo "not exists"
```

If not present, copy from `.bashrc`:

```bash
# Add to ~/.zshrc:
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
```

### Step 6: Sync conda/mamba from .bashrc to .zshrc

Check if conda is already in `~/.zshrc`:

```bash
grep -q "conda" ~/.zshrc && echo "exists" || echo "not exists"
```

If not present, copy from `.bashrc` but adapt for zsh:

```bash
# Add to ~/.zshrc (adjust paths to match the user's miniforge/conda installation):
# >>> conda initialize >>>
__conda_setup="$('path/to/conda' 'shell.zsh' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "path/to/conda.sh" ]; then
        . "path/to/conda.sh"
    else
        export PATH="path/to/conda/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

# >>> mamba initialize >>>
export MAMBA_EXE='path/to/mamba';
export MAMBA_ROOT_PREFIX='path/to/miniforge';
__mamba_setup="$("$MAMBA_EXE" shell hook --shell zsh --root-prefix "$MAMBA_ROOT_PREFIX" 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    alias mamba="$MAMBA_EXE"
fi
unset __mamba_setup
# <<< mamba initialize <<<
```

**Important:** Extract the actual paths from the user's `~/.bashrc` - look for the conda/mamba initialize blocks and copy the exact paths (e.g., `/ssd/home/rlan/miniforge3` or `$HOME/miniconda3`, etc.).

## Verification

After all steps complete, verify the setup:

```bash
# Source the updated zshrc
source ~/.zshrc

# Check oh-my-zsh
echo $ZSH  # Should show ~/.oh-my-zsh

# Check autojump
j --help  # Should show autojump help

# Check nvm
nvm --version  # Should show version number

# Check conda
conda --version  # Should show version number
```

## Notes

- All git clone operations use `--depth 1` for faster cloning
- If network issues occur, retry the git commands
- The conda/mamba paths MUST be extracted from the user's existing `.bashrc` - do not assume default paths
- For the vimrc installation, use `sh` not `bash` to run the installer (per official docs)
- The default theme is set to "robbyrussell" but can be changed in `~/.zshrc`
