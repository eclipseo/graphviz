import pathlib
import os
import typing

from .common import ENGINES, FORMATS, RENDERERS, FORMATTERS, RequiredArgumentError
from . import execute

#: :class:`pathlib.Path` of layout command (``Path('dot')``).
DOT_BINARY = pathlib.Path('dot')


def command(engine: str, format_: str,
            *, renderer: typing.Optional[str] = None,
            formatter: typing.Optional[str] = None
            ) -> typing.List[typing.Union[os.PathLike, str]]:
    """Return ``subprocess.Popen`` args list for rendering."""
    if formatter is not None and renderer is None:
        raise RequiredArgumentError('formatter given without renderer')

    if engine not in ENGINES:
        raise ValueError(f'unknown engine: {engine!r}')
    if format_ not in FORMATS:
        raise ValueError(f'unknown format: {format_!r}')
    if renderer is not None and renderer not in RENDERERS:
        raise ValueError(f'unknown renderer: {renderer!r}')
    if formatter is not None and formatter not in FORMATTERS:
        raise ValueError(f'unknown formatter: {formatter!r}')

    output_format = [f for f in (format_, renderer, formatter) if f is not None]
    output_format_flag = ':'.join(output_format)
    return [DOT_BINARY, f'-K{engine}', f'-T{output_format_flag}']


def render(engine: str, format: str,
           filepath: typing.Union[os.PathLike, str],
           renderer: typing.Optional[str] = None,
           formatter: typing.Optional[str] = None,
           quiet: bool = False) -> str:
    """Render file with Graphviz ``engine`` into ``format``,
        return result filename.

    Args:
        engine: Layout engine for rendering (``'dot'``, ``'neato'``, ...).
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).
        filepath: Path to the DOT source file to render.
        renderer: Output renderer (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter (``'cairo'``, ``'gd'``, ...).
        quiet: Suppress ``stderr`` output from the layout subprocess.

    Returns:
        The (possibly relative) path of the rendered file.

    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
            are not known.
        graphviz.RequiredArgumentError: If ``formatter`` is given
            but ``renderer`` is None.
        graphviz.ExecutableNotFound: If the Graphviz 'dot' executable
            is not found.
        subprocess.CalledProcessError: If the returncode (exit status)
            of the rendering 'dot' subprocess is non-zero.

    Note:
        The layout command is started from the directory of ``filepath``,
        so that references to external files
        (e.g. ``[image=images/camelot.png]``)
        can be given as paths relative to the DOT source file.
    """
    dirname, filename = os.path.split(filepath)
    del filepath

    cmd = command(engine, format, renderer=renderer, formatter=formatter)
    cmd.extend(['-O', filename])

    suffix = '.'.join(f for f in (formatter, renderer, format) if f is not None)
    rendered = f'{filename}.{suffix}'

    if dirname:
        cwd = dirname
        rendered = os.path.join(dirname, rendered)
    else:
        cwd = None

    execute.run_check(cmd, capture_output=True, cwd=cwd, quiet=quiet)
    return rendered


def pipe(engine: str, format: str, data: bytes,
         renderer: typing.Optional[str] = None,
         formatter: typing.Optional[str] = None,
         quiet: bool = False) -> bytes:
    """Return ``data`` (``bytes``) piped through Graphviz ``engine``
        into ``format`` as ``bytes``.

    Args:
        engine: Layout engine for rendering (``'dot'``, ``'neato'``, ...).
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).
        data: Binary (encoded) DOT source bytes to render.
        renderer: Output renderer (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter (``'cairo'``, ``'gd'``, ...).
        quiet: Suppress ``stderr`` output from the layout subprocess.

    Returns:
        Binary (encoded) stdout of the layout command.

    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
            are not known.
        graphviz.RequiredArgumentError: If ``formatter`` is given
            but ``renderer`` is None.
        graphviz.ExecutableNotFound: If the Graphviz 'dot' executable
            is not found.
        subprocess.CalledProcessError: If the returncode (exit status)
            of the rendering 'dot' subprocess is non-zero.

    Example:
        >>> import graphviz
        >>> graphviz.pipe('dot', 'svg', b'graph { hello -- world }')[:14]
        b'<?xml version='

    Note:
        The layout command is started from the current directory.
    """
    cmd = command(engine, format, renderer=renderer, formatter=formatter)
    kwargs = {'input': data}

    proc = execute.run_check(cmd, capture_output=True, quiet=quiet, **kwargs)
    return proc.stdout


def pipe_string(engine: str, format: str, input_string: str,
               *, encoding: str,
                renderer: typing.Optional[str] = None,
                formatter: typing.Optional[str] = None,
                quiet: bool = False) -> str:
    """Return ``input_string`` piped through Graphviz ``engine``
        into ``format`` as ``str``.

    Args:
        engine: Layout engine for rendering (``'dot'``, ``'neato'``, ...).
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).
        input_string: Binary (encoded) DOT source bytes to render.
        encoding: Encoding to en/decode subprocess stdin and stdout (required).
        renderer: Output renderer (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter (``'cairo'``, ``'gd'``, ...).
        quiet: Suppress ``stderr`` output from the layout subprocess.

    Returns:
        Decoded stdout of the layout command.

    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
            are not known.
        graphviz.RequiredArgumentError: If ``formatter`` is given
            but ``renderer`` is None.
        graphviz.ExecutableNotFound: If the Graphviz 'dot' executable
            is not found.
        subprocess.CalledProcessError: If the returncode (exit status)
            of the rendering 'dot' subprocess is non-zero.

    Example:
        >>> import graphviz
        >>> graphviz.pipe_string('dot', 'svg', 'graph { spam }',
        ...                      encoding='ascii')[:14]
        '<?xml version='

    Note:
        The layout command is started from the current directory.
    """
    cmd = command(engine, format, renderer=renderer, formatter=formatter)
    kwargs = {'input': input_string, 'encoding': encoding}

    proc = execute.run_check(cmd, capture_output=True, quiet=quiet, **kwargs)
    return proc.stdout


def pipe_lines(engine: str, format: str, input_lines: typing.Iterator[str],
               *, input_encoding: str,
               renderer: typing.Optional[str] = None,
               formatter: typing.Optional[str] = None,
               quiet: bool = False) -> bytes:
    r"""Return ``input_lines`` piped through Graphviz ``engine``
        into ``format`` as ``bytes``.

    Args:
        engine: Layout engine for rendering (``'dot'``, ``'neato'``, ...).
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).
        input_lines: DOT source lines to render (including final newline).
        input_encoding: Encode input_lines for subprocess stdin (required).
        renderer: Output renderer (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter (``'cairo'``, ``'gd'``, ...).
        quiet: Suppress ``stderr`` output from the layout subprocess.

    Returns:
        Binary stdout of the layout command.

    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
            are not known.
        graphviz.RequiredArgumentError: If ``formatter`` is given
            but ``renderer`` is None.
        graphviz.ExecutableNotFound: If the Graphviz 'dot' executable
            is not found.
        subprocess.CalledProcessError: If the returncode (exit status)
            of the rendering 'dot' subprocess is non-zero.

    Example:
        >>> import graphviz
        >>> graphviz.pipe_lines('dot', 'svg', iter(['graph { spam }\n']),
        ...                     input_encoding='ascii')[:14]
        b'<?xml version='

    Note:
        The layout command is started from the current directory.
    """
    cmd = command(engine, format, renderer=renderer, formatter=formatter)
    kwargs = {'input_lines': (line.encode(input_encoding) for line in input_lines)}

    proc = execute.run_check(cmd, capture_output=True, quiet=quiet, **kwargs)
    return proc.stdout


def pipe_lines_string(engine: str, format: str, input_lines: typing.Iterator[str],
                      *, encoding: str,
                      renderer: typing.Optional[str] = None,
                      formatter: typing.Optional[str] = None,
                      quiet: bool = False) -> str:
    r"""Return ``input_lines`` piped through Graphviz ``engine``
        into ``format`` as ``str``.

    Args:
        engine: Layout engine for rendering (``'dot'``, ``'neato'``, ...).
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).
        input_lines: DOT source lines to render (including final newline).
        encoding: Encoding to en/decode subprocess stdin and stdout (required).
        renderer: Output renderer (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter (``'cairo'``, ``'gd'``, ...).
        quiet: Suppress ``stderr`` output from the layout subprocess.

    Returns:
        Decoded stdout of the layout command.

    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
            are not known.
        graphviz.RequiredArgumentError: If ``formatter`` is given
            but ``renderer`` is None.
        graphviz.ExecutableNotFound: If the Graphviz 'dot' executable
            is not found.
        subprocess.CalledProcessError: If the returncode (exit status)
            of the rendering 'dot' subprocess is non-zero.

    Example:
        >>> import graphviz
        >>> graphviz.pipe_lines_string('dot', 'svg', iter(['graph { spam }\n']),
        ...                            encoding='ascii')[:14]
        '<?xml version='

    Note:
        The layout command is started from the current directory.
    """
    cmd = command(engine, format, renderer=renderer, formatter=formatter)
    kwargs = {'input_lines': input_lines, 'encoding': encoding}

    proc = execute.run_check(cmd, capture_output=True, quiet=quiet, **kwargs)
    return proc.stdout
