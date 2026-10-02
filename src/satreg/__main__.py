from .cli import main

# Guarded: the worker processes of a training import this module again.
if __name__ == "__main__":
    main()
