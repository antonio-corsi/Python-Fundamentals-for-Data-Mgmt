# Install Python on Windows 10/11 with Miniconda, Conda, Windows Terminal, and Visual Studio Code

This guide describes a simple and orderly configuration for using **Python on Windows 10/11** during the course, using **Command Prompt (cmd)** inside **Windows Terminal**.

The idea is:

```text
Miniconda
   ↓
Conda
   ↓
Command Prompt (cmd)
   ↓
Visual Studio Code
   ↓
Python + Python extensions
```

This keeps Python and the packages used in the course isolated from the rest of the system.

---

## Contents

0. [What is a Python environment](#1-what-is-a-python-environment)
1. [Install Visual Studio Code](#1-install-visual-studio-code)
2. [Install Miniconda](#2-install-miniconda)
3. [Make Conda available in the Command Prompt in Windows Terminal](#3-make-conda-available-in-the-command-prompt-in-windows-terminal)
4. [Create a Conda environment dedicated to the course](#4-create-a-conda-environment-dedicated-to-the-course)
5. [Activate the course environment](#5-activate-the-course-environment)
6. [Isolate the environment with `PYTHONNOUSERSITE`](#6-isolate-the-environment-with-pythonnousersite)
7. [Check Python](#7-check-python)
8. [Update `pip`](#8-update-pip)
9. [Install packages with Conda](#9-install-packages-with-conda)
10. [Python interpreter and Jupyter kernel](#10-python-interpreter-and-jupyter-kernel)
11. [Launch Visual Studio Code from the Conda environment](#11-launch-visual-studio-code-from-the-conda-environment)
12. [Install the Python and Jupyter extensions in VS Code](#12-install-the-python-and-jupyter-extensions-in-vs-code)
13. [Select the kernel in VS Code](#13-select-the-kernel-in-vs-code)
14. [Recommended workflow during the course](#14-recommended-workflow-during-the-course)
15. [End the session](#15-end-the-session)
16. [Common problems](#common-problems)
17. [If you have problems with VS Code / Jupyter](#if-you-have-problems-with-vs-code--jupyter)
18. [Command summary](#command-summary)
19. [Fundamental concept](#fundamental-concept)
20. [Mistakes to avoid](#mistakes-to-avoid)

---

## 0. What is a Python environment

![](una-distribuzione-Python.png)

## 1. Install Visual Studio Code

If Visual Studio Code is not already installed:

1. download **Visual Studio Code** from the official Microsoft website;
2. run the installer;
3. leave the standard options enabled;
4. check that the `code` command is available from the terminal.

Open **Windows Terminal** using the **Command Prompt** profile and type:

```cmd
code --version
```

If the VS Code version number is displayed, the `code` command is configured correctly.

---

## 2. Install Miniconda

**Miniconda** is a minimal distribution that installs:

- Python;
- `conda`, the environment and package manager;
- a few other essential components.

It is lighter than Anaconda and allows you to install only what you need.

Download the **Miniconda for Windows 64-bit** version from the official website and run the `.exe` file.

You can **update conda**, when a new version is available, with 

```cmd
conda update -n base
```

or (if the new version were, for example, 26.7.2):

```cmd
conda install -n base -c defaults conda=26.7.2
```

*base* is the environment where conda lives.


### Recommended settings

During installation:

- choose **Just Me**, unless you have specific requirements;
- leave the suggested installation folder;
- **there is no need to add Miniconda to the Windows PATH**;
- complete the installation with the default options.

---

## 3. Make Conda available in the Command Prompt in Windows Terminal

After installing Miniconda, you may need to initialize Conda once for **cmd.exe**.

From the **Start** menu, open:

```text
Miniconda Prompt
```

and type:

```cmd
conda init cmd.exe
```

Then close Miniconda Prompt.

Also close any Windows Terminal windows that are already open and reopen **Windows Terminal** with the profile:

```text
Command Prompt
```

Check that Conda is available:

```cmd
conda --version
```

For example:

```text
conda 26.x.x
```

> `conda init cmd.exe` normally needs to be run only once.

---

## 4. Create a Conda environment dedicated to the course

It is good practice **not to work directly in the `base` environment**.

Let us create a separate environment for the course, giving it the **generic name *myenv***:

```cmd
conda create -n myenv python=3.11
```

Where:

- `conda create` creates a new environment;
- `-n myenv` assigns the name `myenv`;
- `python=3.11` installs Python 3.11 in the environment.

When Conda asks:

```text
Proceed ([y]/n)?
```

type:

```text
y
```

and press **Enter**.

To see the available environments:

```cmd
conda env list
```

or:

```cmd
conda info --envs
```

However, a **better** command for creating the conda environment is the following:

```cmd
conda create -n myenv -c conda-forge --override-channels python=3.11
```

With `--override-channels`, conda uses only *conda-forge* and ignores `defaults`. It therefore does not mix packages compiled in different ways, which is the typical cause of conflicts. The command gives the same result on any PC, regardless of its configuration, and does not access the Anaconda channel, which is subject to licensing terms for corporate use.

👉 After this command, the output of:

```cmd
conda list
```

must always show **ONLY** *conda-forge* in the last column, "channel".


> 📌 If the *myenv* environment already exists and you want to recreate it, you must first **delete it** with the conda command:
>
> ```cmd
> conda remove --name myenv --all -y 
> ```
>
> and then, to be safe, check that the *%USERPROFILE%\miniconda3\envs\myenv* folder no longer exists.<br>
> Otherwise, delete it (from the parent folder) with the *cmd* terminal command:
> ```cmd
> rmdir /s /q myenv 
> ```

---

## 5. Activate the course environment

Whenever you start working on the course, open **Windows Terminal** with the **Command Prompt** profile and type:

```cmd
conda activate myenv
```

The prompt should change and show the environment name:

```text
(myenv) C:\Users\NomeUtente>
```

The presence of:

```text
(myenv)
```

indicates that the environment is active.

An <u>additional check of the active environment</u>, which also gives the environment's path, is the following:

```text
echo %CONDA_PREFIX%
```

The prompt only shows the environment name; the variable also tells you **where the environment is located on disk**.

---

## 6. Isolate the environment with `PYTHONNOUSERSITE`

On some computers, Python can find packages previously installed in the user's personal folder (the so-called *user-site*), even when a Conda environment is active.

To prevent Python from using these packages outside the course environment, in **Command Prompt (cmd)** you can set (**with the *myenv* environment active**):

```cmd
set PYTHONNOUSERSITE=1
```

This environment variable tells Python:

> do not add the user's *user site-packages* folder to the module search path.

In fact, it means:

```text
PYTHON      → concerns Python's behavior
NO          → excludes
USER SITE   → the folder of packages installed at user level
=1          → enables this option
```

In practice, it helps **ensure that Python uses only the packages available in the active Conda environment and its dependencies**.

Simplified diagram:

```text
Without PYTHONNOUSERSITE=1

Conda environment
      │
      ├── environment packages
      │
      └── possible packages installed in the user folder (user-site)
                         ↑
                  possible interference
```

With:

```cmd
set PYTHONNOUSERSITE=1
```

the result is:

```text
Conda environment
      │
      └── environment packages
             ↑
      more isolated environment
```

This can be particularly useful during a course because it reduces the risk of two participants getting different behavior due to Python packages previously installed on their computers.

## When to run the command

One possible sequence for starting a session is:

```cmd
conda activate myenv
set PYTHONNOUSERSITE=1
```

Later, **not now**, we will launch VS Code from the terminal with:
```cmd
code
```

This way, VS Code will be launched with the *PYTHONNOUSERSITE* variable already set and will inherit it.

## Warning: `set` applies only to the current session

With Command Prompt, the command:

```cmd
set PYTHONNOUSERSITE=1
```

sets the variable only in the current terminal window and in programs launched from it.

When that Windows Terminal window is closed, the setting is lost.

Therefore, in the next session, you may need to run the following again:

```cmd
set PYTHONNOUSERSITE=1
```

This behavior is often preferable during a course because it does not permanently change the Windows configuration.

## Check the value

To check that the variable is set:

```cmd
echo %PYTHONNOUSERSITE%
set PYTHONNOUSERSITE       # the alternative

```

The output should be:

```text
1                   # if echo %PYTHONNOUSERSITE% was run
PYTHONNOUSERSITE=1  # if set PYTHONNOUSERSITE was run
```

## Typical pitfalls

👉 **The *cmd* `set` command has some classic pitfalls**:
- the *cmd* command `set NOME=valore` is equivalent to $env:NOME = "valore" in PowerShell: <u>it applies only to that window and to processes launched from it</u> — exactly what we need, provided it is run **before `pip install` in the same window**;
- no spaces around the =: unlike PowerShell, `set PYTHONNOUSERSITE = 1` would create a variable called `PYTHONNOUSERSITE` (with a trailing space in the name!) and our protection against contamination would fail silently;
- no quotation marks: in *cmd*, they would become part of the value (`set X="1"` stores exactly "1", including quotation marks) ⟶  check the variable; if it is not defined, it prints "environment variable not defined».

## Make the setting persistent

To avoid having to remember to set the *PYTHONNOUSERSITE* variable in every new terminal instance, you can make the setting persistent with:

```cmd
setx PYTHONNOUSERSITE 1
```
Things to know:
- `setx` applies only to **terminals opened AFTER running this command, not to the current window**. In that window, you still need to run set PYTHONNOUSERSITE=1 once more, or close and reopen the terminal.
- **programs that are already open do not see it. VS Code must be closed completely**, in all windows, and reopened. From then on, notebook kernels also inherit it.
- administrator privileges are not required. The variable is written to the registry under the HKCU\Environment key and applies only to your user. With /M at the end, from a prompt opened as administrator, it would apply to all users of the PC.
- it affects all Python installations for your user, in every environment and every terminal (cmd, PowerShell, VS Code). Packages installed with pip install --user become invisible everywhere.

Check in a new terminal:

```cmd
echo %PYTHONNOUSERSITE%
python -m site
```

The first command **must print 1**. At the bottom of the second command's output, **you must see *ENABLE_USER_SITE: False***. 

In addition, a complementary check is the following:

```cmd
python -m pip list --user
```

The command lists **what is in the user folder**, and `python -m site --user-site` prints **its path**. It must be run with the variable unset; otherwise, the list is empty. If there is nothing you need there, emptying that folder eliminates the problem at its source. The variable then remains as protection for the future.

## Remove the setting in the current session

To delete the variable:

```cmd
set PYTHONNOUSERSITE=
```

After this command:

```cmd
echo %PYTHONNOUSERSITE%
```

it should no longer show `1`.

## 7. Check Python

With the environment active:

```cmd
python --version
```

For example:

```text
Python 3.11.x
```

To check which Python executable is being used:

```cmd
where python
```

The first path shown should refer to the folder of the `myenv` Conda environment.

To check **exactly which Python interpreter is executing the command**, you can also use:

```cmd
python -c "import sys; print(sys.executable)"
```

The meaning is:

- `python` starts the currently active Python interpreter;
- `-c` means **execute the code specified between quotation marks directly**;
- `import sys` imports the `sys` system module;
- `sys.executable` contains the full path of the Python interpreter in use;
- `print(...)` displays that path.

Example result:

```text
C:\Users\NomeUtente\miniconda3\envs\myenv\python.exe
```

This command is very useful for checking that the Python in the course's Conda environment is actually being used.

---

## 8. Update `pip`

With the environment active:

```cmd
python -m pip install --upgrade pip
```

To check:

```cmd
python -m pip --version
```

---

## 9. Install packages with Conda

With **the course's conda environment active** ⚠️:

```cmd
conda activate myenv
```

packages are installed with:

```cmd
conda install NOME_PACKAGE
```

For example:

```cmd
conda install numpy
```

To install several packages together:

```cmd
conda install numpy pandas matplotlib scikit-learn
```
To **install the entire suite of course packages**, from the **parent** folder:

```cmd
conda install -n myenv -c conda-forge --override-channels --file requirements_TM_conda.txt
```

For this specific course, there is also a package to install with **pip**, `it_core_news_sm`, after the dry run (***--dry-run***):

```cmd
python -m pip install --dry-run -r requirements_TM_pip.txt
```

and then, if everything is fine, install it for real:

```cmd
python -m pip install -r requirements_TM_pip.txt
```

Of course, `conda list` now shows a package (`it-core-news-sm`) with **channel=pypi**.

👉 **The conda / pip installation is complete**. Let's now look at some installation *topics* in more detail.

### Specify the channel

A **Conda channel** is the repository from which Conda downloads packages. Specifying it in the conda installation command is not mandatory.

However, a widely used channel in scientific computing and Data Science is **conda-forge**.

> **Recommendation.** 
>
> <u>**Use `conda-forge` as the only channel and exclude the `defaults` channel</u> (through the *--override-channels* option)**; the *defaults* channel, among other things, requires a <u>commercial license</u> for companies with more than 200 employees/contractors.
>
> For the course, we will therefore adopt `conda-forge` as the **only source** of packages, to make the environment more consistent and reproducible and avoid mixing packages from different channels.
>
> The recommended form of conda installation will therefore be this, with the ```-c conda-forge``` option:
>
> ```cmd
> conda install -c conda-forge --override-channels NOME_PACKAGE
> ```
>
> The `--override-channels` option tells Conda precisely to ignore the channels already configured on the system, including `defaults`, and to use only those specified with `-c`.
>
> `-c` is short for ```--channel```

### Install the packages needed for the course

For example:

```cmd
conda install -c conda-forge --override-channels numpy pandas matplotlib scikit-learn
```

To check the installed packages:

```cmd
conda list
```

> 👉 ```conda list``` also reports the source of the package.

> 📌 Here is the **meaning of the output of ```conda list```**:
>
> *conda list* lists the packages installed in a conda environment, i.e. an isolated folder containing a Python interpreter and a set of packages.
>
> The header lines. 
> - **packages in environment at *C:\Users\Utente\miniconda3***: indicates which environment we are looking at. 
>
> The four columns.
>
> **Name**: the name of the package.
> **Version**: the software version.
> **Build**: the specific "packaging" of that version. There can be several builds of the same version, for different versions of Python or recompiled after a fix.
> **Channel**: the channel, i.e. the online repository from which the package was downloaded:
> - if the cell is empty, the package comes from Anaconda's default channels (*defaults*)
> - *conda-forge* is the community-managed channel
> - *pypi* is not a conda channel: it indicates a package installed with *pip* from PyPI (Python Package Index, the Python package repository.

> <u>Rule of thumb</u>: **always specify the environment explicitly with ```-n <env>``` (or ```-p <percorso>```) even when it is already active**: this avoids the class of errors «command ended up in the wrong environment» due to **distraction** (the active conda environment had been changed!!). 

### pip list

If we now run:

```cmd
python -m pip list
```

we still get a list of packages! Is that an error? No!

```cmd
python -m pip list
```
shows all the Python packages present in the environment, not just those installed by pip. Libraries installed by conda carry the standard metadata that pip can read, so they appear there too.<br>
To find out who installed what:
```cmd
conda list | findstr pypi
```
lists only the packages installed with pip. If it prints nothing, pip has not installed anything.<br>
```cmd
python -m pip list -v
```
 adds the *Installer* (`conda` or `pip`) and *Location* columns; the latter must always be the environment folder.


### Installation strategy

Always prioritize `conda install`; use `python -m pip install` only for packages not available through **Conda**.

However, there are **two important precautions**.

**1. Follow the chronological order**

 It is advisable to install **everything possible with Conda first** and, only afterwards, **what remains with pip**.

The reason is that Conda, when resolving the environment, does not fully manage packages already installed by pip. If something is installed with pip and then a subsequent:

```cmd
conda install ...
```

is run, Conda may modify or replace files and dependencies on which the package installed with pip relied, making the previous installation inconsistent or nonfunctional.

For this reason, it is advisable to leave **pip "at the end"**, therefore:

```text
1. conda install ...
2. conda install ...
3. conda install ...
4. python -m pip install ...   ← only the missing packages (not installable with conda)
```

**2. Do not alternate between Conda and pip for the same package**

Once a package has been installed with pip, updates to **that package** must **always be carried out with pip, not with Conda, and vice versa**.

For example, if a package was installed with:

```cmd
python -m pip install nome-pacchetto
```

subsequent updates should be carried out with:

```cmd
python -m pip install --upgrade nome-pacchetto
```

and not with:

```cmd
conda update nome-pacchetto
```

👉 Mixing the two managers for the same package is one of the most common causes of inconsistent Python environments.

### Recommended form for pip

In any case, always prefer:

> ```cmd
> python -m pip install NOME_PACKAGE
> ```
to the form:

> ```cmd
> pip install NOME_PACKAGE
> ```

The meaning is:
- `python` invokes the currently active Python interpreter;
- `-m` means **run the active Python's pip module** → this way, the active Python interpreter runs **ITS OWN** `pip` module.
- `pip`, as is known, is a module that manages package installation;
- `install NOME_PACKAGE` asks pip to install the specified package.

That is, in summary, ```python -m pip install pandas ``` means: use **this active Python** to run **its pip** and install `pandas`.

This form is preferable to the simple and faster `pip install` because it reduces the risk of accidentally using a `pip` belonging to another Python installation.

It is therefore particularly useful when the PC has:
- multiple versions of Python;
- multiple Conda environments;
- Python also installed outside Miniconda.

### `pip` commands to avoid

**⛔ Always avoid, as mentioned:**

```cmd
pip install NOME_PACKAGE
```

The problem is simple: **which `pip` is being run?**

If there are multiple versions of Python or multiple environments on the PC, the `pip` command found in the `PATH` might not be the one associated with the Python interpreter of the active environment.

**⛔ Avoid (almost always):**

```cmd
python -m pip install --user NOME_PACKAGE
```

The ```--user``` option installs the package in the **user-site**, i.e. in a personal folder belonging to the Windows user, **not in the course's Conda environment**.

On Windows, the *user-site* path is typically similar to:

```text
%APPDATA%\Python\PythonXX\site-packages
```
where: *%APPDATA% = C:\Users\User\AppData\Roaming*.

On my PC, the *user-site* is here:<br>
![](my-user-sites.png)

So:

```text
myenv environment
         │
         ├── environment packages
         │
         └── does NOT contain packages installed with --user

 Windows user-site
         │
         └── packages installed with --user
```

With `venv` (Python's native virtual environment manager, an alternative to conda), the `pip install --user` command is generally rejected because the *user-site* is not visible within the environment. With a Conda environment, however, this command **can install the package outside the environment without the error being obvious**: you may therefore believe you have installed the package in your environment when it is actually in the *user-site*.

The pip `--user` option (when pip must be used) is therefore **the wrong tool**, because it does not isolate the environment.

The *user-site* mechanism and how to neutralize its use are explained in the section dedicated to: ```set PYTHONNOUSERSITE=1```.

**Why did we say “almost always” earlier and not “always”?**

`--user` has some legitimate uses outside the scope of this guide. The classic case is using **system Python without administrator permissions**, when you want to install a package only for the current user.

Another case concerns certain command-line tools that you want to make available to the user independently of the environment; for this scenario, it is now often preferable to use dedicated tools such as `pipx`.

In our course, which always uses a dedicated Conda environment, the **pip rule of thumb** can be summarized as follows:

```text
DO NOT install packages with pip (except packages that CANNOT be installed with conda, and at the end)
if installing with pip is necessary, DO NOT use 'pip install ...' 
use, only when necessary: 'python -m pip install ...'
in any case, in these cases, DO NOT use 'python -m pip install --user ...'
later, if a package had to be installed with pip, perform any upgrade only with pip itself (and never with conda)
```

### Restarting the kernel

After installing a package from the terminal, if VS Code or another IDE was already open, it is normally necessary to restart the VS Code (or other IDE) kernel so that the newly installed module is **recognized correctly** by the running code.

If the kernel is not restarted, attempting to import the package (e.g. `import nome_pacchetto`) will almost certainly produce a `ModuleNotFoundError`, because the currently active Python process <u>has already loaded into memory the list of modules available when it started</u>.

💡 The alternative to restarting the kernel: **"magic" commands**<br>
If you want to avoid restarting the kernel and losing the variables loaded in memory, you can install the package <u>directly inside a notebook cell</u> using Jupyter's "magic commands". This way, the kernel updates automatically without needing to restart:<br>

For **pip**:
- `%pip install <nome_pacchetto>`<br>

For **conda**:
- `%conda install <nome_pacchetto>`
<br>

🛠️ How to **quickly restart the kernel in VS Code**<br>
If the package has already been installed from the external or integrated (in VS Code) terminal, the kernel can be restarted in two quick ways:
1.	Click the *Restart* button (the circular arrow icon) in the toolbar at the top of the VS Code notebook.
2.	Alternatively, press *Ctrl + Shift + P (or Cmd + Shift + P on Mac)*, type "Jupyter: Restart Kernel" and press *Enter*.

Conversely, if Visual Studio Code was not open when the package was installed from the terminal,  simply open VSC and then start the notebook kernel: the new environment **is loaded from scratch**. In this case, Python immediately detects all the updated modules and they can be imported straight away in VSC without performing any restart operation.

###  Installations from an IDE??

📌 **Important: do not install packages from IDE cells with `!pip` or `!conda`**

Avoid running commands such as the following in IDE cells:

```python
!pip install nome_pacchetto
```

or:

```python
!conda install nome_pacchetto
```

The `!` prefix runs the command through a **separate shell**. In that context, there is no guarantee that the `pip` or `conda` found corresponds exactly to the Python environment associated with the notebook **kernel**.

The risk is therefore installing the package in an environment different from the one actually used by the notebook, creating inconsistencies or problems in the kernel.

**Recommended rule for the course:** always install packages from **Windows Terminal**, after activating the Conda environment, or, if the package is not available with conda, with pip.

## 10. Python interpreter and Jupyter kernel

Since we will work exclusively with **Jupyter notebooks (`.ipynb`)** during the course, it is important to distinguish between two concepts: **Python interpreter** and **Jupyter kernel**.

### The Python interpreter

The **interpreter** is the program that executes the Python language.

In our Conda environment, ```myenv```, the interpreter is the `python.exe` file installed inside that environment.<br>
In simplified form:

```text
Conda environment: myenv
        │
        └── python.exe
             ↑
        Python interpreter
```

When we create the environment with:

```cmd
conda create -n myenv python=3.12
```

we are creating a virtual (conda) environment that contains, among other things, a specific **Python 3.12 interpreter**.

The interpreter determines:

> **which Python we are using, which pip, and which packages belong to that environment.**

👉 To **run a python file** (suffix *.py*) in VS Code, it is necessary to <u>choose an interpreter</u> (and not a kernel),in this way:

```text
ctrl + shift + P
   ↓
Python Select Interpreter
   ↓
myenv (X.YY.ZZ)
```
---

### The Jupyter kernel

A Jupyter notebook does not execute cells directly simply "through Python": it uses a **kernel**.

The **kernel** is an active process that:

- uses a particular Python interpreter;
- receives the code of the cells from the notebook;
- executes it;
- returns the results to VS Code;
- **keeps the session state in memory**.

For example, if we run the following in a cell:

```python
x = 100
```

and subsequently, in another cell:

```python
print(x)
```

we obtain:

```text
100
```

because the **kernel has remained active and keeps `x` in memory**.

If we run:

```text
Restart Kernel
```

the **kernel memory is cleared and the previously created variables no longer exist**.

The essential difference is therefore:

```text
INTERPRETER = which Python installation is used

KERNEL      = the active session that uses that interpreter
              to execute the notebook cells
```

👉 The complete relationship is therefore:

```text
Conda environment
myenv
      │
      ├── Python 3.12  (to run .py files)
      │      │
      │      └── INTERPRETER
      │              |
      |              |
      |              ▼
      |        lines of code 
      |            executed
      |
      └── ipykernel
             │
             ▼
        JUPYTER KERNEL
             │
             ▼
       jupyter notebook (to run .ipynb files)
             │
             ▼
        code cells
           executed
```

---

### Install `ipykernel`

To enable the Conda environment to be used as the kernel of a Jupyter notebook, **we install the `ipykernel` package**

First, as always, we must activate the environment **from the terminal**:

```cmd
conda activate myenv
```

and then install:

```cmd
conda install ipykernel
```

Even better is to explicitly force the use of the *conda-forge* channel:

```cmd
conda install -c conda-forge --override-channels ipykernel
```

As stated, therefore, `ipykernel` is the **component that connects the environment's Python interpreter to the execution mode required by Jupyter notebooks**.

In simple terms:

```text
VS Code / Jupyter  (interface: cells, output)
        │   ▲
        │   │   Jupyter protocol (messages: "run this code", "here is the result")
        ▼   │
┌─────────────────────────────────────┐
│  kernel = python.exe process        │
│           running ipykernel         │
│  (Python + environment packages)    │
└─────────────────────────────────────┘
```

---
> 👉 With other tools, such as **Jupyter Notebook or JupyterLab**, if they are launched from an environment other than `myenv`, it is also necessary to **register the kernel**, that is, tell Jupyter which Python interpreter to launch. [Conversely, if the launch environment is `myenv`, the default kernel is already the environment's kernel, and registration is not needed].
>
> The <u>complete and correct sequence</u> to **install and register the kernel** is therefore:
>
> ```cmd
> conda activate myenv
> conda install -c conda-forge --override-channels ipykernel
> python -m ipykernel install --user --name myenv --display-name "Python (myenv)"
> ```
>
> 👉 In VS Code, however, registration (the third command) is not necessary: the **Python** and **Jupyter** extensions detect the available Conda environments and allow them to be selected directly. Installing `ipykernel` (the second command) remains necessary; if it is missing, VS Code offers to install it when a cell is first run. In this case, however, it is always preferable to install it from the terminal, rather than delegate the operation to VS Code: this way we choose the channel from which to download it (*conda-forge*) and, if something goes wrong, **we see the error messages in full**.








---

## 11. Launch Visual Studio Code from the Conda environment

This is the recommended workflow.

First activate the environment:

```cmd
conda activate myenv
```

Then launch Visual Studio Code:

```cmd
code
```

Or, if you are already in the project folder:

```cmd
code .
```

The dot `.` means:

> open the current folder in VS Code.

Example:

```cmd
cd C:\CorsoPython
conda activate myenv
code .
```

This opens VS Code **directly in the current folder (thanks to code .)**, the project folder, and it **inherits the Windows environment variables of the active environment**, that is, the Windows environment variables (primarily Path) at launch time (**it inherits them even without .**). This is the normal mechanism in Windows whereby a *child* process, that is, one launched by another process called the *parent*, starts with the parent's variables.

Notes:
- Windows environment variables are inherited from the prompt **only if VS Code is not already running**. If an instance (that is, a running copy of VS Code) is already open, ```code``` does not launch a new VS Code: it passes the request to that instance, which opens a new window. **The parent of the new window is therefore the already open VS Code, not our prompt!**. The window therefore receives that instance's variables and not those just modified by ```conda activate```. If the instance was launched from the *Start* menu, the *myenv* folders are not in its *Path*. This is a **common trap**, which explains many cases of "I activated the env but VS Code cannot see it". The <u>practical rule</u> is therefore simple: **close all VS Code windows before launching ```code```**.
- 👉 in any case, even when the variables are inherited correctly, this method (of launching VS Code with ```code``` from the terminal) does not automatically guarantee that the *.ipynb* notebook will use *myenv* as its kernel (see the following steps): however, it reduces initial ambiguities and makes Python environment detection more predictable.
- ⚠️ after opening it, it will still be **necessary to check the kernel selected in the notebook**, at the top right.
<br>
<br>

> 🛑 There is a **shortcut for navigating the Windows folder tree**: navigating from Explorer is much faster than from the terminal!<br>

> In fact, all that is needed is to run the following from the terminal (once only, persistently for subsequent terminal sessions):
> ```cmd
> conda init cmd.exe
> # or
> conda init powershell
> ```
> If you get “No action taken”, it means that initialization had already been done.
>
> At this, point we must close and reopen the terminal; `conda init` modifies settings that the terminal reads only at startup.
>
> A terminal will open without the base prefix (typical of conda), but it will be sufficient to run:
> ```cmd
> conda --version
> conda activate <myenv>
> ```
> 
> 👉 At this point the terminal is **equivalent to a miniconda prompt**.
>
>
> At this point the shortcut is active and we can therefore use it as follows:
> - navigate in Windows Explorer to the desired folder (e.g. *myenv*) and use the mouse to select the path in the bar at the top
> - type *cmd* or *powershell* in the bar
> - press Enter and a terminal (of the chosen type) will open **set to that path** (without having to navigate there from the terminal!!).


---

## 12. Install the Python and Jupyter extensions in VS Code

⚠️ They are installed **only once for each VS Code installation**. Creating or deleting conda environments does not affect them.


⚠️ VS CODE can **automatically suggest the necessary Python and Jupyter extensions** when an *.ipynb* file is opened for the first time; however, for a stable and predictable setup, it is advisable to install them explicitly.

In Visual Studio Code, open **Extensions** from the left sidebar or use:

```text
Ctrl + Shift + X
```

Install the following extensions, all published by **Microsoft**.

### 1. Pylance

Provides advanced support for writing Python code:

- autocompletion;
- static analysis;
- type hints;
- code navigation.

### 2. Python

It is the main extension for integration between VS Code and Python.

Among other things, it is used to:

- identify Python interpreters;
- work with Conda environments;
- integrate Python tools into VS Code.

### 3. Python Debugger

Adds Python debugging support:

- breakpoint;
- step-by-step execution;
- variable inspection;
- call stack analysis.

### 4. Python Environments

Makes it easier to manage Python and Conda environments directly from VS Code.

In our case, the environment to use will be:

```text
myenv
```

### 5. Jupyter

Since we will work **only with `.ipynb` notebooks** during the course, this extension is essential.

It allows you to:

- open and edit Jupyter notebooks;
- execute cells;
- choose the kernel;
- view output, charts, and tables;
- manage the notebook session.


### Print a Markdown file open in VS Code

VS Code allows you to directly view the **rendered preview** of a Markdown `.md` file.

To open it:

```text
Ctrl + Shift + V
```

or:

```text
Ctrl + Shift + P
→ Markdown: Open Preview
```

No additional extension needs to be installed just to view it.

To **print** a Markdown file, however, the most practical workflow is:

```text
file .md
   ↓
Markdown Preview
   ↓
export to PDF
   ↓
print the PDF
```

If you want to do everything from VS Code, you can install a dedicated extension, for example:

```text
Markdown PDF
```

which adds export commands, for example:

```text
Markdown PDF: Export (pdf)
```

Once the PDF has been created, you can open and print it normally.

> **In summary**
>
> - to read the Markdown: `Ctrl + Shift + V`
> - to print it: first export it to PDF and then print the PDF

---

### Extensions to install

```text
Pylance
Python
Python Debugger
Python Environments
Jupyter
```

All must have the following publisher:

```text
Microsoft
```

> The **Markdown PDF** extension is optional: it is only needed if you want to conveniently export and print Markdown files directly from VS Code.

## 13. Select the kernel in VS Code (with .ipynb files)

Open the `.ipynb` notebook.

The following usually appears in the top right:

```text
Select Kernel
```

and you then need to click it.

> 👉 `Select Kernel` does not always appear: sometimes VS Code selects the kernel automatically by reading the notebook's **metadata** (the information saved in the `.ipynb` file together with the cells, including the **name of the kernel** used last time) or by remembering the previous selection. In this case, **the kernel name appears directly** in the top right.<br>
> Before starting to run the notebook cells, it is still a good idea to **check that name**: <u>if the notebook comes from another computer</u>, **the metadata refers to the environment of the person who created it**, and <u>VS Code might therefore suggest a different environment</u> from the one we want to use. To change it, simply click the name and select `myenv`.

Returning to the most common case, after clicking `Select kernel`, VS Code displays **one of the following two lists**, depending on the situation.

**Case 1 – VS Code already suggests an environment.** **The proposed kernel** appears at the top of the list, for example:

```text
myenv (Python 3.11.11)   ~\miniconda3\envs\myenv\python.exe
Select Another Kernel...
```

If the name and path match the environment we want to use, simply <u>select the first row</u>. Otherwise, choose **Select Another Kernel...**, a list appears, and we continue with case 2.

**Case 2 – VS Code has no suggestions.**<br> 
VS Code displays a window with several possible kernel sources:

```text
Python Environments...
Jupyter Kernel...
Existing Jupyter Server...
```

In our case, with **Miniconda + a local Conda environment**, the correct choice is:

```text
Python Environments...
```

This option **shows the Python environments available on the computer, including Conda environments**.

Then select the course environment, for example:

```text
Python 3.12 (myenv)
```

The general flow is therefore:

```text
What we do (in VS Code)

Select Kernel
     ↓
Python Environments...
     ↓
myenv


What VS Code does (behind the scenes)

when the first cell is run, it starts the kernel:
python.exe from the myenv environment + ipykernel
     ↓
for each cell that is run:
sends the code to the kernel  ⇄  receives output, results, and errors
     ↓
displays the results below the cell
```

---
> 📌 In any case, in either of the two cases, before running the notebook cells, it is a good idea to check the **path** shown next to the kernel name: it is the path to the environment's `python.exe` (`~` indicates the user's folder) and <u>unambiguously indicates which environment will be used</u>.

---

#### Meaning of the three options

Let's now look in more detail at the meaning of the three options in case 2.

**Python Environments...**

Allows you to choose one of the Python environments installed on the computer:
- Conda environments;
- `venv` environments;
- other local Python installations.

It is **the option to use during the course**.

👉 In VS Code, when you choose *Python Environments...*, **the kernel is built from a specific Python interpreter belonging to a Conda or virtual environment**.

---

**Jupyter Kernel...**

Allows you to choose a **Jupyter kernel already registered** on the system through a *kernelspec*.

For example, a kernel may have been registered manually with:

```cmd
python -m ipykernel install --user --name myenv
```

In our approach, this step is **not normally necessary**, because VS Code can use the Conda environment directly through:

```text
Python Environments...
```

---

**Existing Jupyter Server...**

Allows you to connect VS Code to an **existing Jupyter Server**, either local or remote.

It is useful, for example, when the notebook runs on:

- corporate servers;
- remote machines;
- GPU infrastructure;
- JupyterHub;
- lab servers.

In our local Windows scenario, it is **not necessary**.

---

In summary:

```text
For the course:

Select Kernel
      ↓
Python Environments...
      ↓
myenv
```

At that point, the notebook will use:

```text
myenv
      │
      ├── Python 3.12 interpreter
      ├── ipykernel
      └── packages installed in the environment
```

📌 All notebook cells will therefore be executed by the **kernel associated with the `myenv` environment**.

## 14. Recommended workflow during the course

Each time you start a session:

```text
1. Open Windows Terminal
          ↓
2. Select Command Prompt
          ↓
3. Activate the Conda environment
          ↓
4. Set PYTHONNOUSERSITE
          ↓
5. Go to the project folder
          ↓
6. Launch VS Code
          ↓
7. Open the notebook and select the myenv kernel
```

Commands:

```cmd
conda activate myenv
set PYTHONNOUSERSITE=1
cd C:\CorsoPython
code .
```

Diagram:

```text
Windows Terminal
      │
      ▼
Command Prompt (cmd)
      │
      │  conda activate myenv
      ▼
(myenv)
      │
      │  cd C:\CorsoPython
      ▼
Project folder
      │
      │  code .
      ▼
Visual Studio Code
      │
      ▼
Notebook .ipynb
      │
      ▼
Kernel: myenv
```

---

## 15. End the session

When you have finished working, you can deactivate the environment with:

```cmd
conda deactivate
```

The prefix:

```text
(myenv)
```

will disappear from the prompt.

---

# Common problems

## `conda` is not recognized

If a message similar to the following appears:

```text
'conda' is not recognized as an internal or external command...
```

open **Miniconda Prompt** from the Start menu and run:

```cmd
conda init cmd.exe
```

Close Windows Terminal completely and reopen it. [`conda init` changes settings that the terminal reads only at startup.]

---

## `code` is not recognized

If the following appears:

```text
'code' is not recognized as an internal or external command...
```

close and reopen Windows Terminal after installing VS Code.

If the problem remains, check the Visual Studio Code installation and that the `code` command is available in the PATH.

---

## VS Code uses the wrong Python

Press:

```text
Ctrl + Shift + P
```

then:

```text
Python: Select Interpreter
```

and choose:

```text
myenv
```

---

## VS Code's integrated terminal opens PowerShell instead of cmd

In VS Code, you can select the desired terminal profile.

Open the integrated terminal with:

```text
Ctrl + `
```

From the terminal menu, choose:

```text
Select Default Profile
```

and then:

```text
Command Prompt
```

Finally, open a new terminal.

At this point, the prompt should look similar to:

```text
C:\CorsoPython>
```

and, after activating the environment:

```text
(myenv) C:\CorsoPython>
```

---


# If you have problems with VS Code / Jupyter

If VS Code does not correctly recognize the Conda environment, the kernel does not appear, or the notebook does not run as expected, open the **Command Palette** with:

```text
Ctrl + Shift + P
```

and try the following commands in order.

### 1. `Developer: Reload Window`

Reloads the VS Code window and restarts the interface and extensions without closing the project.

This is the first thing to try when VS Code appears not to update the state of environments or extensions correctly.

---

### 2. `Python Environments: Refresh All Environment Managers`

Forces VS Code to search again for available Python environments.

It is particularly useful when:

- a new Conda environment has just been created;
- the `myenv` environment does not appear;
- VS Code displays an outdated list of environments.

---

### 3. `Python: Select Interpreter`

Allows you to explicitly select the Python interpreter from the Conda environment.

In our case, select:

```text
myenv
```

or an entry similar to:

```text
Python 3.12 (myenv)
```

---

### 4. `Notebook: Select Notebook Kernel`

Allows you to select the kernel used by the notebook again.

Select:

```text
Python Environments...
```

and then:

```text
myenv
```

---

## Recommended troubleshooting sequence

```text
Ctrl + Shift + P
        ↓
Developer: Reload Window
        ↓
Python Environments: Refresh All Environment Managers
        ↓
Python: Select Interpreter
        ↓
myenv
        ↓
Notebook: Select Notebook Kernel
        ↓
Python Environments...
        ↓
myenv
```

If the problem persists, also check that the following is installed in the environment:

```cmd
conda install ipykernel
```

and that the following Microsoft extensions are installed and enabled in VS Code:

```text
Python
Pylance
Python Debugger
Python Environments
Jupyter
```


# Command summary

```cmd
:: initialization: normally only once (persists for all subsequent cmd terminal sessions)
conda init cmd.exe

:: create the course environment
conda create -n myenv python=3.12

:: activate it
conda activate myenv

:: isolate Python from packages installed at user level
set PYTHONNOUSERSITE=1

:: check Python
python --version
where python
python -c "import sys; print(sys.executable)"

:: install the course packages
conda install -c conda-forge --override-channels numpy pandas matplotlib scikit-learn

:: install the Jupyter kernel
conda install ipykernel

:: enter the course folder
cd C:\CorsoPython

:: launch VS Code from the current folder
code .

:: when finished
conda deactivate
```

# Fundamental concept

A **Conda environment** is an isolated Python installation.

We can therefore have different environments on the same computer:

```text
base
│
├── myenv             → Python 3.12 + course libraries
├── progetto-A        → other libraries
└── progetto-B        → a different Python version
```

This reduces conflicts between Python and library versions and makes the course environment easier to reproduce and manage.

---

# Mistakes to avoid

![](Installazione-Miniconda-su-Windows.png)