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
# Skip if already installed
[ -d "$HOME/.oh-my-zsh" ] && echo "oh-my-zsh already installed" || \
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
```

This will:
- Clone oh-my-zsh to `~/.oh-my-zsh`
- Create a new `.zshrc` from template (backing up existing one if present)
- Set zsh as the default shell (optional, user can decide)

### Step 2: Install zsh-autosuggestions

Clone the zsh-autosuggestions plugin to the oh-my-zsh custom plugins directory:

```bash
# Skip if already installed
[ -d "$HOME/.oh-my-zsh/custom/plugins/zsh-autosuggestions" ] && echo "zsh-autosuggestions already installed" || \
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
```

Then edit `~/.zshrc` to add `zsh-autosuggestions` to the plugins array (if not already present):

```bash
# Find the line: plugins=(git)
# Change to: plugins=(git zsh-autosuggestions)
```

### Step 2b (Optional): Install zsh-syntax-highlighting

Another popular zsh plugin that highlights commands as you type:

```bash
# Skip if already installed
[ -d "$HOME/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting" ] && echo "zsh-syntax-highlighting already installed" || \
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
```

Add to plugins (must be last in the plugin list):

```bash
# plugins=(git zsh-autosuggestions zsh-syntax-highlighting)
```

### Step 3: Install autojump

Clone autojump from GitHub and run the Python installer:

```bash
# Skip if already installed
[ -d "$HOME/.autojump" ] && echo "autojump already installed" || \
(git clone --depth 1 https://github.com/wting/autojump.git /tmp/autojump && \
cd /tmp/autojump && python3 install.py && rm -rf /tmp/autojump)
```

After installation, add the source line to `~/.zshrc`:

```bash
# Add to end of ~/.zshrc:
[[ -s "$HOME/.autojump/etc/profile.d/autojump.sh" ]] && source "$HOME/.autojump/etc/profile.d/autojump.sh"
```

Note: Uses `$HOME` to work on any machine.

### Step 4: Install amix/vimrc

Clone the vimrc repository directly to `~/.vim_runtime` and run the installer:

```bash
# Skip if already installed
[ -d "$HOME/.vim_runtime" ] && echo "vimrc already installed" || \
(git clone --depth=1 https://github.com/amix/vimrc.git ~/.vim_runtime && \
sh ~/.vim_runtime/install_awesome_vimrc.sh)
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
echo "ZSH: $ZSH"

# Check zsh-autosuggestions
zpty -t zsh_autosuggestions 2>/dev/null && echo "zsh-autosuggestions: OK" || echo "zsh-autosuggestions: loaded via plugin"

# Check autojump
j --help >/dev/null 2>&1 && echo "autojump: OK" || echo "autojump: FAIL"

# Check vimrc
[ -f "$HOME/.vim_runtime/vimrcs/awesome.vim" ] && echo "vimrc: OK" || echo "vimrc: FAIL"

# Check nvm
nvm --version >/dev/null 2>&1 && echo "nvm: $(nvm --version)" || echo "nvm: FAIL"

# Check conda
conda --version >/dev/null 2>&1 && echo "conda: $(conda --version)" || echo "conda: FAIL"

# Check mamba
mamba --version >/dev/null 2>&1 && echo "mamba: $(mamba --version)" || echo "mamba: FAIL"
```

## Notes

- All git clone operations use `--depth 1` for faster cloning
- If network issues occur, retry the git commands
- The conda/mamba paths MUST be extracted from the user's existing `.bashrc` - do not assume default paths
- For the vimrc installation, use `sh` not `bash` to run the installer (per official docs)
- The default theme is set to "robbyrussell" but can be changed in `~/.zshrc`
