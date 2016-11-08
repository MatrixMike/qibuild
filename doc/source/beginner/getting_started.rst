.. _getting-started:

Getting Started
===============


Requirements
------------

**qiBuild** is a set of command line tools written in **Python**.

Only **Python 2.7** is supported.

Note that most linux distributions now comes with **Python3**
by default now, so you may need to install **python 2** first.


Installation
------------

Linux
+++++

=====  ============================================================================
Step    Action
=====  ============================================================================
1.      Install ``qibuild`` with `pip <http://www.pip-installer.org/en/latest/>`_.

        It is recommended to install qibuild with the ``--user`` option,
        in order to keep your system clean.

        .. code-block:: console

            pip install qibuild --user

2.      Add ``$HOME/.local/bin`` to your ``$PATH``.

        One way to that is to add the following line at the end of
        your ~/.bashrc file:

        .. code-block:: console

            PATH=$PATH:$HOME/.local/bin
=====  ============================================================================

Mac
+++

=====  ============================================================================
Step    Action
=====  ============================================================================
1.      Install ``qibuild`` with `pip <http://www.pip-installer.org/en/latest/>`_.

        It is recommended to install qibuild with the ``--user`` option,
        in order to keep your system clean.

        .. code-block:: console

            pip install qibuild --user

2.      Add ``$HOME/Library/Python/2.7/bin`` to your ``$PATH``.
=====  ============================================================================

Windows
+++++++

=====  ============================================================================
Step    Action
=====  ============================================================================
1.      Install ``qibuild`` with `pip <http://www.pip-installer.org/en/latest/>`_.

        .. code-block:: console

            pip install qibuild

2.      To use scripts written in Python:

        Add ``C:\Python2x`` and
        ``c:\Python2x\Scripts`` in your ``PATH``.


3.      If you'd like to have nice colors in your console, you can install
        the Python readline library: http://pypi.python.org/pypi/pyreadline.
=====  ============================================================================


Continue with the tutorials
----------------------------


.. toctree::
    :maxdepth: 1

    qisrc/tutorial
    qisrc/templates
    qibuild/tutorial
    qidoc/tutorial
    qilinguist/tutorial
