===============
plone.app.async
===============

Introduction
============

This package provides `zc.async`_  integration to plone for performing asynchronous job operations.

Installation
============
You will be typically running plone.app.async in a ZEO environment where you will be having one or more *worker* instances that will be acting as dispatchers polling and carrying out jobs queued by your main zope instances.
For the sake of simplicity it is assumed that you have one instance that can queue new jobs, and one worker instance that consumes them both operating on a single database. In this case, your buildout configuration will look similar to::

  [zeo]
  ...
  recipe = plone.recipe.zope2zeoserver
  file-storage = ${buildout:directory}/var/filestorage/Data.fs

  [instance]
  ...
  recipe = plone.recipe.zope2instance
  eggs = Plone
      plone.app.async
  environment-vars =
      ZC_ASYNC_UUID ${buildout:directory}/var/instance-uuid.txt
  zope-conf-additional =
      <product-config zc.z3monitor>
          port 8081
      </product-config>

  [worker]
  ...
  recipe = plone.recipe.zope2instance
  zserver-threads = 2
  eggs = ${instance:eggs}
  zcml = ${instance:zcml}
  environment-vars =
      ZC_ASYNC_UUID ${buildout:directory}/var/worker-uuid.txt
  zcml-additional =
      <include package="plone.app.async" file="single_db.zcml" />

There are two important stanzas above:

* Each instance has to have the `ZC_ASYNC_UUID` environmental variable to integrate properly with `zc.async`.
* The worker instance loads the `single_db.zcml` zcml configuration in order to setup the queue and setup itself as a dispatcher. Also, if the optional `zc.z3monitor` product configuration is present in the buildout it will be started.

For more details please look at the buildout configuration included in the package.

Credits
=======
Enfold's `plone.core.async`_ package has been extensively used for setting up the queues and Zope Control Panel integration.

References
==========
* `zc.async`_ at pypi
* `plone.core.async`_ svn repository

  .. _zc.async: http://pypi.python.org/pypi/zc.async/
  .. _plone.core.async: https://svn.enfoldsystems.com/public/plone.async.core/

