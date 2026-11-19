Python API reference
====================

Policies
--------

.. automodule:: news.policies
   :members:

Approval and delivery
---------------------

.. automodule:: news.services
   :members:

Domain models
-------------

.. automodule:: news.models

.. autoclass:: news.models.User
   :members: reader_subscriptions, independent_articles, independent_newsletters

.. autoclass:: news.models.Publisher

.. autoclass:: news.models.Article
   :members: clean

.. autoclass:: news.models.Newsletter

.. autoclass:: news.models.PublicationDelivery

.. autoclass:: news.models.ApprovalLog
