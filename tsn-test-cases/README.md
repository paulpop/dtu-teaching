# Installing the dependancies (Windows Guide)

## First install these two dependancies using pip:
```
python3 -m pip install networkx matplotlib
```

## Then install graphviz using this link:
https://gitlab.com/graphviz/graphviz/-/package_files/6164164/download

Note here that any other link won't work

## Install Microsoft Build Tools from this link
https://visualstudio.microsoft.com/visual-cpp-build-tools/

## Then you can install the pygraphviz using the following commmand:
    
```
python3 -m pip install --config-settings="--global-option=build_ext" `
              --config-settings="--global-option=-IC:\Program Files\Graphviz\include" `
              --config-settings="--global-option=-LC:\Program Files\Graphviz\lib" `
              pygraphviz
```

## To run the code afterwards use:
```
python3 generatetsndata.py
```

# Installing the dependancies (macOS Guide)

## First install graphviz using brew
```
brew install graphviz
```

## Then install these dependancies using pip:
```
python3 -m pip install networkx matplotlib pygraphviz
```

## To run the code afterwards use:
```
python3 generatetsndata.py
```

# Installing the dependancies (Linux/Ubuntu Guide)

## First install two packages using apt
```
sudo apt-get install graphviz graphviz-dev
```

## Then install these dependancies using pip:
```
python3 -m pip install networkx matplotlib pygraphviz
```

## To run the code afterwards use:
```
python3 generatetsndata.py
```