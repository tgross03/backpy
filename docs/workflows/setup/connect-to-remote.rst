.. _workflows-connect-to-remote:

Connecting to a Remote
----------------------

Connecting to a remote is relatively simple.
You will need to know the following things before doing so:

``name``
    The name you want to give the remote. This can be an arbitrary one-word name but it has to be exclusive for this remote.
``hostname``
    The hostname or IP of your remote storage (e.g. ``172.217.23.110`` or ``mystoragebox.mydomain.com``)
``username``
    The username of the account that can access the storage server.
``protocol``
    The protocol via which the files should be transferred. Possible values are given in the CLI-reference under :ref:`remote <cli-remote>`.

    .. important::
        The remote server has to support the given protocol and all necessary ports (e.g. ``22`` for default SFTP transfers) have to be opened!

        Also note that not every protocol supports every authentication method.

Authentication method
    You have to know via which authentication method you want to log in. In general you can choose between **SSH-Key** or **password** based authentication.
    We encourage you to use a public/private key combination to ensure maximum security for your remote storage.

    If you want to use

    1. **Password**: You do not have to provide extra keywords. You will be asked for the password during the creation process.
    2. **SSH-Key**: You will have to know the location of your **private** keyfile. This requires the previous creation of such a key and the deployment of the public
       key on the remote server. For further information on this refer to this page: https://wiki.archlinux.org/title/SSH_keys

``key``
    This is the location of the keyfile as described above.

.. note::

    There are more options you can change depending on your system. Check the reference for :ref:`cli-remote` for further information.

The next steps depend on your choice of authentication. Choose the right guide for you.

.. tab-set::

    .. tab-item:: :octicon:`key` With SSH-Key

        .. code-block:: bash

            backpy remote create --name <name> --hostname <hostname> --username <username> --protocol <protocol> --key <path-to-private-key>

        After sending the command, you will be asked to enter the passphrase for the SSH key.
        Since an SSH key does not require a passphrase this can be empty.

        .. code-block::

            > Enter the passphrase for the SSH key (may be empty): █

        This passphrase will only be saved in your local config for this remote.
        The passphrase is not saved in clear text but as an encrypted token.
        Read more about the encryption of ``backpy`` in the concept :ref:`concepts_encryption`.

        After entering the correct passphrase, you should see lines like these:

        .. code-block::

            Created remote test (Hostname: <hostname>, User: <user>).
            Using Protocol sftp.
            ⠼ Testing connection to <hostname> with user <user> using public key authentication.
            Connection test to <hostname> with user testuser was successful.

    .. tab-item:: :octicon:`passkey-fill` With Password

        .. code-block:: bash

            backpy remote create --name <name> --hostname <hostname> --username <username> --protocol <protocol>

        After sending the command, you will be asked to enter your password.

        .. code-block::

            > Enter the password for the user: █

        This password will only be saved in your local config for this remote.
        The password is not saved in clear text but as an encrypted token.
        Read more about the encryption of ``backpy`` in the concept :ref:`concepts_encryption`.

        If you entered the wrong password or passphrase you will receive an error message and the remote will not be created.

        After entering the correct passphrase, you should see lines like these:

        .. code-block::

            Created remote test (Hostname: <hostname>, User: <user>).
            Using Protocol sftp.
            ⠼ Testing connection to <hostname> with user <user> using password authentication.
            Connection test to <hostname> with user testuser was successful.

If everything worked, you should have a working remote storage now.
You can use :code:`backpy remote edit <name>` to edit the remote, :code:`backpy remote test <name>` to test the connection and
:code:`backpy remote delete <name>` to delete the remote.
