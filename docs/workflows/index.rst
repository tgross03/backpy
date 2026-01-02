.. _workflows:

*********
Workflows
*********

The following categories contain guides about different typical workflows while using the ``backpy`` CLI.
These guides' primary motivation is helping you to get used to the basic concept and optimal usage of the package.

.. note::
    Since the package is built for reproducibility, the guides will primarily talk about using the commands of the CLI
    **without** using the ``--interactive`` flag.
    Read more in the section about the :ref:`interactive-mode`.


.. grid:: 2
    :class-row: surface

    .. grid-item-card:: :octicon:`gear` Setup
        :link: workflows-setup
        :link-type: ref

        Setting up the package, remotes, backup spaces and more.

    .. grid-item-card:: :octicon:`globe` Common
        :link: workflows-common
        :link-type: ref

        Day-to-day operations like creating, restoring and locking of backups.

.. grid:: 2
    :class-row: surface

    .. grid-item-card:: :octicon:`cpu` Automation
        :link: workflows-automation
        :link-type: ref

        Automating the creation of backups to create an autonomous backup cycle.

    .. grid-item-card:: :octicon:`tools` Maintenance
        :link: workflows-maintenance
        :link-type: ref

        Checking for problems, cleaning up or migrating the backups.

.. toctree::
    :includehidden:
    :hidden:

    automation/index
    common/index
    maintenance/index
    setup/index