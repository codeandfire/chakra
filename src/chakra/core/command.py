import os
import shlex
import subprocess

def _subprocess_run(args, capture_output=True, env=None):
    try:
        result = subprocess.run(
            args, shell=False, check=False, text=True, capture_output=capture_output,
            env=env)
    except FileNotFoundError as exc:         # normalize this error
        err = f'command not found: {exc.filename}'
        if not capture_output:
            print(err, file=sys.stderr)
            stdout, stderr = None, None
        else:
            stdout, stderr = '', err
        result = subprocess.CompletedProcess(
            args=args, returncode=127, stdout=stdout, stderr=stderr)
    else:
        if capture_output:
            result.stdout, result.stderr = result.stdout.strip(), result.stderr.strip()

    return result

class Command(object):

    def __init__(self, tokens, env_vars={}):
        self.tokens = tokens
        self.env_vars = env_vars

    def __repr__(self):
        return f'{self.__class__.__name__}(tokens={self.tokens!r}, env_vars={self.env_vars!r})'

    def __str__(self):
        return shlex.join(self.tokens)

    def __eq__(self, other):
        return self.tokens == other.tokens and self.env_vars == other.env_vars

    def run(self, capture_output=True):
        env_vars = self.env_vars.copy()
        env_vars['PATH'] = os.environ['PATH']    # pass the current PATH
        return _subprocess_run(self.tokens, capture_output=capture_output, env=env_vars)
