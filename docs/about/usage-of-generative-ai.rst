.. _use-of-gen-ai:

**********************
Usage of Generative AI
**********************

Statement and Principles
------------------------

The usage of generative artificial intelligence ("GenAI") in programming has the potential to optimize the workflows
of developers, assist in debugging and testing programs and generating repetitive code. However there are inherent risks
in using GenAI without proper human supervision.
Most importantly, the ethical justifiability of using GenAI in coding is highly dependent on the transparency and responsible
behavior of the developers. [1]_

In this project, the following principles were applied regarding the usage of GenAI for coding:

.. card::
    :class-card: principle

    **1st Principle**
    ^^^
    If GenAI is used for generating **substantial amounts of code** (e.g. multiple lines, entire functions, classes
    or files) a transparency notice has to be provided stating that

        * GenAI was used to generate the code,
        * specifying which parts of the code were generated
        * using which model and
        * whether the code was modified by human developers.

    In any case the usage must be permitted by the *Terms of Use* (or comparable legal usage requirements)
    of the used model and may not violate any current laws. If the *Terms of Use* require additional steps to
    allow the usage of the code, these must be met or the code may not be used.

.. card::
    :class-card: principle

    **2nd Principle**
    ^^^

    Since GenAI is subject to complications like biases, hallucinations and is highly dependent on the given input,
    generated contents should never be used without checking the content manually. Publishing generated code without
    review poses potential risks for the stability of the program and the devices used to run it.

.. card::
    :class-card: principle

    **3rd Principle**
    ^^^

    There are certain situations in which using GenAI can be advantageous and there are situations in which
    it should not be used.
    In general, using GenAI should not be first solution when encountering problems.
    It is a tool to help the developers but should not replace critical and analytic thinking and problem
    solving.

    This project generally tries to apply the following rule of thumb for some of the most important examples:

    .. table:: Sensible vs Not Sensible - Using GenAI in Programming

        ====================================================== ==========================================
        Sensible                                               Not Sensible
        ====================================================== ==========================================
        Generating boilerplate / repetitive code               Generating large algorithms
        Additional debugging checks of code                    Generating entire parts of the codebase
        Test development (primarily for checking edge cases)   Creating safety critical parts of the code
        Documenting code                                       Documenting code
        ====================================================== ==========================================


    .. note::

        The aspect of *Documenting code* appears in both columns of the table above since this is a debatable application
        of GenAI and **should be decided from case to case**.

        On one hand documenting similar functions and wrappers is repetitive and time consuming, so it could make
        sense to save time by generating this (especially using in-line completion tools). On the other hand, the person writing
        the code should be the one to document it since he/she knows the functionality of the code best and therefore
        should be able explain it.

Example: Transparency Notice
----------------------------

.. code:: txt

    Transparency notice
    -------------------

    A substantial amount of this extension's code generated
    by the generative AI <MODEL_NAME> and modified by the
    developer.

    <ADDITIONAL NOTICES REQUIRED BY THE MODELS TERMS OF USE>

References and Further Reading
------------------------------

.. [1] Atemkeng, M., Hamlomo, S., Welman, B., Oyetunji, N., Ataei, P., and E Fendji, J. L. K., “Ethics of Software Programming with Generative AI: Is Programming without Generative AI always radical?”, 2024. doi:`10.48550/arXiv.2408.10554 <https://doi.org/10.48550/arXiv.2408.10554>`_.
