----------------------------------
Tutorial: How to use ``towncrier``
----------------------------------

We use the python package ``towncrier`` to manage our changelogs.
It can be used to create changelog files (e.g. for pull requests).
When building the docs, these files are collected and merged into
a ``changelog.rst`` file containing the entire changelog of the project.

Therefore it is mandatory to create changelogs when creating pull requests.
There are two main ways to create a ``towncrier`` changelog.

Variant 1: Using the ``towncrier`` CLI
--------------------------------------

The guided way to generate changelogs, is the CLI of ``towncrier``.
To be able to use it, you have to install the ``backpy`` package for development.
Make sure you also install the optional dependencies ``docs``.

After just navigate to your local backpy git repository.
There you can enter the following command

.. code-block:: bash

  towncrier create

You will be prompted to enter the ``issue number``.
Enter the number of the **pull request** your changes are included in.

.. code-block::

  > Issue number (`+` if none): █

Then you have to enter the type of the changes:
Choose the appropriate label for your changes. If you have changes with different types, **create a changelog for every change**.

.. code-block::

  > Fragment type (api, cli, docs, bugfix): █

Now a text editor should open where you can specify your changes.
Keep the description short and concise. You can use sphinx's ``rst`` syntax.

 **Tip:** Refer to this cheat sheet to look up possible ``rst`` commands: https://sphinx-tutorial.readthedocs.io/cheatsheet/

Finally, save your document and commit it to the branch you created the pull request for.

Variant 2: Manually Creating Files
----------------------------------

The shortest way to create your changelog files is creating them yourself.
Therefore navigate to your local ``backpy`` repository.
Inside the repository navigate to ``docs/changes``.

.. code-block::

  cd docs/changes

Create a file with the following naming scheme:

.. code-block::

  <ID of your pull-request>.<type of changes>.rst

The possible types are:

============ =======================
``api``      API Changes
``cli``      CLI Changes
``docs``     Documentation Changes
``bugfix``   Bug Fixes
============ =======================

Open the created file with a editor of your choice and document your changes.
Keep the description short and concise. You can use sphinx's ``rst`` syntax.

 **Tip:** Refer to this cheat sheet to look up possible ``rst`` commands: https://sphinx-tutorial.readthedocs.io/cheatsheet/

Finally, save your document and commit it to the branch you created the pull request for.


