.. _cli-reference:

*************
CLI Reference
*************


The ``backpy`` CLI uses one general command:

.. code-block::

    backpy [OPTIONS] COMMAND [ARGS] ...

Options
-------

--version, -v   Displays the current version of backpy.

--info   Displays some information about backpy.

Subcommands
-----------

.. grid:: 2
    :class-row: surface

    .. grid-item-card:: :octicon:`file-zip` ``backup``
        :link: cli-backup
        :link-type: ref

        Actions related to creating and managing backups.

    .. grid-item-card:: :octicon:`sliders` ``config``
        :link: cli-config
        :link-type: ref

        Actions related to configuring the package.

.. grid:: 2
    :class-row: surface

    .. grid-item-card:: :octicon:`server` ``remote``
        :link: cli-remote
        :link-type: ref

        Actions related to remote locations to save backups at.

    .. grid-item-card:: :octicon:`clock` ``schedule``
        :link: cli-schedule
        :link-type: ref

        Actions related to scheduling for automatic backups.

.. grid:: 1
    :class-row: surface

    .. grid-item-card:: :octicon:`archive` ``space``
        :link: cli-space
        :link-type: ref

        Actions related to creating and managing backup spaces.

.. toctree::
    :hidden:

    backup
    config
    remote
    schedule
    space