# -*- coding: utf-8 -*-
from globaleaks import models
from globaleaks.models import config
from globaleaks.orm import transact
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestModels(helpers.TestGL):
    initialize_test_database_using_archived_db = False

    @inlineCallbacks
    def test_initialize_tenant_config(self):
        @transact
        def transaction(session):
            session.query(models.Config).filter(models.Config.tid == 1).delete()
            config.initialize_tenant_config(session, 1, u'default')

        yield transaction()

    @inlineCallbacks
    def test_fix_tenant_config(self):
        @transact
        def transaction(session):
            # Rename 'name' variable with the effect of:
            # - simuulating missing variable
            # - simulating the presence of a variable not anymore defined
            session.query(models.Config).filter(models.Config.tid == 1, models.Config.var_name=='name').one().var_name='removed'

            # Delete a variable that requires initialization via a constructor
            session.query(models.Config).filter(models.Config.tid == 1, models.Config.var_name=='receipt_salt').delete()

            config.fix_tenant_config(session, 1)

        yield transaction()
